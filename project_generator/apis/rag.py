from langchain_community.document_loaders import PythonLoader, PyPDFLoader, TextLoader, CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=65536, chunk_overlap=10)
    documents = text_splitter.split_documents(documents)
    print("文档分割完成")
    return documents

# 嵌入向量
def get_embedding():
    model_name = 'moka-ai/m3e-base'
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
    print("RAG链构建完成")
    return rag_chain

# 问答
async def chat(rag_chain):
    query = input(">>> Please ask a question: ")
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
    file_path = input("输入文件路径：")
    asyncio.run(rag_main(file_path))