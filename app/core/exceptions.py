import logging
from typing import Any
from uuid import UUID

import fastapi as fa
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


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


class AuthenticationException(AppException):
    """Исключение для ошибок аутентификации (401)."""

    code = "authentication_error"

    def __init__(
        self,
        message: str = "Could not validate credentials",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=fa.status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class ForbiddenException(AppException):
    """Исключение для ошибок авторизации / доступа (403)."""

    code = "forbidden"

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=fa.status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ConflictException(AppException):
    """Исключение для конфликтов данных (409)-дубликат email/username."""

    code = "conflict"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=fa.status.HTTP_409_CONFLICT,
            details=details,
        )


class ValidationException(AppException):
    """Исключение для ошибок бизнес-валидации (422)."""

    code = "validation_error"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            status_code=fa.status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


def register_exception_handlers(app: fa.FastAPI) -> None:
    """Зарегистрировать обработчики исключений"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: fa.Request, exc: AppException) -> JSONResponse:
        """Обработчик всех кастомных исключений приложения"""

        content: dict[str, Any] = {
            "code": exc.code,
            "detail": exc.message,
        }
        if exc.details:
            content["details"] = exc.details

        request_id = getattr(request.state, "request_id", None)
        headers: dict[str, str] = {}
        if request_id:
            headers["X-Request-ID"] = request_id
            content["request_id"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(fa.HTTPException)
    async def http_exception_handler(request: fa.Request, exc: fa.HTTPException) -> JSONResponse:
        """Обработчик стандартных HTTPException"""

        content: dict[str, Any] = {
            "code": "http_error",
            "detail": (exc.detail if isinstance(exc.detail, str) else str(exc.detail)),
        }

        headers = dict(exc.headers) if exc.headers else {}
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            headers["X-Request-ID"] = request_id
            content["request_id"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: fa.Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Обработчик ошибок валидации Pydantic"""

        errors: list[dict[str, Any]] = []
        for error in exc.errors():
            errors.append(
                {
                    "field": ".".join(str(loc) for loc in error["loc"] if loc != "body"),
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        content: dict[str, Any] = {
            "code": "validation_error",
            "detail": "Validation failed",
            "errors": errors,
        }

        request_id = getattr(request.state, "request_id", None)
        headers: dict[str, str] = {}
        if request_id:
            headers["X-Request-ID"] = request_id
            content["request_id"] = request_id

        return JSONResponse(
            status_code=fa.status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=content,
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: fa.Request, exc: Exception) -> JSONResponse:
        """
        Глобальный обработчик непредвиденных ошибок
        """

        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(
            "Unhandled exception [%s]: %s",
            request_id,
            exc,
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        content: dict[str, Any] = {
            "code": "internal_error",
            "detail": "An internal error occurred. Please try again later.",
        }

        headers: dict[str, str] = {}
        if request_id != "unknown":
            headers["X-Request-ID"] = request_id
            content["request_id"] = request_id

        return JSONResponse(
            status_code=fa.status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
            headers=headers,
        )
