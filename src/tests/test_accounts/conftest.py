from typing import AsyncGenerator, Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.databases.models.base import Base

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[Any]:
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session_factory() as session:
        yield session

    await engine.dispose()
