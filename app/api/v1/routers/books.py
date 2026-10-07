from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import BookServiceDep
from app.schemas.book import BookCreate, BookFilters, BookResponse, BookUpdate
from app.schemas.pagination import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
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
    Создать новую книгу
    """
    return await service.create_book(book_data)


@router.get(
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
    return await service.search_books(
        title=filters.title,
        author=filters.author,
        genre=filters.genre,
        year=filters.year,
        available=filters.available,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Получить информацию о книге по id",
)
async def get_book(
    book_id: UUID,
    service: BookServiceDep,
) -> BookResponse:
    """
    Получить книгу по ID
    """
    return await service.get_book(book_id)


@router.patch(
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

    Raises:
        404: Книга не найдена
        422: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(
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
