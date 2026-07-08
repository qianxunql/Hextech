# Poro

Poro 是一个面向《英雄联盟》海克斯大乱斗玩法的桌面知识库问答助手。应用内置英雄与海克斯强化资料，支持 BM25 文本检索和 Ollama Embedding 语义检索两种知识库召回方式，并通过 DeepSeek 生成简洁、实战导向的回答。

## 功能特性

- AI 问答：围绕英雄、海克斯强化、玩法思路进行知识库问答。
- 英雄名录：查看英雄图片和中文名，按中文名升序排列，支持搜索。
- 海克斯强化：查看海克斯强化图标、评级和描述，支持搜索。
- 详情解析：点击英雄或海克斯后自动生成 AI 实战解析。
- 流式输出：AI 回答边生成边显示，降低等待感。
- 双检索模式：BM25 侧重速度和精确关键词命中，Ollama Embedding 侧重语义召回准确性。
- 桌面体验：自定义标题栏、明暗主题、设置页、首次 API Key 引导。

## 资料源

项目资料整理自 ARAM Hextech Wiki：

- 英雄目录：`https://apexlol.info/zh/champions`
- 英雄详情：`https://apexlol.info/zh/champions/{champion}`
- 海克斯强化目录：`https://apexlol.info/zh/hextech`
- 海克斯强化详情：`https://apexlol.info/zh/hextech/{id}`

资料仅作为知识库来源使用。回答内容由 AI 基于本地资料生成，不代表 Riot Games 或英雄联盟官方数据。

## 版本选择

项目提供两个 Windows 单文件版本：

| 文件 | 检索方式 | 速度 | 准确性特点 | 运行要求 |
|---|---|---:|---|---|
| `Poro-TextIndex.exe` | BM25 文本检索 | 更快 | 对英雄名、海克斯名、明确关键词问题命中稳定 | DeepSeek API Key |
| `Poro.exe` | Ollama Embedding 语义检索 | 取决于本机性能 | 对模糊问法、同义表达、语义相关问题更强 | DeepSeek API Key、Ollama、Embedding 模型 |

BM25 适合这类问题：

```text
亚索适合什么海克斯？
三重射击怎么样？
亮剑适合谁？
```

Ollama Embedding 适合这类问题：

```text
有没有适合一直平 A 的强化？
攻速流该拿哪些海克斯？
想玩持续输出该怎么选强化？
```

首次启动时需要在设置页填写 DeepSeek API Key。API Key 会保存到 exe 同目录的 `.env` 文件：

```text
DEEPSEEK_API_KEY=用户自己的 Key
```

如需指定模型，也可以在 exe 同目录编辑 `.env`：

```text
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=用户自己的 Key
```

## 本地开发

安装依赖：

```powershell
uv sync --all-groups
```

配置 DeepSeek API Key：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

启动 Web 调试界面：

```powershell
uv run hextech-web
```

浏览器打开：

```text
http://127.0.0.1:8765
```

启动 BM25 文本检索版桌面界面：

```powershell
uv run hextech-desktop-text
```

启动 Ollama Embedding 语义检索版桌面界面：

```powershell
uv run hextech-desktop
```

命令行提问：

```powershell
uv run hextech ask "海克斯大乱斗里亚索适合拿什么强化？"
```

## 打包 Windows 应用

构建 BM25 文本检索版：

```powershell
.\scripts\build_windows_text.ps1
```

等价手动命令：

```powershell
uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistantText.spec
```

打包结果：

```text
dist\Poro-TextIndex.exe
```

构建 Ollama Embedding 语义检索版：

```powershell
.\scripts\build_windows.ps1
```

等价手动命令：

```powershell
uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistant.spec
```

打包结果：

```text
dist\Poro.exe
```

## 项目结构

```text
src/aiproject/
  config.py       环境变量和运行时配置
  desktop.py      桌面窗口和 WebView 控制
  desktop_text.py 内置文本索引版桌面入口
  graph.py        LangGraph 工作流装配
  llms.py         DeepSeek 模型创建
  main.py         CLI 与问答入口
  nodes.py        检索与回答节点
  scraper.py      页面解析、资料抓取与本地 HTML 导入
  text_index.py   内置 BM25 文本索引
  vectorstore.py  Chroma / Ollama Embedding 向量检索
  web.py          本地 Web UI 与 HTTP API
```

## 问答流程

```text
用户问题
  -> 精确匹配英雄/海克斯名称
  -> BM25 文本索引或 Ollama Embedding 语义检索召回资料
  -> LangGraph 组织上下文
  -> DeepSeek 生成回答
  -> 前端流式展示
```

## 技术栈

- Python
- LangChain
- LangGraph
- DeepSeek API
- BM25 文本检索
- Ollama Embedding
- Chroma
- HTML / CSS / JavaScript
- pywebview
- PyInstaller

## 说明

本项目是个人学习与工具项目，资料版权归原站点与相关权利方所有。请合理使用 API Key，避免将自己的 Key 内置进 exe 后分发给他人。
