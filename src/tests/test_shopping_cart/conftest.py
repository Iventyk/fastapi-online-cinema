import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event

from src.databases.models.base import Base
from src.databases.models.accounts import UserGroupModel, UserGroupEnum, UserModel
from src.databases.models.movies import Certification, Genre, Movie
from src.schemas import CurrentUser

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
    moderator_group = UserGroupModel(name=UserGroupEnum.MODERATOR)
    db_session.add(moderator_group)

    cert = Certification(name="PG-13")
    db_session.add(cert)

    genre = Genre(name="Action")
    db_session.add(genre)

    await db_session.commit()

    return {
        "group_id": group.id,
        "moderator_group_id": moderator_group.id,
        "certification_id": cert.id,
        "genre_id": genre.id
    }

@pytest.fixture
async def test_user(db_session, setup_dependencies):
    """Creating test user in database"""
    user = await UserModel.create(
        email="test_crud@example.com",
        raw_password="SuperStrongPassword2!",
        group_id=setup_dependencies["group_id"],
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_moderator(db_session, setup_dependencies):
    """Creating test moderator in database"""
    user = await UserModel.create(
        email="test_crud_moderator@example.com",
        raw_password="SuperStrongPassword3!",
        group_id=setup_dependencies["moderator_group_id"],
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_movie(db_session, setup_dependencies):
    """Create test movie object in database"""
    movie = Movie(
        name="Test Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=5000,
        description="Sci-fi classic",
        price=15.00,
        certification_id=setup_dependencies["certification_id"]
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie

@pytest.fixture
def auth_user_schema(test_user):
    """
    Authorized user imitation
    """
    return CurrentUser(
        user_id=test_user.id,
        email=str(test_user.email),
        permission="USER",
        is_active=True,
        profile_id=None
    )

@pytest.fixture
def auth_moderator_schema(test_moderator):
    """
    Authorized moderator imitation
    """
    return CurrentUser(
        user_id=test_moderator.id,
        email=str(test_moderator.email),
        permission="MODERATOR",
        is_active=True,
        profile_id=None
    )