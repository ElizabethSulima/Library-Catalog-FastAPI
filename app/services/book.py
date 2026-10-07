import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
    InvalidPagesException,
    InvalidYearException,
    OpenLibraryException,
)
from app.domain.mappers.book_mapper import BookMapper
from app.external.openlibrary.client import OpenLibraryClient
from app.models.book import Book
from app.repositories.book import BookRepository
from app.schemas.book import (
    BookCreate,
    BookResponse,
    BookUpdate,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)


class BookService:
    """
    Сервис для работы с книгами.

    Содержит всю бизнес-логику приложения.
    """

    def __init__(
        self,
        book_repository: BookRepository,
        openlibrary_client: OpenLibraryClient,
    ):
        self.book_repo = book_repository
        self.ol_client = openlibrary_client

    async def create_book(self, book_data: BookCreate) -> BookResponse:
        """
        Создать новую книгу с обогащением из Open Library
        """
        if book_data.isbn:
            existing = await self.book_repo.find_by_isbn(book_data.isbn)
            if existing:
                raise BookAlreadyExistsException(book_data.isbn)

        self._validate_year(book_data.year)
        self._validate_pages(book_data.pages)

        extra = await self._enrich_book_data(book_data)
        data = Book(
            title=book_data.title,
            author=book_data.author,
            year=book_data.year,
            genre=book_data.genre,
            pages=book_data.pages,
            isbn=book_data.isbn,
            description=book_data.description,
            extra=extra,
        )
        created_book = await self.book_repo.create(data)
        return BookMapper.to_show_book(created_book)

    async def get_book(self, book_id: UUID) -> BookResponse:
        """
        Получить книгу по ID
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)

        return BookMapper.to_show_book(book)

    async def update_book(
        self,
        book_id: UUID,
        book_data: BookUpdate,
    ) -> BookResponse:
        """
        Обновить книгу.

        Обновляются только переданные поля.
        """
        if book_data.year is not None:
            self._validate_year(book_data.year)
        if book_data.pages is not None:
            self._validate_pages(book_data.pages)

        update_payload = book_data.model_dump(exclude_unset=True)
        updated = await self.book_repo.update(book_id, **update_payload)
        if updated is None:
            raise BookNotFoundException(book_id)

        return BookMapper.to_show_book(updated)

    async def delete_book(self, book_id: UUID) -> None:
        """
        Удалить книгу
        """
        deleted = await self.book_repo.delete(book_id)
        if not deleted:
            raise BookNotFoundException(book_id)

    async def search_books(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[BookResponse]:
        """
        Поиск книг с фильтрацией и пагинацией.
        """
        pagination = PaginationParams(page=page, page_size=page_size)
        books = await self.book_repo.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=pagination.limit,
            offset=pagination.offset,
        )
        total = await self.book_repo.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )
        mapped_books = BookMapper.to_show_books(books)

        return PaginatedResponse.create(
            items=mapped_books,
            total=total,
            pagination=pagination,
        )

    def _validate_year(self, year: int) -> None:
        """Проверить что год валиден."""

        current_year = datetime.now().year
        if year < 1000 or year > current_year:
            raise InvalidYearException(year)

    def _validate_pages(self, pages: int) -> None:
        """Проверить что количество страниц валидно."""
        if pages <= 0:
            raise InvalidPagesException(pages)

    async def _enrich_book_data(self, book_data: BookCreate) -> dict[str, Any] | None:
        """
        Обогатить данные книги из Open Library.

        Не выбрасывает исключение если API недоступен.
        """
        try:
            extra = await self.ol_client.enrich(
                title=book_data.title,
                author=book_data.author,
                isbn=book_data.isbn,
            )
            return extra if extra else None
        except OpenLibraryException as e:
            logger.warning(
                "Failed to enrich book data from Open Library: %s",
                e,
                extra={"title": book_data.title, "author": book_data.author},
            )
            return None
