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

先准备 Ollama 聊天模型和向量模型：

```powershell
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

抓取目录页下的全部英雄资料并入库：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ingest
```

如果目标站点拒绝程序抓取，可以先用浏览器打开英雄目录页并另存为 `.html`，
放到 `data/html/champions_index.html`，再从目录页本地副本导入：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ingest --index-html data/html/champions_index.html
```

如果你另存为的是多个英雄详情页，也可以从本地目录导入：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ingest --html-dir data/html
```

如果已经有可访问站点的浏览器 Cookie，可以临时设置 `APEXLOL_COOKIE`
并批量下载英雄详情页：

```powershell
$env:PYTHONPATH="src"
$env:APEXLOL_COOKIE="cf_clearance=..."
uv run python -m aiproject.main download --index-html data/html/champions_index.html
```

调试时可以只抓几个：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ingest --limit 3
```

也可以指定英雄 URL 名：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ingest --champion Aatrox --champion Ahri
```

提问：

```powershell
$env:PYTHONPATH="src"
uv run python -m aiproject.main ask "海克斯大乱斗里亚索适合拿什么强化？"
```

By default the project uses Ollama:

```powershell
$env:AI_MODEL_PROVIDER="ollama"
$env:OLLAMA_MODEL="qwen3:4b"
$env:OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
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
