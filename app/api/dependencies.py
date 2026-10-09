from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.session import AsyncSessionDependency, get_async_session
from app.external.openlibrary.client import OpenLibraryClient
from app.models.user import User
from app.repositories.book import BookRepository
from app.services.book import BookService

security = HTTPBearer()

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
    """
    return BookRepository(db)


# ========== SERVICES ==========


async def get_book_service(
    book_repo: Annotated[BookRepository, Depends(get_book_repository)],
    ol_client: Annotated[OpenLibraryClient, Depends(get_openlibrary_client)],
) -> BookService:
    """
    Создать BookService с внедренными зависимостями.
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


# ========== AUTHENTIFICATION ===========


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """Получить текущего пользователя из токена"""
    token = credentials.credentials

    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        stmt = select(User).where(User.user_id == int(user_id))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
