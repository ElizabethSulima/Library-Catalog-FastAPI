from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import BookServiceDep
from app.schemas.book import BookCreate, BookFilters, BookResponse, BookUpdate
from app.schemas.paginations import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
)
async def create_book(
    book_data: BookCreate,
    service: BookServiceDep,
):
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


@router.get(
    "/",
    response_model=PaginatedResponse[BookResponse],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
)
async def get_books(
    service: BookServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[BookFilters, Depends()],
):
    """
    Получить список книг с фильтрацией.

    Поддерживаемые фильтры:
    - title: частичное совпадение (регистронезависимо)
    - author: частичное совпадение (регистронезависимо)
    - genre: точное совпадение
    - year: точное совпадение
    - available: True/False

    Пагинация:
    - page: номер страницы (начиная с 1)
    - page_size: размер страницы (1-100, по умолчанию 20)
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


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID",
)
async def get_book(
    book_id: UUID,
    service: BookServiceDep,
):
    """
    Получить книгу по ID.

    Returns:
        ShowBook: Полная информация о книге

    Raises:
        404: Книга не найдена
    """
    return await service.get_book(book_id)


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
)
async def update_book(
    book_id: UUID,
    book_data: BookUpdate,
    service: BookServiceDep,
):
    """
    Обновить книгу.

    Передаются только те поля, которые нужно изменить.
    Остальные поля остаются без изменений.

    Returns:
        ShowBook: Обновленная книга

    Raises:
        404: Книга не найдена
        400: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
)
async def delete_book(
    book_id: UUID,
    service: BookServiceDep,
):
    """
    Удалить книгу.

    Raises:
        404: Книга не найдена
    """
    await service.delete_book(book_id)
