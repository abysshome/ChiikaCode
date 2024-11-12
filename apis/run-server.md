# 1. 运行生成代码api和RAGapi

cd apis
uvicorn generate_code_api:app --host 127.0.0.1 --port 8000

cd apis
uvicorn rag_api:app --host 127.0.0.1 --port 8001

cd apis
uvicorn executable_code_api:app --host 127.0.0.1 --port 8002

# 2. 测试api

python apis\generate_code_api测试.py

python apis\rag_api_upload_file_path测试.py
python apis\rag_api_ask测试.py

# 3. build vscode 插件

cd vscode
pnpm install
pnpm run build

# 4. 监视 ollama

ollama ps
