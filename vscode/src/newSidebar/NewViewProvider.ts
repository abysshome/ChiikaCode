import * as vscode from 'vscode';

export class NewViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'newView';

    constructor() {
        console.log('NewViewProvider initialized');
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        console.log('resolveWebviewView called for newView');

        webviewView.webview.options = {
            enableScripts: true, // 启用脚本以处理交互
        };

        webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

        // 监听来自 Webview 的消息
        webviewView.webview.onDidReceiveMessage(async message => {
            await this.handleMessage(message);
        });
    }

    private getHtmlForWebview(webview: vscode.Webview): string {
        const nonce = getNonce();

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

                <button id="generateButton">生成项目</button>

                <script nonce="${nonce}">
                    const vscode = acquireVsCodeApi();

                    document.getElementById('generateButton').addEventListener('click', () => {
                        const language = document.getElementById('language').value;
                        const requirements = document.getElementById('requirements').value;

                        vscode.postMessage({
                            command: 'generateProject',
                            language: language,
                            requirements: requirements
                        });
                    });
                </script>
            </body>
            </html>
        `;
    }

    private async handleMessage(message: any) {
        switch (message.command) {
            case 'generateProject':
                const { language, requirements } = message;
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
                    });
    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
    
                    const data = await response.json();
                    console.log("收到的数据: ", data);  // 调试输出，查看返回的数据
    
                    if (data.status === "success") {
                        if (data.result && data.result.files && typeof data.result.files === 'object') {
                            console.log("文件信息:", data.result.files);
                            await this.saveGeneratedFiles(data.result.files);
                        } else {
                            vscode.window.showErrorMessage("生成的文件信息缺失或格式不正确。");
                        }
                    } else {
                        vscode.window.showErrorMessage("生成项目时失败: " + (data.message || "未知错误"));
                    }
    
                } catch (error) {
                    vscode.window.showErrorMessage(`请求失败: ${error instanceof Error ? error.message : String(error)}`);
                }
                break;
        }
    }
    

    private async saveGeneratedFiles(files: { [path: string]: string }) {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage("没有打开的工作区文件夹！");
            return;
        }

        const workspacePath = workspaceFolders[0].uri.fsPath;

        for (const [filePath, content] of Object.entries(files)) {
            console.log(`保存文件: ${filePath}`);
            console.log(`文件内容: ${content}`);
            // 保存文件的逻辑
            const fullPath = vscode.Uri.file(`${workspacePath}/${filePath}`);
            const edit = new vscode.WorkspaceEdit();
            edit.createFile(fullPath, { overwrite: true }); // 创建文件
            edit.insert(fullPath, new vscode.Position(0, 0), content); // 插入内容
            console.log(`保存文件: ${fullPath.toString()}`);
            console.log(`文件内容: ${content}`);

            await vscode.workspace.applyEdit(edit);
        }
        await vscode.workspace.saveAll();
    }
}

// 辅助函数生成随机字符串，用于 Content Security Policy 的 nonce
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
