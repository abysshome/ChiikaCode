const vscode = acquireVsCodeApi()

document.getElementById('generateButton').addEventListener('click', () => {
    const language = document.getElementById('language').value
    const question = document.getElementById('question').value

    fetch('http://127.0.0.1:8000/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ language, question }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const output = document.getElementById('output')
                output.innerHTML = `<h2>项目结构：</h2><pre>${data.project_structure}</pre>`

                // 发送消息给扩展主线程，处理文件生成
                vscode.postMessage({
                    command: 'generateFiles',
                    files: data.files,
                })
            } else {
                alert('生成失败：' + data.message)
            }
        })
        .catch(error => {
            console.error('Error:', error)
            alert('请求失败，请确保 API 服务正在运行。')
        })
})
