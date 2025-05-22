
# ChiikaCode

<p align="center">
  <img src="https://storage.googleapis.com/sourcegraph-assets/blog/vs-code-onboarding-walkthrough-dec-2023-cody-autocomplete-tsx.gif" width="600" alt="ChiikaCode 演示">
</p>

## 项目简介

ChiikaCode 是一个基于 Cody 的智能代码辅助工具，它利用先进的 AI 技术帮助开发者更快地理解、编写和修复代码。ChiikaCode 使用增强检索生成（RAG）技术，能够从本地和远程代码库中提取上下文信息，使您能够在 VS Code 中利用整个代码库中的 API、符号和使用模式等上下文信息，无论代码库规模如何。

## 主要功能

### 代码自动补全

ChiikaCode 可以在任何编程语言、配置文件或文档中自动补全单行代码或整个函数。它由最新的即时大语言模型提供支持，确保准确性和性能。

### 智能对话

通过 ChiikaCode 的聊天功能，您可以询问有关一般编程主题或特定代码库的问题。您可以启用增强上下文功能，让 ChiikaCode 包含您打开的项目信息，或标记特定文件和符号以优化您的聊天提示。

示例问题：
- "我们的应用在 Linux 上如何实现密钥存储？"
- "Web 集成测试的 CI 配置在哪里？"
- "为 AuditLog 编写一个新的 GraphQL 解析器"
- "为什么 UserConnectionResolver 给出'未知用户'错误，如何修复？"
- "添加有用的调试日志语句"

### 内置命令

通过使用 ChiikaCode 命令，简化您的开发过程，帮助理解、改进、修复、记录代码并为代码生成单元测试。

### 自定义命令（测试版）

您还可以构建自己的自定义命令，使 ChiikaCode 适应您的工作流程。自定义命令在您的代码库中定义为 JSON，可以保存到工作区供团队成员重复使用。

### RAG 技术支持

ChiikaCode 采用检索增强生成（RAG）技术，通过知识检索和生成模型的结合来提升生成代码的质量和准确性。

## 安装指南

### 环境要求

- Node.js >= 18
- pnpm >= 8.6.7

### 安装步骤

1. 安装 [asdf](https://asdf-vm.com/)
2. 运行 `asdf install`（如有需要，运行 `asdf plugin add NAME` 安装缺失的插件）
3. 运行 `pnpm install && pnpm build`

## 使用说明

### 启动开发服务器

```bash
pnpm -C agent agent
```

### 构建项目

```bash
pnpm build
```

### 运行测试

```bash
pnpm test          # 运行所有测试
pnpm test:unit     # 仅运行单元测试
pnpm test:integration  # 运行集成测试
pnpm test:e2e      # 运行端到端测试
```

## 项目架构

ChiikaCode 项目由以下主要组件构成：

- **前端**：VS Code 扩展，提供用户界面和交互功能
- **代理（Agent）**：实现 JSON-RPC 服务器，通过 stdout/stdin 与 Cody 交互
- **API**：提供代码生成、RAG 检索等核心功能
- **后端**：处理复杂的代码分析和生成任务

## 参考资料

- Visual Studio Code 插件开发指南
- RAG 检索增强生成技术指南
- 开源大语言模型部署指南
- Python 编码标准与代码质量提升指南
- 大模型集成及推理框架
- VSCode API 参考文档
- Embedding 模型使用手册

## 许可证

[Apache-2.0](LICENSE)

## 贡献指南

欢迎对 ChiikaCode 项目做出贡献！请参阅我们的开发文档了解更多信息。

## 联系我们

如有任何问题或建议，请通过 GitHub Issues 与我们联系。
