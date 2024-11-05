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

        # Call your generation logic
        content = getRawStructureStream(question, language)
        node = parseStructureString(content, language)
        project_structure = node.getStrucureString()

        files = {}
        for f_node in node.getFileNodes(lang_exts[language]):
            code_content = list(getRawCodeStream(None, node.getStrucureString(), f_node.getPath(), language))
            print(f"Code content for {f_node.getPath()}: {code_content}, Type: {type(code_content)}")

            if code_content:
                first_item = code_content[0]
                print(f"First item: {first_item}, Type: {type(first_item)}")
                if isinstance(first_item, str):
                    f_node.content = getLongestCodeBlock(first_item)
                    files[f_node.getPath()] = f_node.content
                else:
                    print(f"Expected a string but got: {type(first_item)}")
            else:
                print(f"No code content generated for {f_node.getPath()}")

        return GenerateResponse(
            status="success",
            message="项目代码生成成功",
            project_structure=project_structure,
            files=files,
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return GenerateResponse(status="error", message=str(e))
