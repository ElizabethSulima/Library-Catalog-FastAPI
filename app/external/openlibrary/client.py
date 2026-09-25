import httpx

from app.core.settings import settings
from app.domain.exceptions import (
    OpenLibraryException,
    OpenLibraryTimeoutException,
)
from app.external.base.base_client import BaseApiClient
from app.external.openlibrary.schemas import OpenLibrarySearchResponse


class OpenLibraryClient(BaseApiClient):
    """Клиент для Open Library API."""

    def __init__(
        self,
        base_url: str = settings.OPENLIBRARY_BASE_URL,
        timeout: float = settings.OPENLIBRARY_TIMEOUT,
    ):
        super().__init__(base_url, timeout=timeout)

    def client_name(self) -> str:
        return "openlibrary"

    def _process_search_response(self, data: dict | list | str) -> dict:
        """
        Обработать сырой ответ от /search.json.
        Проверяет тип данных и извлекает первую книгу из массива docs.
        """
        response = OpenLibrarySearchResponse.model_validate(data)
        if not response.docs:
            return {}

        return self._extract_book_data(response.docs[0])

    async def search_by_isbn(self, isbn: str) -> dict:
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
            data = await self._get(
                "/search.json", params={"isbn": isbn, "limit": 1}
            )
            return self._process_search_response(data)

        except httpx.TimeoutException as exc:
            raise OpenLibraryTimeoutException(self.timeout) from exc
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e)) from e

    async def search_by_title_author(self, title: str, author: str) -> dict:
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
    ) -> dict:
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
            except OpenLibraryException:
                pass

        # Попытка 2: По title + author
        return await self.search_by_title_author(title, author)

    def _extract_book_data(self, doc: dict) -> dict:
        """
        Извлечь нужные поля из ответа Open Library.

        Args:
            doc: Документ из массива docs

        Returns:
            dict: Обработанные данные
        """
        result = {}

        # Cover URL
        if cover_id := doc.get("cover_i"):
            result["cover_url"] = self._get_cover_url(cover_id)

        # Subjects (темы)
        subjects = doc.get("subject", [])
        if isinstance(subjects, list):
            result["subjects"] = subjects[:10]
        elif isinstance(subjects, str):
            result["subjects"] = [subjects]

        # Publisher
        publishers = doc.get("publisher")
        if isinstance(publishers, list) and publishers:
            result["publisher"] = publishers[0]
        elif isinstance(publishers, str):
            result["publisher"] = publishers

        # Language
        languages = doc.get("language")
        if isinstance(languages, list) and languages:
            result["language"] = languages[0]
        elif isinstance(languages, str):
            result["language"] = languages

        # Ratings
        if ratings := doc.get("ratings_average"):
            result["rating"] = ratings

        return result

    def _get_cover_url(self, cover_id: int | None) -> str | None:
        """Получить URL обложки"""
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
