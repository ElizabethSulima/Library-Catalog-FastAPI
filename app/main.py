"""
Library Catalog API - Точка входа приложения.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.routers import books, health
from app.core.dependency import dispose_engine
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import setup_logging
from app.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI.

    Выполняется при:
    - startup: настройка логирования
    - shutdown: закрытие подключений к БД
    """
    # Startup
    setup_logging()
    print("🚀 Application started")

    yield

    # Shutdown
    await dispose_engine()
    print("👋 Application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    version="1.0.0",
    description="REST API для управления библиотечным каталогом",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(
    books.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    health.router,
    prefix=settings.API_V1_PREFIX,
)


@app.get("/")
async def root():
    """Корневой эндпоинт."""
    return {
        "message": "Welcome to Library Catalog API",
        "docs": settings.DOCS_URL,
        "version": "1.0.0",
    }


if not settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.APP_ALLOWED_ORIGINS,
        allow_credentials=True,
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.APP_ALLOWED_HOSTS
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
