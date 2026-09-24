from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from core.settings import settings


async def get_async_session() -> AsyncIterator[AsyncSession]:
    # pylint: disable=C0301
    async with AsyncSession(create_async_engine(settings.dsn)) as session:  # type: ignore[arg-type]
        yield session


AsyncSessionDepency = Annotated[
    AsyncSession, Depends(get_async_session, use_cache=True)
]
