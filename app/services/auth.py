from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    ForbiddenException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import Token, UserCreate, UserResponse


class AuthService:
    """
    Сервис для работы авторизации
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_data: UserCreate) -> UserResponse:
        """Регистрация нового пользователя"""
        existing_user = await self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ConflictException(
                message="Username already registered",
                details={"field": "username"},
            )

        existing_email = await self.user_repo.get_by_email(user_data.email)
        if existing_email:
            raise ConflictException(
                message="Username already registered",
                details={"field": "username"},
            )

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
        )

        created_user = await self.user_repo.create(user)
        return UserResponse.model_validate(created_user)

    async def login(self, username: str, password: str) -> Token:
        """Авторизация и выдача токенов"""
        user = await self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationException(message="User not found")

        if not user.is_active:
            raise ForbiddenException(message="Inactive user")

        access_token = create_access_token(data={"sub": str(user.user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user.user_id)})

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> Token:
        """Обновление access токена"""

        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise AuthenticationException(message="User not found")

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationException(message="User not found")

            new_access_token = create_access_token(data={"sub": user_id})
            new_refresh_token = create_refresh_token(data={"sub": user_id})

            return Token(access_token=new_access_token, refresh_token=new_refresh_token)

        except Exception:
            raise AuthenticationException(message="User not found") from None
