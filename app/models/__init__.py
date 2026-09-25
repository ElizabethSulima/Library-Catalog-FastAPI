from typing import Type, TypeVar

from app.models.base import Base
from app.models.book import Book

MODEL = TypeVar("MODEL", bound=Base)

TypeModel = Type[MODEL]
