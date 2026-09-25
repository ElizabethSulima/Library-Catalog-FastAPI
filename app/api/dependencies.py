from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.dependency import AsyncSessionDepency
from app.core.settings import settings
from app.external.openlibrary.client import OpenLibraryClient
from app.repositories.book import BookRepository
from app.services.book import BookService

# ========== EXTERNAL CLIENTS (Singletons) ==========


@lru_cache
def get_openlibrary_client() -> OpenLibraryClient:
    """
    Получить singleton OpenLibraryClient.

    lru_cache создает клиент один раз и переиспользует.
    """
    return OpenLibraryClient(
        base_url=settings.OPENLIBRARY_BASE_URL,
        timeout=settings.OPENLIBRARY_TIMEOUT,
    )


# ========== REPOSITORIES ==========


async def get_book_repository(
    db: AsyncSessionDepency,
) -> BookRepository:
    """
    Создать BookRepository для текущей сессии БД.

    Создается новый экземпляр для каждого запроса.
    """
    return BookRepository(db)


# ========== SERVICES ==========


async def get_book_service(
    book_repo: Annotated[BookRepository, Depends(get_book_repository)],
    ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    Создать BookService с внедренными зависимостями.

    FastAPI автоматически разрешит все зависимости:
    1. get_db() создаст AsyncSession
    2. get_book_repository() создаст BookRepository с session
    3. get_openlibrary_client() вернет singleton клиент
    4. Все внедрится в BookService
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

# Можно использовать в роутерах так:
# async def my_route(service: BookServiceDep):
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
DbSessionDep = AsyncSessionDepency
