from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import BookServiceDep
from app.schemas.book import BookCreate, BookFilters, BookResponse, BookUpdate
from app.schemas.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(  # type: ignore[misc]
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
)
async def create_book(
    book_data: BookCreate,
    service: BookServiceDep,
) -> BookResponse:
    """
    Создать новую книгу.

    Автоматически обогащает данные из Open Library API:
    - Обложка книги
    - Темы/subjects
    - Издатель
    - Рейтинг

    Если Open Library недоступен, книга все равно будет создана.
    """
    return await service.create_book(book_data)


@router.get(  # type: ignore[misc]
    "/",
    response_model=PaginatedResponse[BookResponse],
    summary="Получить список книг",
)
async def get_books(
    service: BookServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[BookFilters, Depends()],
) -> PaginatedResponse[BookResponse]:
    """
    Получить список книг с фильтрацией
    """
    books, total = await service.search_books(
        title=filters.title,
        author=filters.author,
        genre=filters.genre,
        year=filters.year,
        available=filters.available,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return PaginatedResponse.create(books, total, pagination)


@router.get(  # type: ignore[misc]
    "/{book_id}",
    response_model=BookResponse,
    summary="Получить информацию о книге по id",
)
async def get_book(
    book_id: UUID,
    service: BookServiceDep,
) -> BookResponse:
    """
    Получить книгу по ID.

    Returns:
        BookResponse: Полная информация о книге

    Raises:
        404: Книга не найдена
    """
    return await service.get_book(book_id)


@router.patch(  # type: ignore[misc]
    "/{book_id}",
    response_model=BookResponse,
    summary="Обновить книгу",
)
async def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    service: BookServiceDep,
) -> BookResponse:
    """
    Обновить книгу.

    Передаются только те поля, которые нужно изменить.
    Остальные поля остаются без изменений.

    Returns:
        BookResponse: Обновленная книга

    Raises:
        404: Книга не найдена
        422: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(  # type: ignore[misc]
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
)
async def delete_book(
    book_id: UUID,
    service: BookServiceDep,
) -> None:
    """
    Удалить книгу.

    Raises:
        404: Книга не найдена
    """
    await service.delete_book(book_id)
