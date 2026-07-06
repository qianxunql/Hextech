from dataclasses import dataclass
from contextlib import contextmanager
from contextvars import ContextVar
import os
from pathlib import Path
from typing import Any, Iterator


SETTINGS_OVERRIDES: ContextVar[dict[str, Any]] = ContextVar("settings_overrides", default={})


@dataclass(frozen=True)
class Settings:
    model_provider: str = "deepseek"
    deepseek_model: str = "deepseek-chat"
    deepseek_api_key: str = ""
    ollama_model: str = "qwen3:4b"
    ollama_embedding_model: str = "nomic-embed-text"
    dashscope_model: str = "qwen-plus"
    temperature: float = 0.2
    knowledge_base_dir: str = "data/chroma"
    collection_name: str = "hex_aram"


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_settings() -> Settings:
    load_dotenv()
    overrides = SETTINGS_OVERRIDES.get()
    return Settings(
        model_provider=overrides.get("model_provider", os.getenv("AI_MODEL_PROVIDER", "deepseek")).lower(),
        deepseek_model=overrides.get("deepseek_model", os.getenv("DEEPSEEK_MODEL", "deepseek-chat")),
        deepseek_api_key=overrides.get("deepseek_api_key", os.getenv("DEEPSEEK_API_KEY", "")),
        ollama_model=overrides.get("ollama_model", os.getenv("OLLAMA_MODEL", "qwen3:4b")),
        ollama_embedding_model=overrides.get(
            "ollama_embedding_model",
            os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        ),
        dashscope_model=overrides.get("dashscope_model", os.getenv("DASHSCOPE_MODEL", "qwen-plus")),
        temperature=float(overrides.get("temperature", os.getenv("AI_TEMPERATURE", "0.2"))),
        knowledge_base_dir=overrides.get("knowledge_base_dir", os.getenv("KNOWLEDGE_BASE_DIR", "data/chroma")),
        collection_name=overrides.get("collection_name", os.getenv("CHROMA_COLLECTION", "hex_aram")),
    )


@contextmanager
def settings_override(**overrides: Any) -> Iterator[None]:
    current = SETTINGS_OVERRIDES.get().copy()
    current.update({key: value for key, value in overrides.items() if value is not None})
    token = SETTINGS_OVERRIDES.set(current)
    try:
        yield
    finally:
        SETTINGS_OVERRIDES.reset(token)
