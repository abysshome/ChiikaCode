import os

import uvicorn
from fastapi import FastAPI, HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import (CharacterTextSplitter,
                                     RecursiveCharacterTextSplitter)
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import (CSVLoader, PyPDFLoader,
                                                  PythonLoader, TextLoader)
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from pydantic import BaseModel

app = FastAPI()

# 定义一个请求模型，用于接收文件路径
class FilePathRequest(BaseModel):
    file_path: str

# 数据加载
def load_file(file_path):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="文件路径不存在")

    if file_path.endswith('.py'):
        loader = PythonLoader(file_path)
    elif file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path)
    else:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    documents = loader.load()
    return documents

# 文档分割
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=65536, chunk_overlap=10)
    documents = text_splitter.split_documents(documents)
    return documents

# 嵌入向量获取
def get_embedding():
    model_name = 'moka-ai/m3e-base'
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    embedding = HuggingFaceBgeEmbeddings(
        model_name=model_name, 
        model_kwargs=model_kwargs, 
        encode_kwargs=encode_kwargs
    )
    return embedding

# 构建向量数据库
def build_vector_db(documents, embedding):
    persist_directory = 'db'
    db = Chroma.from_documents(
        documents, 
        embedding, 
        persist_directory=persist_directory
    )
    return db

# 构建检索器
def build_retriever(db):
    retriever = db.as_retriever()
    return retriever

# 构建RAG链
def build_rag_chain(retriever):
    template = """
        根据context详细解释有关question的内容，并给出答案。
        Question: {question} Context: {context} Answer: """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOllama(model='llama3.2:latest')
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()} |
        prompt |
        llm |
        StrOutputParser()
    )
    return rag_chain

# 全局变量，用于保存 RAG 链
rag_chain = None

# 上传文件路径并初始化 RAG 链
@app.post("/upload_file_path")
async def upload_file_path(request: FilePathRequest):
    global rag_chain
    try:
        # 加载文件
        documents = load_file(request.file_path)
        documents = split_documents(documents)
        embedding = get_embedding()
        db = build_vector_db(documents, embedding)
        retriever = build_retriever(db)
        rag_chain = build_rag_chain(retriever)
        return {"message": "文件路径上传成功，RAG链已初始化"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

# 定义提问模型
class QuestionRequest(BaseModel):
    question: str

# 提问并获取答案
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    global rag_chain
    if not rag_chain:
        raise HTTPException(status_code=400, detail="RAG链尚未初始化，请先上传文件路径")

    question = request.question
    answer = ""
    async for chunk in rag_chain.astream(question):
        answer += chunk
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)