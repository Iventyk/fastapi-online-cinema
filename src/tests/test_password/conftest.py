from typing import AsyncGenerator, Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from src.databases import get_db
from src.databases.models.base import Base
from src.main import app
from src.config.limiter import limiter

limiter.enabled = False


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


@pytest_asyncio.fixture
async def client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db to return our test session
    async def _get_test_db():
        yield async_session

    app.dependency_overrides[get_db] = _get_test_db

    # Initialize the client with the app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_celery():
    with (
        patch("src.crud.password.send_password_reset_email_task.delay"),
        patch(
            "src.crud.password.send_password_reset_complete_email_task.delay"
        ),
    ):
        yield
