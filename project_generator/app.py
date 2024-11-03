from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from gencode import getRawCodeStream
from share import getLongestCodeBlock, lang_exts, supported_langs
from structure import Node, getRawStructureStream, parseStructureString

app = FastAPI()

# 请求体数据模型
class RequestData(BaseModel):
    question: str
    language: str

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
