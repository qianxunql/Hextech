# 英雄联盟海克斯大乱斗助手

基于 LangChain + LangGraph 的知识库问答助手。资料源默认来自：

- `https://apexlol.info/zh/champions`
- `https://apexlol.info/zh/champions/x`
- `https://apexlol.info/zh/hextech`
- `https://apexlol.info/zh/hextech/x`

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

下载并导入海克斯详情页：

```powershell
$env:APEXLOL_COOKIE="cf_clearance=..."
uv run python -m aiproject.main download-hextech --index-html "海克斯强化列表 _ ARAM Hextech Wiki.html"
uv run python -m aiproject.main ingest-hextech --index-html "海克斯强化列表 _ ARAM Hextech Wiki.html" --html-dir data/html/hextech
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
uv run hextech-desktop
```

启动内置文本索引版桌面界面：

```powershell
uv run hextech-desktop-text
```

### 打包 Windows 应用

生成 Ollama Embedding 版单文件桌面应用：

```powershell
.\scripts\build_windows.ps1
```

等价手动命令：

```powershell
uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistant.spec
```

打包结果在：

```text
dist\Poro.exe
```

生成内置文本索引版单文件桌面应用：

```powershell
.\scripts\build_windows_text.ps1
```

等价手动命令：

```powershell
uv sync --all-groups
uv run pyinstaller --noconfirm --clean HextechAssistantText.spec
```

打包结果在：

```text
dist\Poro-TextIndex.exe
```

两个 exe 都是单文件应用，已经内置：

- `data/chroma` 知识库
- 英雄目录页、英雄详情页索引数据
- 海克斯目录页、海克斯详情页索引数据
- 英雄图片和海克斯图标

不要把项目源码、`.venv`、`data` 文件夹一起发给用户。只需要发送：

```text
dist\Poro.exe
```

或者发送内置文本索引版：

```text
dist\Poro-TextIndex.exe
```

两个版本区别：

| 文件 | 检索方式 | 用户电脑要求 |
|---|---|---|
| `Poro.exe` | Chroma + Ollama Embedding | DeepSeek API Key、Ollama、`nomic-embed-text` |
| `Poro-TextIndex.exe` | exe 内置 HTML 资料 + 文本索引 | DeepSeek API Key |

### 给别人使用

用户双击 exe 后会打开桌面应用窗口。

第一次使用时点击左下角设置按钮，填写自己的 DeepSeek API Key。API Key 会保存到 exe 同目录的 `.env` 文件：

```text
DEEPSEEK_API_KEY=用户自己的 Key
```

如果发给别人使用，推荐发送 `Poro-TextIndex.exe`。这个版本不需要安装 Ollama，不需要项目源码，也不需要单独发送知识库文件。

如果需要指定 DeepSeek 模型，也可以在 exe 同目录手动创建或编辑 `.env`：

```text
AI_MODEL_PROVIDER=deepseek
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_KEY=用户自己的 Key
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

内置文本索引版会在启动时自动使用：

```text
RETRIEVAL_MODE=text
```

原 Ollama 版默认使用：

```text
RETRIEVAL_MODE=ollama
```

## LangGraph

当前问答图：

```text
START -> retrieve -> answer -> END
```

后续可以继续加入意图识别、召回重排、装备推荐、强化推荐、阵容克制、人工审核等节点。
