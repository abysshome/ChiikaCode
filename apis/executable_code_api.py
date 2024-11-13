import asyncio
from typing import List

import requests
from fastapi import FastAPI
from ollama import generate
from pydantic import BaseModel


# 定义请求模型
class CodeRequest(BaseModel):
    function_name: str
    arguments: List[str]
    doc_string: str

# 定义返回模型
class CodeResponse(BaseModel):
    code: str

app = FastAPI()

import asyncio
from typing import List

from ollama import generate

model = 'starcoder2:3b'
# model='llama3.2:latest'
num_predict = 256
temperature = 1
top_p = 0.9

# 获得补全的部分
def getCompleteBody(prefix: str, suffix: str) -> str:
    return generate(
        model=model,
        prompt=prefix,
        suffix=suffix,
        options={
            'num_predict': num_predict,
            'temperature': temperature,
            'top_p': top_p,
        }
    )['response']

# 通过函数名和文档字符串获取原始代码
def getOriginalCode(functionName: str, arguements: List[str], docString: str) -> str:
    prefix1 = \
        f'def {functionName} ({", ".join(arguements)}):\n'\
        f'    """ {docString} """'
    suffix1 = \
        f'return'

    body = getCompleteBody(prefix1, suffix1)
    while not body.strip():
        body = getCompleteBody(prefix1, suffix1)
    # print(body)

    functionString = \
        f'# {docString}\n'\
        f'def {functionName} ({", ".join(arguements)}):{body}'

    while body.strip():
        body = getCompleteBody(functionString, '')
        functionString = f'{functionString}{body}'

    prefix2 = \
        f'# imports\n'
    suffix2 = \
        f'\n\n{functionString}'

    import_body = getCompleteBody(prefix2, suffix2)

    res = \
        f'{import_body}\n'\
        f'{functionString}\n'
    return res.strip('\n')

# 通过函数字符串获取测试代码
def getTestCode(functionName: str, functionString: str) -> str:
    prefix = \
        f'{functionString}\n\n'\
        f'# A simple test case\n'\
        f'def test () -> None:\n'\
        f'    '''
    suffix = \
        f'\n\n# Run test function\n'\
        f'if __name__ == "__main__":\n'\
        f'    test()\n'

    body = getCompleteBody(prefix, suffix)

    return f'{prefix}{body}{suffix}'

# 获取没有错误的代码
def getNoErrorCode(functionName: str, arguements: List[str], docString: str) -> str:
    executable = False
    while not executable:
        functionString = getOriginalCode(functionName, arguements, docString)
        try:
            exec(functionString, globals())
            executable = True
        except Exception as e:
            # print(functionString)
            # print(e)
            # input('-----getExecutableCode-----')
            pass
    return functionString

# 获取可运行代码，采用如下策略：
# 1. 尝试生成代码，直到生成的代码没有语法错误
# 2. 尝试生成10次测试代码，如果任意一次通过测试，则认为代码可运行
# 3. 否则回到1
# functionName: 函数名
# arguements: 函数参数列表
# docString: 函数文档字符串
def getExecutable(functionName: str, arguements: List[str], docString: str) -> str:
    runnable = False
    functionString = getNoErrorCode(functionName, arguements, docString)
    count = 0
    while not runnable:
        if count > 10 or 'input' in functionString:
            print('generating new code...')
            functionString = getNoErrorCode(functionName, arguements, docString)
            count = 0
            # print(functionString)
        if 'input' in functionString:
            print('input found')
            continue
        testString = getTestCode(functionName, functionString)
        # print('----- test -----')
        # print(testString)
        # print('----- 0000 -----')
        # input('press any key to continue...')
        try:
            exec(testString, globals())
            runnable = True
        except Exception as e:
            count += 1
            # print(count)
            # print(e)
            print('generating new code...')
            pass

    return functionString

# 创建API路由
@app.post("/generate_code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    code = getExecutable(request.function_name, request.arguments, request.doc_string)
    print(code)
    return {"code": code}

# 启动FastAPI应用的部分
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)