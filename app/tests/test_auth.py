import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.user import User

pytestmark = pytest.mark.anyio


class TestAuthEndpoints:
    async def test_login_success(self, client: AsyncClient, test_user: User, user_password: str):
        """Успешный логин возвращает токены"""
        payload = {
            "username": test_user.username,
            "password": user_password,
        }
        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Логин с неверным паролем возвращает 401"""
        payload = {
            "username": test_user.username,
            "password": "wrong_password",
        }
        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "User not found"
