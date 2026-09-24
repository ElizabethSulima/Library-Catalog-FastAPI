from typing import Type, TypeVar

from models.base import Base
from models.book import Book

MODEL = TypeVar("MODEL", bound=Base)

TypeModel = Type[MODEL]
