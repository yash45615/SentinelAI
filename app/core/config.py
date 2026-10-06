from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SentinelAI"
    app_version: str = "0.1.0"

    database_url: str

    cors_origins: str = "http://localhost:5173"

    ai_rca_enabled: bool = False
    ai_rca_provider: str = "openai"
    ai_rca_model: str = "gpt-4.1-mini"
    ai_rca_api_key: str | None = None
    ai_rca_timeout_seconds: int = 30

    app_env: str = "development"

    security_enabled: bool = False
    admin_api_key: str = "change-this-in-production"

    rate_limit_enabled: bool = False
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    docs_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()