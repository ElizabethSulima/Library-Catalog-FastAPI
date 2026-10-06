import asyncio
import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, cast

import httpx


class BaseApiClient(ABC):
    """
    Базовый класс для HTTP клиентов внешних API.

    Включает:
    - Retry логику
    - Обработку ошибок
    - Логирование
    - Timeout management
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        retries: int = 3,
        backoff: float = 0.5,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._client = httpx.AsyncClient(timeout=self.timeout)
        self.logger = logging.getLogger(self.client_name())

    @abstractmethod
    def client_name(self) -> str:
        """Имя клиента для логирования"""

    def _build_url(self, path: str) -> str:
        """Построить полный URL."""
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """
        Выполнить HTTP запрос с retry логикой.

        Raises:
            httpx.TimeoutException: При таймауте
            httpx.HTTPError: При HTTP ошибке
        """
        url = self._build_url(path)

        for attempt in range(self.retries):
            try:
                self.logger.debug("%s %s params=%s", method, url, params)

                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500 and attempt < self.retries - 1:
                    wait_time = self.backoff * (2**attempt)
                    self.logger.warning(
                        "Server error %s, retrying in %ss...",
                        e.response.status_code,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("HTTP error: %s", e)
                    raise

            except httpx.RequestError as e:
                if attempt < self.retries - 1:
                    wait_time = self.backoff * (2**attempt)
                    self.logger.warning(
                        "Request error (%s), retrying in %ss...",
                        type(e).__name__,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("Request failed after %s attempts: %s", self.retries, e)
                    raise

    async def _get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """GET запрос"""
        return cast(dict[str, Any], await self._request("GET", path, **kwargs))

    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        await self._client.aclose()

    async def __aenter__(self) -> "BaseApiClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Асинхронный контекстный менеджер для корректного закрытия"""
        await self.close()
