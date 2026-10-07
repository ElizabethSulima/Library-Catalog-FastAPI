from typing import Any

import fastapi as fa
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book

pytestmark = pytest.mark.anyio


class TestBookEndpoints:
    """Интеграционные тесты API"""

    async def test_create_and_get_book(self, client: AsyncClient) -> None:
        """Создание и получение книги"""
        payload = {
            "title": "Clean Code",
            "author": "Robert Martin",
            "year": 2008,
            "genre": "Programming",
            "pages": 464,
            "isbn": "978-0132350884",
        }

        response = await client.post("/api/v1/books/", json=payload)
        assert response.status_code == fa.status.HTTP_201_CREATED
        data = response.json()
        book_id = data["book_id"]
        assert data["title"] == "Clean Code"

        response_get = await client.get(f"/api/v1/books/{book_id}")
        assert response_get.status_code == fa.status.HTTP_200_OK
        assert response_get.json()["title"] == "Clean Code"

    async def test_create_with_openlibrary_enrichment(
        self, client: AsyncClient, mock_openlibrary_success: Any
    ) -> None:
        """Клиент OL через MockTransport"""
        payload = {
            "title": "Clean Code",
            "author": "Robert Martin",
            "year": 2008,
            "genre": "Programming",
            "pages": 464,
            "isbn": "9780132350884",
        }

        response = await client.post("/api/v1/books/", json=payload)
        assert response.status_code == fa.status.HTTP_201_CREATED

        data = response.json()
        # 1. Проверка базовых полей
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["year"] == payload["year"]
        assert data["genre"] == payload["genre"]
        assert data["pages"] == payload["pages"]
        assert data["isbn"] == payload["isbn"]

        # 2. Проверка сгенерированных полей
        assert "book_id" in data
        assert isinstance(data["available"], bool)
        assert "created_at" in data
        assert "updated_at" in data

        # 3. ГЛАВНАЯ ПРОВЕРКА: данные успешно обогатились из Open Library
        assert data["extra"] is not None, "Поле extra не должно быть None при успешном обогащении"
        assert isinstance(data["extra"], dict)
        assert "cover_url" in data["extra"], "В поле extra должен присутствовать cover_url"

    async def test_create_with_openlibrary_timeout_fallback(
        self,
        client: AsyncClient,
        mock_openlibrary_timeout: Any,
        db_session: AsyncSession,
    ) -> None:
        """Сервис с заглушкой enricher, которая бросает таймаут"""
        payload = {
            "title": "Clean Code",
            "author": "Robert Martin",
            "year": 2008,
            "genre": "Programming",
            "pages": 464,
            "isbn": "9780132350884",
        }

        response = await client.post("/api/v1/books/", json=payload)
        assert response.status_code == fa.status.HTTP_201_CREATED

        data = response.json()
        assert data["title"] == payload["title"]
        assert data["isbn"] == payload["isbn"]

        assert data.get("extra") is None, "При таймауте Open Library поле extra должно быть null"

        stmt = select(Book).where(Book.isbn == payload["isbn"])
        result = await db_session.execute(stmt)
        db_book = result.scalar_one_or_none()

        assert db_book is not None, "Книга не была сохранена в базу данных"
        assert db_book.title == payload["title"]
        assert db_book.extra is None, "В базе данных поле extra также должно быть None"

    async def test_duplicate_isbn_returns_409(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Повторный ISBN → 409 Conflict"""
        payload = {
            "title": "Clean Code",
            "author": "Robert Martin",
            "year": 2008,
            "genre": "Programming",
            "pages": 464,
            "isbn": "9780132350884",
        }

        first_response = await client.post("/api/v1/books/", json=payload)
        assert first_response.status_code == fa.status.HTTP_201_CREATED

        response = await client.post("/api/v1/books/", json=payload)
        assert response.status_code == fa.status.HTTP_409_CONFLICT

        data = response.json()
        assert data["code"] == "book_already_exists"
        assert data["detail"] == "Book with ISBN '9780132350884' already exists"
        assert "details" in data
        assert data["details"]["isbn"] == "9780132350884"

        stmt = (
            select(func.count())  # pylint: disable=E1102
            .select_from(Book)
            .where(Book.isbn == payload["isbn"])
        )
        count = await db_session.scalar(stmt)
        assert count == 1

    async def test_patch_with_null_title_returns_422(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Тест на PATCH с {"title": null} → 422, а не 500"""
        book = Book(
            title="Old Title",
            author="Author",
            year=2020,
            genre="Fiction",
            pages=100,
            isbn="1111111111",
        )
        db_session.add(book)
        await db_session.commit()
        await db_session.refresh(book)

        response = await client.patch(
            f"/api/v1/books/{book.book_id}",
            json={"title": None},
        )
        assert response.status_code == fa.status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
