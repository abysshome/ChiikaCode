import os

import requests

# 上传文件路径初始化RAG链的端点
upload_url = "http://127.0.0.1:8000/upload_file_path"
# 当前目录的路径加上文件相对路径
file_path=os.path.join(os.getcwd(), "apis\关于举办第十八届全国大学生软件创新大赛-软件设计创新赛的参赛通知.pdf")
print(file_path)
file_path_payload = {
    "file_path": file_path
}

# 发送 POST 请求
response = requests.post(upload_url, json=file_path_payload)
print(response.json())
