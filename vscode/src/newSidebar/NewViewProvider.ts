import * as vscode from 'vscode'

const fetch = require('node-fetch')



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
                <meta charset="UTF-8">
                <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src ${webview.cspSource};">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>项目级代码生成</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 10px;
                    }
                    label {
                        display: block;
                        margin-top: 10px;
                        margin-bottom: 5px;
                    }
                    select, input, button {
                        width: 100%;
                        padding: 8px;
                        margin-bottom: 10px;
                        box-sizing: border-box;
                    }
                    button {
                        background-color: #007acc;
                        color: white;
                        border: none;
                        cursor: pointer;
                    }
                    button:hover {
                        background-color: #005f99;
                    }
                </style>
            </head>
            <body>
                <h1>项目级代码生成</h1>

                <label for="language">选择编程语言：</label>
                <select id="language">
                    <option value="javascript">JavaScript</option>
                    <option value="python">Python</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="csharp">C#</option>
                </select>

                <label for="requirements">项目需求：</label>
                <input type="text" id="requirements" placeholder="请输入需要生成的项目级别代码的需求" />

                <label for="fileUpload">上传文档：</label>
                <input type="file" id="fileUpload" />

                <label for="questionInput">提问：</label>
                <input type="text" id="questionInput" placeholder="请输入您的问题" />

                <label for="folderUpload">上传文件夹：</label>
                <input type="file" id="folderUpload" webkitdirectory directory />


                <button id="generateButton">生成项目</button>
                <button id="askButton">提问</button>

                <div id="responseContainer"></div>

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
                        const question = document.getElementById('questionInput').value;

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

                    // 读取文件路径并上传
                    document.getElementById('fileUpload').addEventListener('change', () => {
                        const file = document.getElementById('fileUpload').files[0];
                        if (file) {
                            const filePath = file.name;  // 获取文件名（相对路径）
                            const fullPath = file.webkitRelativePath || file.name;  // 获取相对路径（浏览器支持的路径）

                            // 将文件路径上传到后端
                            vscode.postMessage({
                                command: 'uploadFile',
                                filePath: fullPath  // 发送文件路径到后端
                            });
                        }
                    });

                    // 读取文件夹路径并上传
                    document.getElementById('folderUpload').addEventListener('change', () => {
                        const folder = document.getElementById('folderUpload').files;
                        if (folder.length > 0) {
                            // 获取文件夹路径，这里我们只取第一个文件的路径来代表文件夹
                            const filePath = folder[0].webkitRelativePath.split('/')[0];

                            // 将文件夹路径上传到后端
                            vscode.postMessage({
                                command: 'uploadFolder',
                                filePath: filePath  // 发送文件夹路径到后端
                            });
                        }
                    });

                    // 接收来自后端的响应
                    window.addEventListener('message', (event) => {
                        const message = event.data;  // 获取消息数据

                        if (message.command === 'askQuestion') {
                            const responseContainer = document.getElementById('responseContainer');
                            if (responseContainer) {
                                // 使用 innerText 确保只有纯文本插入，避免 HTML 解析引发问题
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
                const filePathUploadFile = message.filePath  // 修改变量名避免冲突
                try {
                    // 这里拼接工作区的绝对路径
                    const workspaceFolders = vscode.workspace.workspaceFolders
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage("没有打开的工作区文件夹！")
                        return
                    }
                    const workspacePath = workspaceFolders[0].uri.fsPath

                    const absolutePath = vscode.Uri.file(`${workspacePath}/${filePathUploadFile}`).fsPath

                    // 发送绝对路径到后端
                    const response = await fetch('http://localhost:8001/upload_file_path', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            file_path: absolutePath,  // 使用绝对路径字段
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log("文件上传成功:", data)
                    vscode.window.showInformationMessage("文件上传成功，RAG链已初始化")
                } catch (error) {
                    vscode.window.showErrorMessage(`上传文件失败: ${error instanceof Error ? error.message : String(error)}`)
                }
                break

            case 'uploadFolder':
                const filePathUploadFolder = message.filePath  // 修改变量名避免冲突
                try {
                    // 这里拼接工作区的绝对路径
                    const workspaceFolders = vscode.workspace.workspaceFolders
                    if (!workspaceFolders) {
                        vscode.window.showErrorMessage("没有打开的工作区文件夹！")
                        return
                    }
                    const workspacePath = workspaceFolders[0].uri.fsPath

                    const absolutePath = vscode.Uri.file(`${workspacePath}/${filePathUploadFolder}`).fsPath

                    // 发送绝对路径到后端
                    const response = await fetch('http://localhost:8001/upload_file_path', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            file_path: absolutePath,  // 使用绝对路径字段
                        }),
                    })

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`)
                    }

                    const data = await response.json()
                    console.log("文件夹上传成功:", data)
                    vscode.window.showInformationMessage("文件夹上传成功，RAG链已初始化")
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
