from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

import models
from repositories import BookRepository


class BookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = BookRepository(self.session)

    async def get_books(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[models.Book]:
        """Получить список книг с фильтрацией"""

        return await self.repository.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=limit,
            offset=offset,
        )

    async def get_book_by_id(self, book_id: int) -> models.Book | None:
        """Получить книгу по ID"""
        return await self.repository.get_item_id(book_id)

    async def get_book_by_isbn(self, isbn: str) -> models.Book | None:
        """Получить книгу по ISBN"""
        return await self.repository.find_by_isbn(isbn)

    async def create_book(self, data: dict) -> models.Book:
        """Создать новую книгу"""
        return await self.repository.create_item(data)

    async def update_book(
        self, book_id: int, data: dict
    ) -> models.Book | None:
        """Обновить книгу"""
        data["id"] = book_id
        return await self.repository.update_item(data)

    async def delete_book(self, book_id: int) -> None:
        """Удалить книгу"""
        await self.repository.delete_item(book_id)

    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """Подсчитать количество книг по фильтрам"""
        return await self.repository.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )
