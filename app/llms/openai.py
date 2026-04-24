from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings


def create_openai_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    settings = settings or get_settings()

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout,
    )
