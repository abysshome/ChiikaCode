from gencode import getRawCodeStream
from share import getLongestCodeBlock, lang_exts, supported_langs
from structure import Node, getRawStructureStream, parseStructureString
import json

def directGetJsonString(requirement: str, lang: str = "python") -> str:
    """ 输入需求，返回结果 """
    stream = getRawStructureStream(requirement, lang) # 结构字符流
    stream_str = ''.join(list(stream))  # 结构字符串
    print(stream_str)
    structure_node = parseStructureString(stream_str, lang) # 解析为文件树

    # 遍历文件，填充代码
    for f_node in structure_node.getFileNodes(lang_exts[lang]):
        content_stream = getRawCodeStream(
            requirement,
            structure_node.getStrucureString(),
            f_node.getPath(),
            lang
        )
        f_node.content = getLongestCodeBlock(''.join(list(content_stream)))
        print(f_node.getPath(), f_node.content)

    # 返回包含文件结构的字典，转化为 JSON 字符串
    return json.dumps(structure_node.getJsonDict(), indent=4)

if __name__ == '__main__':
    s = directGetJsonString("贪吃蛇", "python")
    with open("result.json", "w", encoding="utf-8") as f:
        f.write(s)