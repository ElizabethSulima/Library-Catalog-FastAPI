from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Book(BaseModel):
    """Базовая схема книги с обязательными полями"""

    title: str
    author: str
    year: int
    genre: str
    pages: int
    available: bool = True
    isbn: str | None = None
    description: str | None = None
    extra: dict[str, Any] | None = None


class BookResponse(Book):
    """Схема ответа с дополнительными полями из БД"""

    book_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookCreate(BaseModel):
    """Схема создания книги с обязательными полями"""

    title: str
    author: str
    year: int
    genre: str
    pages: int
    available: bool = True
    isbn: str | None = None
    description: str | None = None
    extra: dict[str, Any] | None = None


class BookUpdate(BaseModel):
    """Схема обновления книги с обязательными полями"""

    title: str | None = None
    author: str | None = None
    year: int | None = None
    genre: str | None = None
    pages: int | None = None
    available: bool | None = None
    isbn: str | None = None
    description: str | None = None
    extra: dict[str, Any] | None = None
