from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Схема для создания пользователя"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Схема отображения информации по пользователю"""

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: str


class Token(BaseModel):
    """Схема токена"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Схема для refresh токена"""

    refresh_token: str


class LoginRequest(BaseModel):
    """Схема для авторизации"""

    username: str
    password: str
