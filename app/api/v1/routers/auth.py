from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.core.session import get_async_session
from app.repositories.user import UserRepository
from app.schemas.user import (
    LoginRequest,
    Token,
    TokenRefresh,
    UserCreate,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session),
) -> UserResponse:
    """Зарегистрировать нового пользователя"""
    user_repo = UserRepository(session)
    auth_service = AuthService(user_repo)
    return await auth_service.register(user_data)


@router.post("/login", response_model=Token, summary="Авторизация и получение токенов")
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> Token:
    """Авторизоваться и получить access + refresh токены"""
    user_repo = UserRepository(session)
    auth_service = AuthService(user_repo)
    return await auth_service.login(credentials.username, credentials.password)


@router.post("/refresh", response_model=Token, summary="Обновление access токена")
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    token_data: TokenRefresh,
    session: AsyncSession = Depends(get_async_session),
) -> Token:
    """Обновить access токен используя refresh токен"""
    user_repo = UserRepository(session)
    auth_service = AuthService(user_repo)
    return await auth_service.refresh_token(token_data.refresh_token)
