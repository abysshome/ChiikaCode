import streamlit as st
import json
import tempfile
import st_helper
from gencode import getRawCodeStream
from share import getLongestCodeBlock, lang_exts, supported_langs,supported_model
from structure import Node, getRawStructureStream, parseStructureString
from apis.rag import split_documents,get_embedding,build_vector_db,build_retriever,upload_file,build_rag_chain,chat,rag_main
from langchain.schema import Document
import pdfplumber
import json
import streamlit as st
import pdfplumber
import json
import asyncio
import hashlib
from langchain.prompts import ChatPromptTemplate

# 用于收集异步生成器输出
async def collect_async_responses(async_gen):
    responses = []
    async for response in async_gen:
        responses.append(response)
    return responses
# 文件读取函数，将文件内容处理成字符串
def read_file_as_string(uploaded_file):
    file_content = None
    
    # 检查文件类型并读取内容
    if uploaded_file.type in ["text/plain", "text/markdown"]:  # 纯文本或 Markdown 文件
        file_content = uploaded_file.read().decode("utf-8")
    
    elif uploaded_file.type == "application/pdf":  # PDF 文件
        file_content = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                file_content += page.extract_text() or ""
    
    elif uploaded_file.type == "application/json":  # JSON 文件
        file_content = json.dumps(json.load(uploaded_file), indent=2, ensure_ascii=False)  # 转换为 JSON 格式字符串
    
    else:
        st.warning("不支持的文件类型")
    
    return file_content

def generate_project():
    if st.session_state['question']: # 如果有输入或上传文件
        language = st.session_state['language'] # 获取语言
        question = st.session_state['question'] or ""  # 获取问题输入
        # add_message("user", "text", question)  # 添加用户消息
        st_helper.stAddMessage("user", "text", question)  # 添加用户消息
        with st.empty(): # st.empty() 可以显示加载动画
            content = st_helper.stWrite(st.chat_message("ai"), getRawStructureStream(question,  language)) # 获取项目结构流
            st_helper.stAddMessage("ai", "text", "根据你的需求，我生成了以下项目结构：")  # 添加AI消息
            # 将生成器内容拼接成一个完整的字符串
            node = parseStructureString(content, language)
        st_helper.stAddMessage("ai", "markdown", node.getStrucureString()) # 添加AI消息
        st.session_state['node'] = node # 保存节点
        startGeneratConfirm() # 开始生成确认

    if st.session_state["generating"]:
        if st.session_state['button_ok']:
            add_message("ai", "开始生成项目代码...")
            generateCode(st.session_state['node'], st.session_state['language'])
            add_message("ai", "项目代码生成完成")
            st.session_state["generating"] = False
        if st.session_state['button_cancel']:
            add_message("ai", "项目代码生成已取消")
            st.session_state["generating"] = False
    if st.session_state["generating"]:
        drawButton()

# 初始化会话状态并包含对话管理
def init():
    if "conversations" not in st.session_state:
        st.session_state["conversations"] = {} # 初始化对话状态
    if "current_conversation" not in st.session_state:
        st.session_state["current_conversation"] = "default" # 初始化当前对话
    st.session_state["generating"] = False # 初始化生成状态
    st.session_state['node'] = None # 初始化节点状态
    st.session_state['question'] = None # 初始化问题状态
    st.session_state['language'] = None  # 初始化语言状态
    st.session_state['button_ok'] = False # 初始化确认按钮状态
    st.session_state['button_cancel'] = False  # 初始化取消按钮状态
    st.session_state['uploaded_file_content'] = None  # 文件内容状态

    if "default" not in st.session_state["conversations"]:
        st.session_state["conversations"]["default"] = [] # 初始化默认对话

    st_helper.stAddMessage("ai", "text", "我是你的 AI 助手，请问您需要什么帮助?", wirte=False)
    st.session_state["initialized"] = True # 初始化完成


# 在侧边栏显示对话选择框并添加新对话按钮
def sidebar():
    st.sidebar.title("对话管理") 

    # 切换对话
    conversation_names = list(st.session_state["conversations"].keys())
    selected_conversation = st.sidebar.selectbox("选择对话", conversation_names) # 选择对话
    if selected_conversation != st.session_state["current_conversation"]:
        st.session_state["current_conversation"] = selected_conversation
        st.session_state["messages"] = st.session_state["conversations"][selected_conversation]

    # 添加新对话
    new_conversation = st.sidebar.text_input("新对话名称")
    if st.sidebar.button("添加对话") and new_conversation:
        if new_conversation not in st.session_state["conversations"]:
            st.session_state["conversations"][new_conversation] = []
            st.session_state["current_conversation"] = new_conversation
            st.session_state["messages"] = st.session_state["conversations"][new_conversation]
            st.sidebar.success("对话已添加")
            
        else:
            st.sidebar.error("对话名称已存在")

def startGeneratConfirm():
    st.session_state["generating"] = True
    st.session_state['button_ok'] = False
    st.session_state['button_cancel'] = False

# 将消息保存到当前对话中
def add_message(role, content, msg_type="text"):
    current_conv = st.session_state["current_conversation"]
    st.session_state["conversations"][current_conv].append({"role": role, "content": content, "type": msg_type})

def drawButton():
    def on_ok():
        st.session_state['button_ok'] = True
    def on_cancel():
        st.session_state['button_cancel'] = True
    st.session_state['button_ok'] = st.button("确定生成", on_click=on_ok)
    st.session_state['button_cancel'] = st.button("取消", on_click=on_cancel)

def generateCode(node: Node, language: str):
    if node is None:
        return

    with st.empty():
        for f_node in node.getFileNodes(lang_exts[language]):
            content = st_helper.stWrite(
                st.chat_message("ai"),
                getRawCodeStream(
                    None,
                    node.getStrucureString(),
                    f_node.getPath(),
                    language
                )
            )
            f_node.content = getLongestCodeBlock(content)
            st_helper.stAddMessage("ai", "text", f"文件: {f_node.getPath()}", wirte=False)
            st_helper.stAddMessage("ai", "markdown", f"f_node.content", wirte=True)

def rag_upload(uploaded_file):
    if uploaded_file:
        file_content = uploaded_file.read().decode("utf-8")
        st.session_state['uploaded_file_content'] = file_content
    
        documents=split_documents(file_content)
        embedding=get_embedding()
        db=build_vector_db(documents,embedding)
        st_helper.stAddMessage("user", "text", f"已上传并存储文件内容：\n{file_content}")
        return db
    

from langchain_community.chat_models import ChatOllama
from langchain.schema.output_parser import StrOutputParser
def generate_ai():
    if st.session_state['question']:
        question = st.session_state['question']
        add_message("user", question)
        st_helper.stAddMessage("user", "text", question) 
        llm = ChatOllama(model='llama3.2:latest')
        rag_chain_ai = (
            llm |
            StrOutputParser()
        )
        with st.empty():
            # 显示AI的回答
            response=st_helper.stWrite(st.chat_message("ai"), rag_chain_ai.stream(question))
            st_helper.stAddMessage("ai", "text", response)
            add_message("ai", response)

def init_main():
    # -------------------- 初始化 -------------------- #
    if "initialized" not in st.session_state:
        init()

    # -------------------- 绘制侧边栏 -------------------- #
    # sidebar()

    # -------------------- 绘制UI界面 -------------------- #
    st.title(st.session_state["current_conversation"])
    st.session_state['model'] = st.selectbox('选择模式', supported_model)
    st.session_state['language'] = st.selectbox("选择语言", supported_langs)
    st_helper.stShowMessages()
    st.session_state['question'] = st.chat_input("输入您的需求")


    #-------------------- 生成代码 -------------------- #
    
    model=st.session_state['model']

    if model == '项目级代码生成':
        generate_project()
        
    elif model == '文档阅读':
        files = []
        # 上传文件功能
        uploaded_file = st.file_uploader("上传文件以提供需求说明", type=   ["txt","pdf", "md", "json"])
        

        if uploaded_file:
            # 获取文件内容哈希值
            file_content = uploaded_file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            # 判断文件是否已上传
            if file_hash not in files:
                files.append(file_hash)
                st.write("文件上传成功！")
                file_content=read_file_as_string(uploaded_file)
                add_message("user",f"上传的内容：\n{file_content}")
                documents = split_documents([Document      (page_content=file_content)])
                embedding = get_embedding()
                db = build_vector_db(documents, embedding)
                retriever = build_retriever(db)
                rag_chain = build_rag_chain(retriever)
            else:
                st.write("该文件已上传，无需重复上传。")
            
        if st.session_state['question']:
            question=st.session_state['question']
            add_message("user", question)
            st_helper.stAddMessage("user", "text", question)
            with st.empty():
                content=st_helper.stWrite(st.chat_message("ai"), rag_chain.stream(question))
                st_helper.stAddMessage("ai", "text", "根据向量数据库内容回答如下：")
                resopnse=''.join(content)
            st_helper.stAddMessage("ai", "text", resopnse)  # 显示AI的  回答
            add_message("ai", resopnse)
    elif model == 'ai对话':
        generate_ai()

if __name__ == '__main__':
    init_main()

