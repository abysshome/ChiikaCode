from langchain_community.document_loaders import PythonLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 本地数据加载
documents = PyPDFLoader(r"test.pdf").load()
print(documents)

print('load finished')

# 文档分割
text_splitter = CharacterTextSplitter(chunk_size=65536, chunk_overlap=10)
documents = text_splitter.split_documents(documents)

# 词嵌入
model_name = 'moka-ai/m3e-base'
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}
embedding = HuggingFaceBgeEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
print('embedding finished')

# 数据入库
persist_directory = 'db'
db = Chroma.from_documents(documents, embedding, persist_directory=persist_directory)

# 检索
retriever = db.as_retriever()

# 增强
template = """
    You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise.
    Question: {question} Context: {context} Answer: """
prompt = ChatPromptTemplate.from_template(template)


# 生成
llm = ChatOllama(model='qwen:7b')
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()} |
    prompt |
    llm |
    StrOutputParser()
)

async def ask_question(llm, question):
    print("开始回答---------------")
    # 定义消息列表，包括用户的问题
    messages = [
        ("human", question),
    ]

    # 使用astream方法逐个词语输出
    async for chunk in llm.astream(messages):
        print(chunk.content, end=' ', flush=True)

async def chat():
    query = input(">>> Please ask a question: ")
    print(">>> RAG-bot:")
    async for chunk in rag_chain.astream(query): # rag_chain.astream(query)返回一个异步生成器
        print(chunk, end='', flush=True) # chunk表示生成的文本片段，end=''表示不换行，flush=True表示立即输出
    print("\n")

async def main():
    while True:
        await chat()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())