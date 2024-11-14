import json
from typing import Iterator, Optional

from fastapi import FastAPI, HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from pydantic import BaseModel
from rag_api import (build_rag_chain, build_retriever, get_embedding,
                     get_vector_db, handle_folder)
from share import getLongestCodeBlock, lang_exts, llm, supported_langs
from structure import Node, getRawStructureStream, parseStructureString

app = FastAPI()

# 请求体数据模型
class RequestData(BaseModel):
    question: str
    language: str

from langchain.schema.runnable import RunnablePassthrough


def getRawCodeStream(user_requirement: str, code_structure: str, filename: str, language: str) -> Iterator[str]:
    """通过用户需求、代码结构、语言、文件名，生成大模型回答的原始字符流"""

    # 获取嵌入和数据库
    embedding = get_embedding()
    db = get_vector_db(embedding)
    retriever = build_retriever(db)

    language = language.lower()
    if language not in supported_langs:
        raise ValueError(f"Unsupported language: {language}. (Support: {supported_langs})")

    # 定义模板
    template = """
        请根据以下信息，为指定文件生成基本 {language} 代码。
        可参考的知识库：{retriever}
        用户需求：{user_requirement}
        代码框架：
        ```markdown
        {code_structure}
        ```
        需要生成的文件：{filename}。
        回答：
    """
    prompt = ChatPromptTemplate.from_template(template)

    # 构建数据流，确保输入通过 RunnablePassthrough 顺利传递
    llm_chain = (
        RunnablePassthrough() |
        prompt |
        llm |
        StrOutputParser()
    )
    
    # 将数据传递到 stream 函数
    return llm_chain.stream({
        "language": language,
        "retriever": retriever,
        "user_requirement": user_requirement,
        "code_structure": code_structure,
        "filename": filename
    })


# 初始化 FastAPI应用
@app.on_event("startup")
async def startup_event():
    print("FastAPI 服务已启动...")

# 生成代码结构的函数
def generate_code_structure(question: str, language: str) -> dict:
    # 获取项目结构流
    structure_content ="".join(getRawStructureStream(question, language))
    print("getRawStructureStream 成功")
    print(structure_content)

    # 解析项目结构字符串为 Node 对象
    node = parseStructureString(structure_content, language)
    print("parseStructureString 成功")

    if not node:
        raise HTTPException(status_code=500, detail="生成项目结构失败")
    
    # 生成代码内容并保存到节点
    for f_node in node.getFileNodes(lang_exts[language]):
        print(f_node)
        content = "".join(getRawCodeStream(None, node.getStrucureString(), f_node.getPath(), language))
        f_node.content = getLongestCodeBlock(content)
        print(f_node.content)
    
    # 将结构转换为 JSON 格式并保存
    result_json = node.getJsonDict()
    print(result_json)
    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_json, f, indent=4)
    
    return result_json

# 创建API端点
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
