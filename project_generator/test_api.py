import requests
import json

url = "http://localhost:8000/generate"

# 定义请求数据
data = {
    "question": "请生成一个简单的Python项目",
    "language": "Python"
}

# 设置请求头
headers = {
    "Content-Type": "application/json"
}

# 发送POST请求
response = requests.post(url, headers=headers, data=json.dumps(data))

# 打印响应结果
print("状态码：", response.status_code)
print("响应数据：", response.json())
