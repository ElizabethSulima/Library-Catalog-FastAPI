from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpenLibrarySearchDoc(BaseModel):
    """Документ из поиска Open Library."""

    title: str
    author_name: list[str] | None = None
    cover_i: int | None = None
    subject: list[str] | None = None
    publisher: list[str] | None = None
    language: list[str] | None = None
    ratings_average: float | None = None

    model_config = ConfigDict(populate_by_name=True)

    # Валидатор для защиты от кейсов, когда API возвращает строку вместо списка
    @field_validator(
        "author_name", "subject", "publisher", "language", mode="before"
    )
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class OpenLibrarySearchResponse(BaseModel):
    """Ответ от /search.json"""

    numFound: int
    docs: list[OpenLibrarySearchDoc] = Field(default_factory=list)
