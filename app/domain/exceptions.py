from datetime import datetime
from uuid import UUID

import fastapi as fa

from app.core.exceptions import AppException, NotFoundException


class BookNotFoundException(NotFoundException):
    """Книга не найдена"""

    code = "book_not_found"

    def __init__(self, book_id: UUID):
        super().__init__(resource="Book", identifier=book_id)


class BookAlreadyExistsException(AppException):
    """Книга с таким ISBN уже существует"""

    code = "book_already_exists"

    def __init__(self, isbn: str):
        super().__init__(
            message=f"Book with ISBN '{isbn}' already exists",
            status_code=fa.status.HTTP_409_CONFLICT,
            details={"isbn": isbn},
        )


class InvalidYearException(AppException):
    """Невалидный год издания"""

    code = "invalid_year"

    def __init__(self, year: int):
        current_year = datetime.now().year
        super().__init__(
            message=f"Year {year} is invalid (must be 1000-{current_year})",
            status_code=fa.status.HTTP_400_BAD_REQUEST,
        )


class InvalidPagesException(AppException):
    """Невалидное количество страниц"""

    code = "invalid_pages"

    def __init__(self, pages: int):
        super().__init__(
            message=f"Pages count must be positive, got {pages}",
            status_code=fa.status.HTTP_400_BAD_REQUEST,
        )


class OpenLibraryException(AppException):
    """Ошибка Open Library API"""

    code = "open_library_error"

    def __init__(
        self,
        message: str,
        status_code: int = fa.status.HTTP_503_SERVICE_UNAVAILABLE,
    ):
        super().__init__(
            message=f"Open Library API error: {message}",
            status_code=status_code,
        )


class OpenLibraryTimeoutException(OpenLibraryException):
    """Таймаут при обращении к Open Library API"""

    code = "open_library_timeout"

    def __init__(self, timeout: float):
        super().__init__(
            message=f"Request timeout after {timeout}s",
            status_code=fa.status.HTTP_504_GATEWAY_TIMEOUT,
        )
