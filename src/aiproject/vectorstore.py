from __future__ import annotations

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from aiproject.config import Settings, get_settings
from aiproject.scraper import ChampionPage


def build_embeddings(settings: Settings) -> OllamaEmbeddings:
    return OllamaEmbeddings(model=settings.ollama_embedding_model)


def get_vectorstore(settings: Settings | None = None) -> Chroma:
    settings = settings or get_settings()
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=build_embeddings(settings),
        persist_directory=settings.knowledge_base_dir,
    )


def pages_to_documents(pages: list[ChampionPage]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
        separators=["\n\n", "\n", "。", "，", " ", ""],
    )
    documents: list[Document] = []
    for page in pages:
        documents.append(
            Document(
                page_content=f"英雄页面：{page.name}\n来源：{page.url}\n\n{page.text}",
                metadata={"champion": page.name, "source": page.url},
            )
        )
    return splitter.split_documents(documents)


def ingest_pages(pages: list[ChampionPage], settings: Settings | None = None) -> int:
    vectorstore = get_vectorstore(settings)
    chunks = pages_to_documents(pages)
    if not chunks:
        return 0
    try:
        vectorstore.add_documents(chunks)
    except ConnectionError as exc:
        raise RuntimeError(
            "无法连接 Ollama，知识库入库需要本地 Embedding 模型。"
            "请先启动 Ollama，并执行：ollama pull nomic-embed-text"
        ) from exc
    return len(chunks)
