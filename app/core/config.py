from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    vectorstore_url: str = "http://localhost:6333"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
