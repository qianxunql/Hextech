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

    supported = "deepseek"
    raise ValueError(f"Unsupported AI_MODEL_PROVIDER: {settings.model_provider}. Use: {supported}")
