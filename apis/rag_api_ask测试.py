import requests

# 提问端点
ask_url = "http://127.0.0.1:8001/ask"
question_payload = {
    "question": "报名截止日期是哪一天"  # 替换为实际问题
}

# 发送 POST 请求
response = requests.post(ask_url, json=question_payload)
print(response.json())
