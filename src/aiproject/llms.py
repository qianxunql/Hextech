from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from aiproject.config import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    if settings.model_provider == "ollama":
        return init_chat_model(
            settings.ollama_model,
            model_provider="ollama",
            temperature=settings.temperature,
        )

    if settings.model_provider == "dashscope":
        return init_chat_model(
            settings.dashscope_model,
            model_provider="tongyi",
            temperature=settings.temperature,
        )

    supported = "ollama, dashscope"
    raise ValueError(f"Unsupported AI_MODEL_PROVIDER: {settings.model_provider}. Use: {supported}")
