from fastapi import FastAPI
from pydantic import BaseModel
import json

# 导入您的现有模块
import st_helper
from gencode import getRawCodeStream
from share import getLongestCodeBlock, lang_exts, supported_langs
from structure import Node, getRawStructureStream, parseStructureString

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 根据需要设置允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义请求模型
class GenerateRequest(BaseModel):
    question: str
    language: str


# 定义响应模型
class GenerateResponse(BaseModel):
    status: str
    message: str
    project_structure: str = None
    files: dict = None


@app.post("/generate", response_model=GenerateResponse)
def generate_project(request: GenerateRequest):
    try:
        question = request.question
        language = request.language

        # 调用您的生成逻辑
        content = getRawStructureStream(question, language)
        node = parseStructureString(content, language)
        project_structure = node.getStrucureString()

        # 生成代码文件内容
        files = {}
        for f_node in node.getFileNodes(lang_exts[language]):
            code_content = getRawCodeStream(
                None, node.getStrucureString(), f_node.getPath(), language
            )
            f_node.content = getLongestCodeBlock(code_content)
            files[f_node.getPath()] = f_node.content

        return GenerateResponse(
            status="success",
            message="项目代码生成成功",
            project_structure=project_structure,
            files=files,
        )

    except Exception as e:
        return GenerateResponse(status="error", message=str(e))
