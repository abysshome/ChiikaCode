from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model='llama3.2:latest')

supported_langs = [
    'c', 'cpp', 'csharp', 'go', 'java', 'javascript', 'python', 'typescript'
]
supported_model=[
    '项目级代码生成','文档阅读','ai对话'
]
lang_exts = {
    'c': ['.c', '.h'],
    'cpp': ['.cpp', '.h', '.hpp'],
    'csharp': ['.cs'],
    'go': ['.go'],
    'java': ['.java'],
    'javascript': ['.js'],
    'python': ['.py', '.pyi', '.ipynb'],
    'typescript': ['.ts']
}

def getLongestCodeBlock(raw_text: str) -> str:
    """ 返回文本中的代码块, 如果有多个, 则返回最长的那个, 否则返回空字符串 """

    # 如果没有代码块, 则直接返回空字符串
    if not '```' in raw_text:
        return ''

    lines = raw_text.split('\n')

    code_sep_count = 0
    start_incidies = []
    end_incidies = []
    for i, line in enumerate(lines):
        if '```' in line:
            code_sep_count += 1
            if code_sep_count % 2 == 1:
                start_incidies.append(i)
            else:
                end_incidies.append(i)
    # 如果代码块的标志数量不是偶数, 则说明格式不对
    if code_sep_count % 2 != 0:
        return ''

    # 找到代码块的起始和结束位置
    code_block_len = [
        (i, pair[1] - pair[0] - 1)
        for i, pair in enumerate(zip(start_incidies, end_incidies))
    ]
    # 找到最长的代码块
    code_block_len.sort(key=lambda x: x[1], reverse=True)
    block_idx = code_block_len[0][0]
    start_idx = start_incidies[block_idx]
    end_idx = end_incidies[block_idx]
    code_block = '\n'.join(lines[start_idx+1:end_idx])
    return code_block


def __test_codeBlock():
    raw_text = """
    abc
    ```python
    def main():
        print('hello world')
    ```
    hello world
    ```c
    #include <stdio.h>

    int main() {
        printf("hello world");
        return 0;
    }
    ```
    end of text
    """
    print(getLongestCodeBlock(raw_text))

    raw_text2 = """
    abc
    ```python
    def main():
        print('hello world')
    """
    print(getLongestCodeBlock(raw_text2))

if __name__ == '__main__':
    __test_codeBlock()