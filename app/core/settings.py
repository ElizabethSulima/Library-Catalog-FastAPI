from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):  # type: ignore[misc]
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True

    # fastapi app
    APP_NAME: str = "LIBRARY CATALOG"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Cors
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = False

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DB_POOL_SIZE: int = 20

    # Open library
    OPENLIBRARY_BASE_URL: str = "https://openlibrary.org"
    OPENLIBRARY_TIMEOUT: float = 10.0

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def docs_url(self) -> str | None:
        """Swagger UI включен в dev/staging, выключен в prod."""
        return None if self.is_production else "/docs"

    @property
    def redoc_url(self) -> str | None:
        return None if self.is_production else "/redoc"

    @property
    def openapi_url(self) -> str | None:
        return None if self.is_production else "/openapi.json"

    @property
    def database_url(self) -> URL:
        """
        Возвращает объект URL для SQLAlchemy(create_async_engin /create_engine)
        """
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @property
    def alembic_database_url(self) -> str:
        """
        Строка подключения специально для Alembic
        """
        return self.database_url.render_as_string(hide_password=False).replace("%", "%%")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
