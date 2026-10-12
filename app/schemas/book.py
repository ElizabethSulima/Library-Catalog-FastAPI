from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class BookBase(BaseModel):
    """Базовая схема с общими полями и валидацией"""

    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=300)
    year: int = Field(..., ge=1000, le=2100)
    genre: str = Field(..., min_length=1, max_length=100)
    pages: int = Field(..., gt=0)


class BookCreate(BookBase):
    """Схема для создания книги"""

    model_config = ConfigDict(extra="forbid")

    isbn: str | None = Field(None, min_length=10, max_length=20)
    description: str | None = Field(None, max_length=5000)
    extra: dict[str, Any] | None = Field(None, description="Дополнительные метаданные")

    @field_validator("isbn", mode="before")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        """Валидация формата ISBN."""
        if v is None:
            return v

        clean = str(v).replace("-", "").replace(" ", "")

        # Проверка: только цифры (и 'X' для ISBN-10)
        if not clean.replace("X", "").isdigit():
            raise ValueError("ISBN должен содержать только цифры и, возможно, 'X' на конце")

        # Проверка длины
        if len(clean) not in (10, 13):
            raise ValueError("Длина ISBN должна быть 10 или 13 символов")

        return clean.upper()  #'x' в 'X'

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "extra": {
                        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
                        "subjects": [
                            "Computer Science",
                            "Software Engineering",
                        ],
                    },
                }
            ]
        }
    )


class BookUpdate(BaseModel):
    """Схема для обновления книги (все поля опциональны)."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=500)
    author: str | None = Field(None, min_length=1, max_length=300)
    year: int | None = Field(None, ge=1000, le=2100)
    genre: str | None = Field(None, min_length=1, max_length=100)
    pages: int | None = Field(None, gt=0)
    available: bool | None = None
    isbn: str | None = None
    description: str | None = Field(None, max_length=5000)
    extra: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, data: Any) -> Any:
        """
        Запрещаем явную передачу null для любых полей.
        Это гарантирует возврат 422 вместо 500.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    raise ValueError(f"Field '{key}' cannot be explicitly set to null")
        return data


class BookResponse(BookBase):
    """Схема для отображения книги (response)."""

    book_id: UUID
    available: bool
    isbn: str | None
    description: str | None
    extra: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "book_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "available": True,
                    "isbn": "9780132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "extra": {
                        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
                        "subjects": ["Computer Science"],
                    },
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-01T12:00:00Z",
                }
            ]
        },
    )


class BookFilters(BaseModel):
    """Фильтры для поиска книг"""

    title: str | None = Field(
        None,
        max_length=100,
        description="Поиск по названию (частичное совпадение)",
    )
    author: str | None = Field(
        None,
        max_length=100,
        description="Поиск по автору (частичное совпадение)",
    )
    genre: str | None = Field(None, max_length=100, description="Точное совпадение жанра")
    year: int | None = Field(None, ge=1000, le=2100, description="Точное совпадение года")
    available: bool | None = Field(None, description="Фильтр по доступности")
