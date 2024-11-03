import streamlit as st
import pdfplumber
import json

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

# 文件上传组件
uploaded_file = st.file_uploader("上传文件以提供需求说明", type=["txt", "pdf", "md", "json"])

# 处理上传的文件
if uploaded_file:
    file_content = read_file_as_string(uploaded_file)
    
    # 检查文件内容是否成功读取
    if file_content:
        st.write("文件内容：")
        st.text(file_content)
    else:
        st.error("文件内容无法读取，请检查文件格式")
