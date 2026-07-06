from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    model_provider: str = "ollama"
    ollama_model: str = "qwen3:4b"
    ollama_embedding_model: str = "nomic-embed-text"
    dashscope_model: str = "qwen-plus"
    temperature: float = 0.2
    knowledge_base_dir: str = "data/chroma"
    collection_name: str = "hex_aram"


def get_settings() -> Settings:
    return Settings(
        model_provider=os.getenv("AI_MODEL_PROVIDER", "ollama").lower(),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        dashscope_model=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
        temperature=float(os.getenv("AI_TEMPERATURE", "0.2")),
        knowledge_base_dir=os.getenv("KNOWLEDGE_BASE_DIR", "data/chroma"),
        collection_name=os.getenv("CHROMA_COLLECTION", "hex_aram"),
    )
