from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    """
    Модель пользователя
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(sa.String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(255))
    is_active: Mapped[bool] = mapped_column(server_default=sa.true())
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),  # pylint: disable=E1102
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),  # pylint: disable=E1102
        onupdate=sa.func.now(),  # pylint: disable=E1102
    )

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, username='{self.username}')>"
