from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow", env_file=".env")

    ROOT_DIR: Path = Path(__file__).parent.parent.resolve()
    MEDIA_DIR: Path = ROOT_DIR / "media"
    BASE_URL: str = ""

    # run server
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: Literal["development", "staging", "production"] = (
        "development"
    )

    # Redis TTL for auth sessions (seconds)
    REDIS_EXPIRE_TIME: int = 60

    # fastapi app
    APP_NAME: str = "LIBRARY CATALOG"
    APP_ALLOWED_ORIGINS: list[str] = ["*"]
    APP_ALLOWED_HOSTS: list[str] = ["*"]
    APP_VERSION: str = "1.0.0"
    DOCS_URL: str | None = None
    REDOC_URL: str | None = None
    CORS_ORIGINS: list[str] = ["*"]

    # DB settings
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "library_catalog"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_POOL_SIZE: int = 20

    # Open library
    OPENLIBRARY_BASE_URL: str = "https://openlibrary.org"
    OPENLIBRARY_TIMEOUT: float = 10.0

    @computed_field
    def dsn(self) -> str:
        return (
            f"postgresql+psycopg://{self.DB_USER}:"
            f"{self.DB_PASSWORD}@{self.DB_HOST}:"
            f"{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
