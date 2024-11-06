from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import (CSVLoader, PyPDFLoader,
                                                  PythonLoader, TextLoader)
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


# 数据加载
def upload_file(file_path):
    if file_path.endswith('.py'):
        loader = PythonLoader(file_path)
    elif file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path)
    elif file_path.endswith('.csv'):
        loader = CSVLoader(file_path)
    else:
        raise ValueError('Unsupported file type')
    documents = loader.load() # load documents from file
    print(documents)
    return documents

# 文档分割
def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=10)
    documents = text_splitter.split_documents(documents)
    print("文档分割完成")
    return documents

# 嵌入向量
def get_embedding():
    model_name = r"moka-ai/m3e-base"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': True}
    embedding = HuggingFaceBgeEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    print("嵌入向量获取完成")
    return embedding

# 构建向量数据库
def build_vector_db(documents, embedding):
    persist_directory = 'db'
    db = Chroma.from_documents(
        documents,
        embedding,
        persist_directory=persist_directory
    )
    print("向量数据库构建完成")
    return db

# 构建检索器
def build_retriever(db):
    retriever = db.as_retriever()
    print("检索器构建完成")
    return retriever

# 构建RAG链
def build_rag_chain(retriever):
    template = """
    你是一名负责问答任务的助理。
    使用以下检索到的上下文来回答问题。
    如果你不知道答案，就说你不知道。
    上下文：{context} 请回答问题：{question} """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOllama(model='llama3.2:latest')
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()} |
        prompt |
        llm |
        StrOutputParser()
    )
    print("RAG链构建完成")
    return rag_chain

# 问答
async def chat(rag_chain):
    query = input(">>> Please ask a question: ")
    if not query.strip().endswith('?'):
        query += '?'
    print(">>> RAG-bot:")
    async for chunk in rag_chain.astream(query): # rag_chain.astream(query)返回一个异步生成器
        print(chunk, end='', flush=True) # chunk表示生成的文本片段，end=''表示不换行，flush=True表示立即输出
    print("\n")

# 主函数
async def rag_main(file_path):
    documents = upload_file(file_path)
    documents = split_documents(documents)
    embedding = get_embedding()
    db = build_vector_db(documents, embedding)
    retriever = build_retriever(db)
    rag_chain = build_rag_chain(retriever)
    while True:
        await chat(rag_chain)

if __name__ == '__main__':
    import asyncio
    file_path = input("请输入文件路径")
    asyncio.run(rag_main(file_path))
