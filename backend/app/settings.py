from functools import lru_cache
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables / .env.
    """

    # Core service config
    APP_NAME: str = "fastapi-tracking-service"

    # Redis configuration
    REDIS_URL: AnyUrl = "redis://redis:6379"
    REDIS_CHANNEL: str = "locations"

    # Simple auth
    API_KEY: str | None = None

    # History configuration
    MAX_DEVICE_HISTORY: int = 1000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance so we don't recreate it on each request.
    """
    return Settings()


