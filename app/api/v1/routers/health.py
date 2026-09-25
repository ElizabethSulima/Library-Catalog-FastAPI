import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.api.dependencies import DbSessionDep
from app.core.settings import settings
from app.schemas.paginations import HealthCheckResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

START_TIME = datetime.now(timezone.utc)


@router.get(
    "/",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверить состояние сервиса и подключение к БД",
    responses={
        200: {"description": "Сервис работает корректно"},
        503: {"description": "Сервис работает, но БД недоступна"},
    },
)
async def health_check(db: DbSessionDep):
    """
    Проверить здоровье сервиса.

    Проверяет:
    - Сервис запущен
    - Подключение к БД работает
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
        overall_status = "healthy"
        http_status = status.HTTP_200_OK
    except Exception as exc:  # pylint: disable=W0718
        logger.error("Database health check failed: %s", exc, exc_info=True)
        db_status = "disconnected"
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    uptime_seconds = (datetime.now(timezone.utc) - START_TIME).total_seconds()

    response = HealthCheckResponse(
        status=overall_status,
        database=db_status,
        version=(
            settings.APP_VERSION
            if hasattr(settings, "APP_VERSION")
            else "unknown"
        ),
        uptime_seconds=int(uptime_seconds),
        timestamp=datetime.now(timezone.utc),
    )
    if http_status != status.HTTP_200_OK:
        raise HTTPException(
            status_code=http_status,
            detail=response.model_dump(),
        )

    return response
