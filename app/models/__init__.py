from typing import TypeVar

from app.models.base import BaseModel

MODEL = TypeVar("MODEL", bound=BaseModel)

TypeModel = type[MODEL]
