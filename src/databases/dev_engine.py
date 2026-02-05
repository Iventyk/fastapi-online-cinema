from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.config import get_settings

settings = get_settings()


engine = create_async_engine(
    url=settings.DEV_DATABASE_URL, connect_args={"check_same_thread": False}
)


AsyncSessionLocal = async_sessionmaker(
    autoflush=False, autocommit=False, expire_on_commit=False, bind=engine
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.

    This function returns an async generator yielding a new database session.
    It ensures that the session is properly closed after use.

    :return: An asynchronous generator yielding an AsyncSession instance.
    """

    async with AsyncSessionLocal() as db:
        yield db
