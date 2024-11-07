import * as vscode from 'vscode'

const fetch = require('node-fetch')

const path = require('path')


export class NewViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'newView';

    constructor() {
        console.log('NewViewProvider initialized')
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        console.log('resolveWebviewView called for newView')

        webviewView.webview.options = {
            enableScripts: true, // Enable scripts for handling interaction
        }

        webviewView.webview.html = this.getHtmlForWebview(webviewView.webview)

        // Listen for messages from Webview
        webviewView.webview.onDidReceiveMessage(async message => {
            await this.handleMessage(message, webviewView)
        })
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        const nonce = this.getNonce()


        return `
<!DOCTYPE html>
<html lang="zh-CN">

<head>
  <title>Home</title>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <meta name="robots" content="index,follow" />
  <meta name="generator" content="GrapesJS Studio" />
  <style>
    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
      background-color: #f9fafb;
      color: #333;
    }

    .container {
      max-width: 600px;
      width: 100%;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      margin-bottom: 20px;
    }

    h1 {
      font-size: 24px;
      text-align: center;
      color: #007acc;
      margin-bottom: 20px;
    }

    .form-group {
      margin-bottom: 20px;
    }

    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
    }

    select,
    input[type="text"],
    input[type="file"] {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 16px;
      box-sizing: border-box;
      transition: border-color 0.2s;
    }

    select:focus,
    input:focus {
      border-color: #007acc;
      box-shadow: 0 0 5px rgba(0, 122, 204, 0.5);
    }

    button {
      width: 100%;
      padding: 12px;
      margin-top: 10px;
      background-color: #007acc;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
      transition: background-color 0.3s;
    }

    button:hover {
      background-color: #005f99;
    }

    .button-group {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: space-between;
    }

    .button-group button {
      flex: 1 1 48%;
    }

    @media (max-width: 600px) {
      body {
        padding: 15px;
      }

      h1 {
        font-size: 20px;
      }

      .button-group button {
        flex: 1 1 100%;
      }
    }
  </style>
</head>

<body>
  <div class="container">
    <h1>Chiika <font color="#2463eb">Code</font></h1>
    <div class="text-main-content" style="text-align: center; margin-bottom: 20px;">项目级代码生成工具</div>

    <!-- 选择编程语言 -->
    <div class="form-group">
      <label for="language">选择编程语言</label>
      <select id="language">
        <option value="python">Python</option>
        <option value="javascript">JavaScript</option>
        <option value="C">C#</option>
        <option value="typescript">TypeScript</option>
      </select>
    </div>

    <!-- 输入项目需求 -->
    <div class="form-group">
      <label for="requirements">项目需求</label>
      <input type="text" id="requirements" placeholder="请输入项目需求" />
    </div>

    <!-- 按钮组 -->
    <div class="button-group">
        <button type="button" id="uploadFileButton">上传文件</button>
        <input type="file" id="fileUpload" style="display: none;">

        <button type="button" id="uploadFolderButton">上传文件夹</button>
        <input type="file" id="folderUpload" webkitdirectory directory style="display: none;"> 

        <button type="button" id="generateButton">生成项目</button>
        <button type="button" id="askButton">提问</button>
    </div>
  </div>
    <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();

    // 生成项目按钮点击事件
    document.getElementById('generateButton').addEventListener('click', () => {
        const language = document.getElementById('language').value;
        const requirements = document.getElementById('requirements').value;

        // 调用后端接口生成项目
        vscode.postMessage({
            command: 'generateProject',
            language: language,
            requirements: requirements
        });
    });
    // 提问按钮点击事件
    document.getElementById('askButton').addEventListener('click', () => {
        const question = document.getElementById('requirements').value;

        if (question.trim()) {
            // 提交问题到后端
            vscode.postMessage({
                command: 'askQuestion',
                question: question
            });
        } else {
            alert("请输入问题！");
        }
    });
    // 文件上传按钮点击事件
    document.getElementById('uploadFileButton').addEventListener('click', function(event) {
        event.preventDefault();  // 防止默认行为，确保触发 input
        document.getElementById('fileUpload').click();
    });

    // 文件夹上传按钮点击事件
    document.getElementById('uploadFolderButton').addEventListener('click', function(event) {
        event.preventDefault();  // 防止默认行为，确保触发 input
        document.getElementById('folderUpload').click();
    });
    // 上传文件
    document.getElementById('fileUpload').addEventListener('change', () => {
        const file = document.getElementById('fileUpload').files[0];
        if (file) {
            const filePath = file.name;  // 仅获取文件名
            const fullPath = file.webkitRelativePath || file.name;  // 获取相对路径

            // 获取文件的完整路径，不依赖工作区路径
            const absoluteFilePath = file.path || fullPath;  // 在此我们尝试直接使用文件的绝对路径

            // 将文件路径上传到后端
            vscode.postMessage({
                command: 'uploadFile',
                filePath: absoluteFilePath  // 发送完整的文件路径到后端
            });
        }
    });
    // 上传文件夹
    document.getElementById('folderUpload').addEventListener('change', () => {
        const folder = document.getElementById('folderUpload').files;
        if (folder.length > 0) {
            // 获取文件夹的相对路径（通常是第一个文件的路径），然后提取文件夹名称
            const relativeFolderPath = folder[0].webkitRelativePath.split('/')[0];
            console.log('上传文件夹名:', relativeFolderPath);

            // 只传递文件夹名，不需要完整路径
            vscode.postMessage({
                command: 'uploadFolder',
                folderName: relativeFolderPath,  // 发送文件夹名
            });

        } else {
            vscode.window.showErrorMessage("没有选择文件夹中的任何文件！");
        }
    });




    // 接收来自后端的响应
    window.addEventListener('message', (event) => {
        const message = event.data;  // 获取消息数据

        if (message.command === 'askQuestion') {
            const responseContainer = document.getElementById('responseContainer');
            if (responseContainer) {
                // 如果后端没有返回 answer 字段，显示错误信息
                const answer = message.answer || '未找到答案';  // 如果没有返回答案，则显示默认消息
                responseContainer.innerHTML = '';  // 清空之前的内容

                const answerElement = document.createElement('p');
                const strongElement = document.createElement('strong');
                strongElement.innerText = '答案: ';
                answerElement.appendChild(strongElement);
                answerElement.appendChild(document.createTextNode(answer));
                responseContainer.appendChild(answerElement);
            }
        }
    });
    </script>
    </body>

    </html>

        `
    }

    private async handleMessage(message: any, webviewView: vscode.WebviewView) {
        switch (message.command) {
            case 'generateProject':
                const { language, requirements } = message
                try {
                    const response = await fetch('http://localhost:8000/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            question: requirements,
                            language: language,
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log("收到的数据: ", data)

                    if (data.status === "success") {
                        if (data.result && data.result.files && typeof data.result.files === 'object') {
                            console.log("文件信息:", data.result.files)
                            await this.saveGeneratedFiles(data.result.files)
                        } else {
                            vscode.window.showErrorMessage("生成的文件信息缺失或格式不正确。")
                        }
                    } else {
                        vscode.window.showErrorMessage("生成项目时失败: " + (data.message || "未知错误"))
                    }

                } catch (error) {
                    vscode.window.showErrorMessage(`请求失败: ${error instanceof Error ? error.message : String(error)}`)
                }
                break

            case 'askQuestion':
                const { question } = message
                try {
                    const response = await fetch('http://127.0.0.1:8001/ask', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            question: question
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log("收到的数据: ", data)

                    // 向 Webview 发送答案
                    webviewView.webview.postMessage({
                        command: 'askQuestion',
                        answer: data.answer || '未找到答案'
                    })

                } catch (error) {
                    vscode.window.showErrorMessage(`请求失败: ${error instanceof Error ? error.message : String(error)}`)
                }
                break


            case 'uploadFile':
                const { filePath } = message  // 获取文件路径
                try {
                    console.log(`上传文件路径: ${filePath}`)

                    // 获取工作区路径
                    const workspaceFolders = vscode.workspace.workspaceFolders
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage("没有打开的工作区文件夹！")
                        return
                    }

                    const workspacePath = workspaceFolders[0].uri.fsPath
                    const absoluteFilePath = path.join(workspacePath, filePath)  // 拼接工作区路径和文件路径
                    console.log(`上传文件的绝对路径: ${absoluteFilePath}`)

                    // 调用后端 API 上传文件路径
                    const response = await fetch('http://127.0.0.1:8001/upload_file_path', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            file_path: absoluteFilePath,  // 发送文件的绝对路径
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log(data)  // 打印后端返回的数据
                    vscode.window.showInformationMessage("文件上传成功，RAG链已初始化！")

                } catch (error) {
                    vscode.window.showErrorMessage(`上传文件失败: ${error instanceof Error ? error.message : String(error)}`)
                }
                break

            case 'uploadFolder':
                const { folderName } = message  // 获取文件夹名
                try {
                    console.log(`上传的文件夹名: ${folderName}`)

                    // 获取工作区路径
                    const workspaceFolders = vscode.workspace.workspaceFolders
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage("没有打开的工作区文件夹！")
                        return
                    }

                    const workspacePath = workspaceFolders[0].uri.fsPath
                    console.log("工作区路径:", workspacePath)

                    // 拼接文件夹的绝对路径
                    const absoluteFolderPath = path.join(workspacePath, folderName)
                    console.log('拼接后的文件夹路径:', absoluteFolderPath)

                    // 调用后端 API 上传文件夹路径（可以上传整个文件夹或者做进一步操作）
                    const response = await fetch('http://127.0.0.1:8001/upload_file_path', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            file_path: absoluteFolderPath,  // 发送拼接后的路径
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log(data)  // 打印后端返回的数据
                    vscode.window.showInformationMessage("文件夹上传成功，RAG链已初始化！")

                } catch (error) {
                    vscode.window.showErrorMessage(`上传文件夹失败: ${error instanceof Error ? error.message : String(error)}`)
                }
                break



        }
    }

    private async saveGeneratedFiles(files: { [path: string]: string }) {
        const workspaceFolders = vscode.workspace.workspaceFolders
        if (!workspaceFolders) {
            vscode.window.showErrorMessage("没有打开的工作区文件夹！")
            return
        }

        const workspacePath = workspaceFolders[0].uri.fsPath

        for (const [filePath, content] of Object.entries(files)) {
            console.log(`保存文件: ${filePath}`)
            console.log(`文件内容: ${content}`)

            const absoluteFilePath = vscode.Uri.file(`${workspacePath}/${filePath}`)
            const fileFolder = absoluteFilePath.with({ path: absoluteFilePath.path.split('/').slice(0, -1).join('/') })

            const edit = new vscode.WorkspaceEdit()

            await vscode.workspace.fs.createDirectory(vscode.Uri.file(fileFolder.path))

            edit.createFile(absoluteFilePath, { overwrite: true })
            edit.set(absoluteFilePath, [
                new vscode.TextEdit(new vscode.Range(0, 0, 0, 0), content)
            ])

            await vscode.workspace.applyEdit(edit)
        }
    }


    private getNonce(): string {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        let result = ''
        for (let i = 0; i < 32; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length))
        }
        return result
    }
}