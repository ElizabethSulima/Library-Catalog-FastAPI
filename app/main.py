from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.settings import settings

app = FastAPI(
    title=settings.APP_NAME,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    description="REST API для управления библиотечным каталогом",
)


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
