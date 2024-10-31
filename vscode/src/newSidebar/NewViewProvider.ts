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
        // 生成随机 nonce 用于 Content Security Policy
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
                    <!-- 可以根据需要添加更多语言选项 -->
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
                // 在这里处理生成项目的逻辑，例如调用后端 API
                vscode.window.showInformationMessage(`生成项目：语言=${language}, 需求=${requirements}`);
                break;
        }
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
