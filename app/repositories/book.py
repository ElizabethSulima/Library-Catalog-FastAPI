from typing import Any, TypeVar
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book

_T = TypeVar("_T")


class BookRepository:
    """Репозиторий для работы с книгами"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, book: Book) -> Book:
        """
        Создать книгу.

        ORM-подход + refresh, чтобы подтянуть server_default
        колонки (created_at, updated_at) без MissingGreenlet.
        """
        self.session.add(book)
        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def get_by_id(self, book_id: UUID) -> Book | None:
        """Получить книгу по ID."""
        return await self.session.get(Book, book_id)

    async def update(self, book_id: UUID, **data: Any) -> Book | None:
        """
        Обновить книгу.

        Возвращает обновлённый объект или None, если не найдена.
        refresh подтягивает onupdate-колонки (updated_at).
        """
        book = await self.get_by_id(book_id)
        if book is None:
            return None

        for key, value in data.items():
            setattr(book, key, value)

        await self.session.flush()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: UUID) -> bool:
        """
        Удалить книгу.

        Returns:
            True если удалена, False если не найдена.
        """
        book = await self.get_by_id(book_id)
        if book is None:
            return False

        await self.session.delete(book)
        await self.session.flush()
        return True

    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Найти книгу по ISBN."""
        stmt = sa.select(Book).where(Book.isbn == isbn)
        return await self.session.scalar(stmt)

    def _apply_filters(
        self,
        stmt: sa.Select[_T],
        title: str | None,
        author: str | None,
        genre: str | None,
        year: int | None,
        available: bool | None,
    ) -> sa.Select[_T]:
        if title:
            stmt = stmt.where(Book.title.icontains(title, autoescape=True))
        if author:
            stmt = stmt.where(Book.author.icontains(author, autoescape=True))
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if year is not None:
            stmt = stmt.where(Book.year == year)
        if available is not None:
            stmt = stmt.where(Book.available == available)
        return stmt

    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Book]:
        """Поиск книг с фильтрацией и пагинацией"""

        stmt = self._apply_filters(sa.select(Book), title, author, genre, year, available)
        stmt = stmt.order_by(Book.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """Подсчитать количество книг по фильтрам"""

        stmt = self._apply_filters(
            sa.select(sa.func.count()).select_from(  # pylint: disable=E1102
                Book
            ),
            title,
            author,
            genre,
            year,
            available,
        )
        return await self.session.scalar(stmt) or 0
