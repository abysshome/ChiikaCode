import os
from typing import Iterator, List

from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough

from share import getLongestCodeBlock, lang_exts, llm, supported_langs
from rag_api import get_embedding,get_vector_db,build_retriever,build_rag_chain,handle_folder

def getRawStructureStream(requirement: str, languange: str = 'python') -> Iterator[str]:
    """ 输入需求, 返回大语言模型生成的项目结构数据流 """

    embedding=get_embedding()
    db=get_vector_db(embedding)
    retriever=build_retriever(db)
    languange = languange.lower()
    if languange not in supported_langs:
        raise ValueError(f"Unsupported language: {languange}. (Support: {supported_langs})")

    template = '项目需求：{requirement}\n'\
        f'你将为该项目生成基本的 {languange} 代码框架。\n'\
        '可以参考{retriever}来获取相关代码片段。\n'\
        '请给出项目的文件目录结构，应尽可能包含所有的模块可能用到的文件。\n'\
        '路径中不要包含中文，请使用英文。\n'\
        '只需用4个空格的缩进表示文件的层级关系，请不要包含其它符号。\n'\
        '只要给出文件名即可，不需要具体描述内容，如非要描述，请用 // 注释。\n'\
        '请以：\n'\
        f'```{languange}\n'\
        'project/\n'\
        '    src/\n'\
        '为文件结构开头\n'\
        '回答：'
    prompt = ChatPromptTemplate.from_template(template)
    llm_chain = (
        {"retriever":retriever,"requirement": RunnablePassthrough()} |
        prompt |
        llm |
        StrOutputParser()
    )
    return llm_chain.stream(requirement)


class Node:
    """ 文件系统节点, type 为 'folder' 或 'code' 或 'file' """
    def __init__(self, name: str, type: str, parent: 'Node' = None):
        self.name = name
        self.type = type
        self.parent = parent
        self.children: List[Node] = []

        # 该变量由 Node.addChild() 自动维护
        self.depth = 0
        # 只有 type = 'code' 的节点才有 content 属性
        self.content = ''

    def __repr__(self):
        return f"<Node: {self.getPath()} ({self.type})>"

    def getPath(self) -> str:
        """ 获取节点的路径 """
        if self.parent is None:
            return self.name
        else:
            return os.path.join(self.parent.getPath(), self.name)
        
    def getJsonDict(self) -> dict:
        """ 获取节点的 JSON 字典表示 """
        if self.type == 'folder':
            return {
                'name': self.name,
                'type': self.type,
                'children': [child.getJsonDict() for child in self.children]
            }
        elif self.type == 'code':
            return {
                'name': self.name,
                'type': self.type,
                'content': self.content
            }
        else:
            return {
                'name': self.name,
                'type': self.type
            }
        
    def getStrucureString(self, indent: int = 4) -> str:
        """ 获取节点的结构字符串表示 """
        if self.type == 'folder':
            return f"{' '* indent * self.depth}{self.name}\n" + \
                ''.join(child.getStrucureString(indent) for child in self.children)
        else:
            return f"{' '* indent * self.depth}{self.name}\n"

    def getFileNodes(self, exts: List[str] = None) -> List['Node']:
        """ 获取节点下所有文件节点 """
        if self.type == 'folder':
            files = []
            for child in self.children:
                files += child.getFileNodes(exts)
            return files
        else:
            if exts is None:
                return [self]
            elif os.path.splitext(self.name)[1] in exts:
                return [self]
            else:
                return []

    def addChild(self, child: 'Node'):
        child.depth = self.depth + 1
        self.children.append(child)

def parseStructureString(structure_str: str, languange: str = 'python') -> Node:
    """ 解析项目结构数据流, 返回根节点 """

    code_block = getLongestCodeBlock(structure_str)
    exts = lang_exts[languange.lower()]
    indent = 4
    current_indent = 0
    stack: List[Node] = [Node(name='project', type='folder')]
    for line in code_block.split('\n'):
        if line.startswith('--') and line.endswith('--'):
            continue

        # 格式化
        _line = line.strip()
        if _line.startswith('//'):
            continue
        if '//' in _line:
            _line = _line.split('//')[0].strip()

        if _line.startswith('#'):
            continue
        if '#' in _line:
            _line = _line.split('#')[0].strip()

        while _line.startswith('-'):
            _line = _line[1:].strip()

        if _line == '':
            continue

        # 开头的空格数
        indent_count = len(line) - len(line.lstrip())
        current_indent = (indent_count + indent - 1) // indent

        # 用栈维护文件系统结构
        while current_indent < len(stack) and len(stack) > 1:
            stack.pop()
        if current_indent == len(stack):
            # 判断文件类型
            if os.path.splitext(_line)[1] in exts:
                _type = 'code'
            elif os.path.splitext(_line)[1] != '':
                _type = 'file'
            else:
                _type = 'folder'

            # 创建节点
            _node = Node(_line, _type, stack[-1])
            stack[-1].addChild(_node)
            stack.append(_node)
            if _type != 'folder':
                stack.pop()
    return stack[0]

def makeFolder(path: str) -> None:
    ''' Check if this folder exists, ohterwize build recursively. '''
    head, tail = os.path.split(path)
    if head and not os.path.exists(head):
        makeFolder(head)
    if not os.path.exists(path):
        os.mkdir(path)

def __loadNodeFromJsonDict(node_dict: dict, parent: Node = None) -> Node:
    ret = Node(node_dict['name'], node_dict['type'], parent)
    if ret.type == 'folder':
        for ch_dict in node_dict['children']:
            ret.children.append(__loadNodeFromJsonDict(ch_dict, ret))
    elif ret.type == 'code':
        ret.content = node_dict['content']
    elif ret.type == 'file':
        pass
    else:
        raise ValueError(f'Wrong type: {ret.type}')
    return ret

def __writeNodeIntoFolder(root: str, node: Node):
    path = os.path.join(root, node.getPath())
    if node.type == 'folder':
        makeFolder(path)
        for ch in node.children:
            __writeNodeIntoFolder(root, ch)
    elif node.type == 'code':
        with open(path, 'w', encoding='utf-8') as f:
            f.write(node.content)
    elif node.type == 'file':
        with open(path, 'w', encoding='utf-8') as f:
            pass
    else:
        raise ValueError(f'Wrong type: {node.type}')

def writeNodeJsonDictIntoFolder(root: str, node_dict: dict):
    node = __loadNodeFromJsonDict(node_dict)
    __writeNodeIntoFolder(root, node)

if __name__ == '__main__':
    # with open('result.txt', 'r', encoding='utf-8') as f:
    #     structure_str = f.read()
    # root = parseStructureString(structure_str, 'java')
    # import json
    # print(json.dumps(root.getJsonDict(), indent=4))
    # print(root.getStrucureString())

    import json
    with open('result.json') as f:
        d = json.load(f)
    writeNodeJsonDictIntoFolder('project', d)
    