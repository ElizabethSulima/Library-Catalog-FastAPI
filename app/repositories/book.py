from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.repositories.common import Base as BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = Book

    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Book]:
        """Поиск книг с фильтрацией"""

        stmt = sa.select(self.model)

        if title:
            stmt = stmt.where(self.model.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(self.model.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(self.model.genre.ilike(f"%{genre}%"))
        if year is not None:
            stmt = stmt.where(self.model.year == year)
        if available is not None:
            stmt = stmt.where(self.model.available == available)

        stmt = (
            stmt.order_by(self.model.book_id.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def find_by_isbn(self, isbn: str) -> Book | None:
        """Найти книгу по ISBN"""
        stmt = sa.select(self.model).where(self.model.isbn == isbn)
        result = await self.session.scalar(stmt)
        return result

    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """Подсчитать количество книг по фильтрам"""

        stmt = sa.select(sa.func.count()).select_from(  # pylint: disable=E1102
            self.model
        )
        if title:
            stmt = stmt.where(self.model.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(self.model.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(self.model.genre.ilike(f"%{genre}%"))
        if year is not None:
            stmt = stmt.where(self.model.year == year)
        if available is not None:
            stmt = stmt.where(self.model.available == available)

        result = await self.session.scalar(stmt)
        return result or 0
