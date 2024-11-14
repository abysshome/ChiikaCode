from fastapi import FastAPI, HTTPException
from generate_code_api import RequestData,supported_langs, generate_code_structure
import uvicorn
app = FastAPI()

# 项目级代码生成
@app.post("/generate_project")
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
    
from executable_code_api import getExecutable, CodeResponse,CodeRequest
# 创建API路由
@app.post("/generate_executable_code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    code = getExecutable(request.function_name, request.arguments, request.doc_string)
    print(code)
    return {"code": code}

# rag
from rag_api import QuestionRequest, SingletonResources, FilePathRequest, handle_folder,load_file, split_documents, get_embedding, build_vector_db, get_vector_db, build_retriever, build_rag_chain
import os
@app.post("/rag_ask")
async def ask_question(request: QuestionRequest):
    resources = SingletonResources()
    if not resources.rag_chain:
        raise HTTPException(status_code=400, detail="RAG链尚未初始化，请先上传文件路径")

    question = request.question
    answer = ""
    async for chunk in resources.rag_chain.astream(question):
        answer += chunk
    return {"answer": answer}

@app.post("/upload_file_path")
async def upload_file_path(request: FilePathRequest):
    resources = SingletonResources()
    resources.initialize_embedding()
    try:
        # 如果是文件夹
        if os.path.isdir(request.file_path):
            handle_folder(request.file_path)
        # 如果是文件
        else:
            documents = load_file(request.file_path)  # 加载文件
            documents = split_documents(documents)
            build_vector_db(documents, resources.embedding)
        # 获取向量数据库
        db = get_vector_db(resources.embedding)
        retriever = build_retriever(db)
        resources.initialize_rag_chain(retriever)
        return {"message": "文件路径上传成功，RAG链已初始化"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)