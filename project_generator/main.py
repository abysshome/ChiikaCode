import streamlit as st
import json

import st_helper
from gencode import getRawCodeStream
from share import getLongestCodeBlock, lang_exts, supported_langs
from structure import Node, getRawStructureStream, parseStructureString


def init():
    st.session_state["messages"] = []
    st.session_state["generating"] = False
    st.session_state['node'] = None
    st.session_state['question'] = None
    st.session_state['language'] = None
    st.session_state['button_ok'] = False
    st.session_state['button_cancel'] = False

    st_helper.stAddMessage("ai", "text", "你需要生成什么项目?", wirte=False)

    st.session_state["initialized"] = True

def startGeneratConfirm():
    st.session_state["generating"] = True
    st.session_state['button_ok'] = False
    st.session_state['button_cancel'] = False

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

# -------------------- 初始化 -------------------- #
if "initialized" not in st.session_state:
    init()

# -------------------- 绘制UI界面 -------------------- #
st.title("项目级代码生成")
st.session_state['language'] = st.selectbox("选择语言", supported_langs)
st_helper.stShowMessages()

st.session_state['question'] = st.chat_input("项目需求")

if st.session_state['question']:
    language = st.session_state['language']
    question = st.session_state['question']
    st_helper.stAddMessage("user", "text", question)
    with st.empty():
        content = st_helper.stWrite(st.chat_message("ai"), getRawStructureStream(question, language))
        node = parseStructureString(content, language)
        st_helper.stAddMessage("ai", "text", "根据你的需求，我生成了以下项目结构：")
    st_helper.stAddMessage("ai", "markdown", node.getStrucureString())
    st.session_state['node'] = node
    startGeneratConfirm()

if st.session_state["generating"]:
    if st.session_state['button_ok']:
        st_helper.stAddMessage("ai", "text", "开始生成项目代码...")
        generateCode(st.session_state['node'], st.session_state['language'])
        st_helper.stAddMessage("ai", "text", "项目代码生成完成")
        with open('reult.json', 'w', encoding='utf-8') as f:
            json.dump(st.session_state['node'].getJsonDict(), f, indent=4)
        st.session_state["generating"] = False
    if st.session_state['button_cancel']:
        st_helper.stAddMessage("ai", "text", "项目代码生成已取消")
        st.session_state["generating"] = False

if st.session_state["generating"]:
    drawButton()