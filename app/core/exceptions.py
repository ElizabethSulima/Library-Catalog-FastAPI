from typing import Any
from uuid import UUID

import fastapi as fa
from fastapi.responses import JSONResponse


class AppException(Exception):
    """
    Базовое исключение для всего приложения.
    Все кастомные исключения должны наследоваться от него.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    @property
    def error_code(self) -> str:
        """
        Автоматически генерирует код ошибки из имени класса.
        Например: BookNotFoundException -> BOOK_NOT_FOUND_EXCEPTION
        """
        name = self.__class__.__name__
        snake = "".join(
            (
                f"_{c}"
                if c.isupper() and i > 0 and not name[i - 1].isupper()
                else c
            )
            for i, c in enumerate(name)
        )
        return snake.upper()


class NotFoundException(AppException):
    """
    Базовое исключение для случаев, когда ресурс не найден (404).
    Автоматически формирует сообщение вида: "{resource} with {identifier} not found".
    """

    def __init__(
        self,
        resource: str,
        identifier: str | int | UUID,
        details: dict[str, Any] | None = None,
    ):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} with identifier '{identifier}' not found"

        if details is None:
            details = {f"{resource.lower()}_id": str(identifier)}

        super().__init__(
            message=message,
            status_code=fa.status.HTTP_404_NOT_FOUND,
            details=details,
        )


def register_exception_handlers(app: fa.FastAPI) -> None:
    """Зарегистрировать обработчики исключений."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: fa.Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
