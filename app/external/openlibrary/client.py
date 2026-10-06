import logging
from typing import Any

import httpx

from app.core.settings import settings
from app.domain.exceptions import (
    OpenLibraryException,
    OpenLibraryTimeoutException,
)
from app.external.base.base_client import BaseApiClient
from app.external.openlibrary.schemas import (
    OpenLibrarySearchDoc,
    OpenLibrarySearchResponse,
)

logger = logging.getLogger(__name__)


class OpenLibraryClient(BaseApiClient):
    """Клиент для Open Library API"""

    def __init__(
        self,
        base_url: str = settings.OPENLIBRARY_BASE_URL,
        timeout: float = settings.OPENLIBRARY_TIMEOUT,
    ):
        super().__init__(base_url, timeout=timeout)

    def client_name(self) -> str:
        return "openlibrary"

    def _process_search_response(self, data: dict[str, Any] | list[Any] | str) -> dict[str, Any]:
        """
        Обработать сырой ответ от /search.json.
        Проверяет тип данных и извлекает первую книгу из массива docs.
        """
        response = OpenLibrarySearchResponse.model_validate(data)
        if not response.docs:
            return {}

        return self._extract_book_data(response.docs[0])

    async def search_by_isbn(self, isbn: str) -> dict[str, Any]:
        """
        Поиск книги по ISBN.

        Args:
            isbn: ISBN-10 или ISBN-13

        Returns:
            dict: Данные книги (cover_url, subjects, etc.)

        Raises:
            OpenLibraryException: При ошибке API
        """
        try:
            data = await self._get("/search.json", params={"isbn": isbn, "limit": 1})
            return self._process_search_response(data)

        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e)) from e

    async def search_by_title_author(self, title: str, author: str) -> dict[str, Any]:
        """Поиск по названию и автору"""
        try:
            data = await self._get(
                "/search.json",
                params={"title": title, "author": author, "limit": 1},
            )
            return self._process_search_response(data)

        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e)) from e

    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> dict[str, Any]:
        """
        Обогатить данные книги.

        Сначала пытается найти по ISBN, затем по title+author.

        Returns:
            dict: Обогащенные данные или пустой словарь
        """
        # Попытка 1: По ISBN
        if isbn:
            try:
                data = await self.search_by_isbn(isbn)
                if data:
                    return data
            except OpenLibraryException as exc:
                logger.warning(
                    "Open Library enrich by ISBN failed: %s. Falling back to title/author.",
                    exc.message,
                    extra={"isbn": isbn},
                )
        # Попытка 2: По title + author
        try:
            return await self.search_by_title_author(title, author)
        except OpenLibraryException as exc:
            logger.warning(
                "Open Library enrich by title/author failed: %s.",
                exc.message,
                extra={"title": title, "author": author},
            )
            return {}

    def _extract_book_data(self, doc: OpenLibrarySearchDoc) -> dict[str, Any]:
        """
        Извлечь нужные поля из ответа Open Library.

        Args:
            doc: Документ из массива docs

        Returns:
            dict: Обработанные данные
        """
        result: dict[str, Any] = {}
        if doc.cover_i:
            result["cover_url"] = self._get_cover_url(doc.cover_i)

        if doc.subject:
            result["subjects"] = doc.subject[:10]

        if doc.publisher:
            result["publisher"] = doc.publisher[0]

        if doc.language:
            result["language"] = doc.language[0]

        if doc.ratings_average:
            result["rating"] = doc.ratings_average

        return result

    def _get_cover_url(self, cover_id: int | None) -> str | None:
        """Получить URL обложки"""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
