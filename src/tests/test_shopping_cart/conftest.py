import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from src.databases.models.base import Base
from src.databases.models.accounts import UserGroupModel, UserGroupEnum
from src.databases.models.movies import Certification, Genre


DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def setup_dependencies(db_session):
    """
    Creating important additional data: User groups, Movie certificates.
    """
    group = UserGroupModel(name=UserGroupEnum.USER)
    db_session.add(group)

    cert = Certification(name="PG-13")
    db_session.add(cert)

    genre = Genre(name="Action")
    db_session.add(genre)

    await db_session.commit()

    return {
        "group_id": group.id,
        "certification_id": cert.id,
        "genre_id": genre.id
    }
