# 1. 运行生成代码api

cd apis 
uvicorn generate_code_api:app --host 127.0.0.1 --port 8000
cd apis 
uvicorn generate:app --host 127.0.0.1 --port 8000

# 2. 测试api

python apis\generate_code_api测试.py

# 3. build vscode 插件

cd vscode
pnpm install
pnpm run build

# 4. 监视 ollama

ollama ps
