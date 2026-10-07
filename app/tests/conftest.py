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

from app.core.session import get_async_session
from app.external.openlibrary.client import OpenLibraryClient
from app.main import create_app
from app.models.base import BaseModel
from app.repositories.book import BookRepository
from app.services.book import BookService


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
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
