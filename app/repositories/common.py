from typing import Any, Generic, Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

import models


class Base(Generic[models.MODEL]):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.model: models.TypeModel

    def _get_pk_column(self):
        """Получить колонку первичного ключа модели."""
        mapper = sa.inspect(self.model)
        return mapper.primary_key[0]

    async def create_item(self, data: dict[str, Any]) -> models.MODEL:
        item = await self.session.scalar(
            sa.insert(self.model).returning(self.model).values(**data)
        )
        return item  # type: ignore[return-value]

    async def get_items(self) -> Sequence[models.MODEL]:
        pk = self._get_pk_column()
        result = await self.session.scalars(
            sa.select(self.model).order_by(pk.desc())
        )
        return result.unique().all()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[models.MODEL]:
        """Получить все записи с пагинацией"""
        pk = self._get_pk_column()
        stmt = (
            sa.select(self.model)
            .order_by(pk.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(stmt)
        return result.unique().all()

    async def get_item_id(self, item_id: int) -> models.MODEL | None:
        pk = self._get_pk_column()
        stmt = sa.select(self.model).where(pk == item_id)
        result = await self.session.scalar(stmt)
        return result

    async def update_item(self, data: dict[str, Any]) -> models.MODEL | None:
        pk = self._get_pk_column()
        item_id = data.pop(pk.name)
        stmt = (
            sa.update(self.model)
            .returning(self.model)
            .where(pk == item_id)
            .values(**data)
        )
        item = await self.session.scalar(stmt)
        await self.session.flush()
        return item

    async def delete_item(self, item_id: int) -> None:
        pk = self._get_pk_column()
        await self.session.execute(sa.delete(self.model).where(pk == item_id))
