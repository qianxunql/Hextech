from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek

from aiproject.config import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    if settings.model_provider == "deepseek":
        if not settings.deepseek_api_key:
            raise RuntimeError(
                "缺少 DEEPSEEK_API_KEY。请在 .env.example 旁创建 .env，"
                "或在系统环境变量中设置 DEEPSEEK_API_KEY。"
            )
        return ChatDeepSeek(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            temperature=settings.temperature,
        )

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

    supported = "deepseek, ollama, dashscope"
    raise ValueError(f"Unsupported AI_MODEL_PROVIDER: {settings.model_provider}. Use: {supported}")
