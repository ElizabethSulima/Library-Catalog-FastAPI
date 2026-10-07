from typing import Any
from uuid import UUID

import fastapi as fa
from starlette.responses import JSONResponse


class AppException(Exception):
    """
    Базовое исключение для всего приложения.
    Все кастомные исключения должны наследоваться от него.
    """

    code: str = "app_exception"

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


class NotFoundException(AppException):
    """
    Базовое исключение для случаев, когда ресурс не найден (404).
    Автоматически формирует сообщение вида: "{resource} with {identifier} not found".
    """

    code = "not_found"

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
    async def app_exception_handler(request: fa.Request, exc: AppException) -> JSONResponse:
        content: dict[str, Any] = {
            "code": exc.code,
            "detail": exc.message,
        }
        if exc.details:
            content["details"] = exc.details

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )
