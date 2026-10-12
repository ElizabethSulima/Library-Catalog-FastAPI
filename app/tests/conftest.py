import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from respx import MockRouter
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password
from app.core.session import get_async_session
from app.external.openlibrary.client import OpenLibraryClient
from app.main import create_app
from app.models.base import BaseModel
from app.models.user import User
from app.repositories.book import BookRepository
from app.services.book import BookService


@pytest.fixture(scope="function")
def engine() -> AsyncEngine:
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
async def setup_db(engine: AsyncEngine) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)


@pytest.fixture
async def db_session(setup_db: None, engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Свежая сессия для каждого теста с гарантированным откатом транзакции"""
    async with engine.connect() as connection, connection.begin() as transaction:
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
def app(db_session: AsyncSession) -> FastAPI:
    app = create_app()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_db
    app.state.ol_client = OpenLibraryClient(base_url="https://openlibrary.org")
    return app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Создает тестового пользователя в БД"""
    unique_suffix = str(uuid.uuid4())[:8]
    user = User(
        email=f"test_{unique_suffix}@example.com",
        username=f"testuser_{unique_suffix}",
        hashed_password=hash_password("SecureTestPassword123!"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_password() -> str:
    """Возвращает известный пароль тестового пользователя"""
    return "SecureTestPassword123!"


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """
    Генерирует валидный access-токен и возвращает словарь заголовков
    для использования в httpx запросах.
    """
    token = create_access_token(data={"sub": str(test_user.user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_openlibrary_success(respx_mock: MockRouter) -> MockRouter:
    """Успешный ответ от Open Library с обложкой"""
    respx_mock.get(url__regex=r"openlibrary\.org").respond(
        json={
            "num_found": 1,
            "docs": [
                {
                    "title": "Clean Code",
                    "author_name": ["Robert Martin"],
                    "cover_i": 8234567,
                }
            ],
        }
    )
    return respx_mock


@pytest.fixture
def mock_openlibrary_timeout(respx_mock: MockRouter) -> MockRouter:
    """Имитация таймаута Open Library"""
    respx_mock.get(url__regex=r"openlibrary\.org").mock(
        side_effect=httpx.TimeoutException("Simulated timeout")
    )
    return respx_mock


@pytest.fixture
def book_service(db_session: AsyncSession) -> BookService:
    repo = BookRepository(session=db_session)
    ol_client = OpenLibraryClient(base_url="https://openlibrary.org")
    return BookService(book_repository=repo, openlibrary_client=ol_client)


@pytest.fixture(autouse=True)
def reset_rate_limiter(app: FastAPI) -> None:
    """
    Очищает хранилище rate limiter перед каждым тестом.

    Это предотвращает ошибку 429 Too Many Requests
    """
    if hasattr(limiter, "reset"):
        limiter.reset()
    else:
        if hasattr(limiter, "_storage") and hasattr(limiter._storage, "storage"):
            limiter._storage.storage.clear()
