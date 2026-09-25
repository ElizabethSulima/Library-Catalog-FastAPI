from app.models.book import Book
from app.schemas.book import BookResponse


class BookMapper:
    """Маппер для преобразования Book entity в DTO."""

    @staticmethod
    def to_show_book(book: Book) -> BookResponse:
        """
        Преобразовать Book ORM модель в ShowBook DTO.

        Args:
            book: ORM модель из БД

        Returns:
            ShowBook: Pydantic модель для API
        """
        return BookResponse(
            book_id=book.book_id,
            title=book.title,
            author=book.author,
            year=book.year,
            genre=book.genre,
            pages=book.pages,
            available=book.available,
            isbn=book.isbn,
            description=book.description,
            extra=book.extra,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )

    @staticmethod
    def to_show_books(books: list[Book]) -> list[BookResponse]:
        """Преобразовать список книг."""
        return [BookMapper.to_show_book(book) for book in books]
