from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.2"
    openai_timeout: float = 30.0
    vectorstore_url: str = "http://localhost:6333"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        if self.app_env.lower() in {"local", "test"}:
            return self

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required outside local/test environments.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
