import json
from typing import Iterator, Optional

from fastapi import FastAPI, HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel
from share import getLongestCodeBlock, lang_exts, llm, supported_langs
from structure import Node, getRawStructureStream, parseStructureString

app = FastAPI()

# 请求体数据模型
class RequestData(BaseModel):
    question: str
    language: str


def getRawCodeStream(user_requirement: str, code_structure: str, filename: str, language: str) -> Iterator[str]:
    """通过用户需求、代码结构、语言、文件名，生成大模型回答的原始字符流"""

    language = language.lower()
    if language not in supported_langs:
        raise ValueError(f"Unsupported language: {language}. (Support: {supported_langs})")

    template = f"""
        请根据以下信息，为指定文件生成基本 {language} 代码。
        用户需求：{user_requirement}
        代码框架：
        ```markdown
        {code_structure}
        ```
        需要生成的文件：{filename}。
        回答：
    """
    prompt = ChatPromptTemplate.from_template(template)
    llm_chain = (
        prompt |
        llm |
        StrOutputParser()
    )
    return llm_chain.stream({})

# 初始化 FastAPI 应用
@app.on_event("startup")
async def startup_event():
    print("FastAPI 服务已启动...")

# 生成代码结构的函数
def generate_code_structure(question: str, language: str) -> dict:
    # 获取项目结构流
    structure_content = "".join(getRawStructureStream(question, language))
    print("getRawStructureStream 成功")
    print(structure_content)

    # 解析项目结构字符串为 Node 对象
    node = parseStructureString(structure_content, language)
    print("parseStructureString 成功")

    if not node:
        raise HTTPException(status_code=500, detail="生成项目结构失败")
    
    # 生成代码内容并保存到节点
    files = {}
    for f_node in node.getFileNodes(lang_exts[language]):
        print(f_node)
        content = "".join(getRawCodeStream(None, node.getStrucureString(), f_node.getPath(), language))
        f_node.content = getLongestCodeBlock(content)
        print(f_node.content)

        # 将文件路径和内容添加到文件字典
        files[f_node.getPath()] = f_node.content
    
    # 返回包含 files 的 JSON 格式
    print("返回的文件内容: ", files)  # 调试输出，检查返回的文件字典
    return {"files": files}



# 创建 API 端点
@app.post("/generate")
async def generate_project(data: RequestData):
    print(data)
    # 检查语言是否支持
    if data.language not in supported_langs:
        raise HTTPException(status_code=400, detail=f"语言 '{data.language}' 不受支持")
    
    print("语言支持")
    # 调用生成代码结构的函数
    try:
        result_json = generate_code_structure(data.question, data.language)
        print("generate_code_structure 成功")
        return {"status": "success", "message": "项目代码生成完成", "result": result_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成代码时出错: {str(e)}")

# 运行应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
