from typing import List

import requests

# 获取可运行代码，采用如下策略：
# 1. 尝试生成代码，直到生成的代码没有语法错误
# 2. 尝试生成10次测试代码，如果任意一次通过测试，则认为代码可运行
# 3. 否则回到1
# functionName: 函数名
# arguements: 函数参数列表
# docString: 函数文档字符串


# 测试用例
def test_generate_code():
    url = "http://127.0.0.1:8002/generate_code"
    data = {
        "function_name": "swap",# functionName: 函数名
        "arguments": ["a","b"],# arguements: 函数参数列表
        "doc_string": "swap a and b"# docString: 函数文档字符串
    }
    response = requests.post(url, json=data)
    print("Generated code:", response.json())

# 执行测试用例
if __name__ == "__main__":
    test_generate_code() 