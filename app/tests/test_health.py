from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import fastapi as fa
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import get_async_session

pytestmark = pytest.mark.anyio


class TestHealthEndpoints:
    """Тесты для эндпоинтов Liveness и Readiness"""

    async def test_liveness_check_always_returns_200(self, app: fa.FastAPI) -> None:
        """
        Liveness check не зависит от БД и всегда должен возвращать 200,
        пока приложение запущено.
        """

        async def failing_get_db() -> None:
            raise ConnectionError("Database connection failed")

        app.dependency_overrides[get_async_session] = failing_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health/live")

            assert response.status_code == fa.status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "alive"
            assert "version" in data

    async def test_readiness_check_healthy_db(self, app: fa.FastAPI) -> None:
        """
        Readiness check с рабочей БД возвращает 200 и status: healthy
        """
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")

            assert response.status_code == fa.status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert "version" in data
            assert "uptime_seconds" in data
            assert "timestamp" in data

    async def test_readiness_check_failing_db_returns_503(self, app: fa.FastAPI) -> None:
        """
        Readiness check с падающей БД возвращает 503 и status: unhealthy.
        """
        mock_session = AsyncMock()
        mock_session.execute.side_effect = ConnectionError("Database connection failed")

        async def failing_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield mock_session

        app.dependency_overrides[get_async_session] = failing_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")
            assert response.status_code == fa.status.HTTP_503_SERVICE_UNAVAILABLE

            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert "version" in data
            assert "uptime_seconds" in data
            assert "timestamp" in data

            assert "error_code" not in data
            assert "detail" not in data
