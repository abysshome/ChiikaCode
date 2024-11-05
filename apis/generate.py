import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# 请求体数据模型
class RequestData(BaseModel):
    question: str
    language: str

# 读取 result.json 文件并返回内容
def read_result_json() -> Dict:
    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            result_json = json.load(f)
        return result_json
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取 result.json 文件时出错: {str(e)}")

# 创建替代接口，直接读取 result.json 文件并返回
@app.post("/generate")
async def generate_project(data: RequestData):
    try:
        # 读取 result.json 并返回
        result_json = read_result_json()
        return {"status": "success", "message": "项目代码生成完成", "result": result_json}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件时出错: {str(e)}")

# 运行应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
