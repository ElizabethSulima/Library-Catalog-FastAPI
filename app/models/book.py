import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Book(Base):
    """
    Модель книги в каталоге библиотеки.

    Представляет собой основную сущность для хранения информации о книгах.
    Поддерживает автоматическое отслеживание времени создания и обновления записи.

    Attributes:
        book_id(uuid.UUID): Уникальный идентификатор книги(Primary Key,автоматически).
        title(str): Название книги(максимум 500 символов, индексируется).
        author(str): Автор книги. Обязательно, максимум 300 символов. Индексируется.
        year(int): Год издания книги. Обязательно. Индексируется.
        genre(str): Жанр книги. Обязательно, максимум 100 символов. Индексируется.
        pages(int): Количество страниц в книге. Обязательно.
        available(bool): Флаг наличия книги в библиотеке. По умолчанию True. Индексируется.
        isbn(str | None): Уникальный международный стандартный книжный номер.
        description(str | None): Подробное описание книги.
        extra(dict | None): Дополнительные произвольные данные в формате JSONB.
        created_at(datetime): Дата и время создания записи(автоматически).
        updated_at(datetime): Дата и время последнего изменения записи(автоматически).
    """

    __tablename__ = "books"
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        sa.String(length=500),
        nullable=False,
        index=True,
    )
    author: Mapped[str] = mapped_column(sa.String(length=300), index=True)
    year: Mapped[int] = mapped_column(index=True)
    genre: Mapped[str] = mapped_column(sa.String(length=100), index=True)
    pages: Mapped[int]
    available: Mapped[bool] = mapped_column(
        server_default=sa.true(), index=True
    )

    isbn: Mapped[str | None] = mapped_column(sa.String(length=20), unique=True)
    description: Mapped[str | None] = mapped_column(sa.Text)
    extra: Mapped[dict | None] = mapped_column(JSONB)

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
        return f"<Book(id={self.book_id}, title='{self.title}')>"
