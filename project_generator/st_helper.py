from typing import Iterator

import streamlit as st
from streamlit.delta_generator import DeltaGenerator


def stWrite(chat_message: DeltaGenerator, s: Iterator[str]) -> str:
    ''' 写入 Streamlit 文本框, 并返回写入的内容 '''
    result = []
    def append_line(line: str):
        result.append(line)
        return line
    my_stream = (append_line(line) for line in s)
    chat_message.write(my_stream)
    return ''.join(result)

def __stShowMessage(msg: dict):
    if msg["type"] == "text":
        st.chat_message(msg["role"]).write(msg["content"])
    elif msg["type"] == "markdown":
        st.chat_message(msg["role"]).code(msg["content"], language="markdown")

def stAddMessage(role: str, _type: str, message: str, wirte: bool = True):
    """ role = ['ai', 'user']; type = ['text', 'markdown'] """

    msg = {"role": role, "type": _type, "content": message}
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    st.session_state["messages"].append(msg)

    if wirte:
        __stShowMessage(msg)

def stShowMessages():
    for msg in st.session_state.messages:
        __stShowMessage(msg)