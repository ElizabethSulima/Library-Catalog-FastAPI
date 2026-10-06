from typing import Annotated, cast

from fastapi import Depends, Request

from app.core.session import AsyncSessionDependency
from app.external.openlibrary.client import OpenLibraryClient
from app.repositories.book import BookRepository
from app.services.book import BookService

# ========== EXTERNAL CLIENTS (Singletons) ==========


def get_openlibrary_client(request: Request) -> OpenLibraryClient:
    """
    Зависимость для получения экземпляра OpenLibraryClient
    """
    return cast(OpenLibraryClient, request.app.state.ol_client)


# ========== REPOSITORIES ==========


async def get_book_repository(
    db: AsyncSessionDependency,
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
    1. get_async_session() создаст AsyncSession
    2. get_book_repository() создаст BookRepository с session
    3. get_openlibrary_client() вернет singleton клиент
    4. Все внедрится в BookService
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
