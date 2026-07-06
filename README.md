# 英雄联盟海克斯大乱斗助手

基于 LangChain + LangGraph 的知识库问答助手。资料源默认来自：

- `https://apexlol.info/zh/champions`
- `https://apexlol.info/zh/champions/x`

## Project Layout

```text
src/aiproject/
  config.py      Runtime settings from environment variables
  llms.py        LangChain chat model factory
  scraper.py     Champion page discovery and scraping
  vectorstore.py Chroma vector database helpers
  state.py       LangGraph state schema
  nodes.py       Graph node implementations
  graph.py       LangGraph workflow assembly
  main.py        CLI entry point
```

## Quick Start

先配置 DeepSeek API Key。复制 `.env.example` 为 `.env`，然后在 `.env` 里填写：

```text
DEEPSEEK_API_KEY=你的 DeepSeek API Key
```

`.env` 文件在项目根目录：

```text
D:\Study\AIProject\.env
```

如果还没有本地向量模型，准备 Ollama 向量模型：

```powershell
ollama pull nomic-embed-text
```

抓取目录页下的全部英雄资料并入库：

```powershell
uv run python -m aiproject.main ingest
```

如果目标站点拒绝程序抓取，可以先用浏览器打开英雄目录页并另存为 `.html`，
放到 `data/html/champions_index.html`，再从目录页本地副本导入：

```powershell
uv run python -m aiproject.main ingest --index-html data/html/champions_index.html
```

如果你另存为的是多个英雄详情页，也可以从本地目录导入：

```powershell
uv run python -m aiproject.main ingest --html-dir data/html
```

如果已经有可访问站点的浏览器 Cookie，可以临时设置 `APEXLOL_COOKIE`
并批量下载英雄详情页：

```powershell
$env:APEXLOL_COOKIE="cf_clearance=..."
uv run python -m aiproject.main download --index-html data/html/champions_index.html
```

调试时可以只抓几个：

```powershell
uv run python -m aiproject.main ingest --limit 3
```

也可以指定英雄 URL 名：

```powershell
uv run python -m aiproject.main ingest --champion Aatrox --champion Ahri
```

提问：

```powershell
uv run python -m aiproject.main ask "海克斯大乱斗里亚索适合拿什么强化？"
```

也可以使用脚本入口：

```powershell
uv run hextech ask "海克斯大乱斗里亚索适合拿什么强化？"
```

## Desktop App

启动本地 Web 界面：

```powershell
uv run hextech-web
```

然后打开：

```text
http://127.0.0.1:8765
```

启动桌面界面：

```powershell
uv run hextech-gui
```

打包 Windows 可执行文件：

```powershell
uv run pyinstaller --noconsole --onedir --name HextechAssistant --paths src --add-data "data;data" src\aiproject\gui.py
```

打包结果在：

```text
dist\HextechAssistant\HextechAssistant.exe
```

By default the project uses DeepSeek for answering:

```powershell
AI_MODEL_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=
```

Ollama is still used for local embeddings by default:

```powershell
$env:OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
```

To use Ollama for answering instead:

```powershell
$env:AI_MODEL_PROVIDER="ollama"
$env:OLLAMA_MODEL="qwen3:4b"
```

To use DashScope Tongyi:

```powershell
$env:AI_MODEL_PROVIDER="dashscope"
$env:DASHSCOPE_API_KEY="your-api-key"
$env:DASHSCOPE_MODEL="qwen-plus"
```

## LangGraph

当前问答图：

```text
START -> retrieve -> answer -> END
```

后续可以继续加入意图识别、召回重排、装备推荐、强化推荐、阵容克制、人工审核等节点。
