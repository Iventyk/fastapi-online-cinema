from asyncio import AbstractEventLoop
from typing import AsyncGenerator, Generator, Any

import pytest
import asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import event
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from src.databases.models import Cart, CartItem
from src.main import app
from src.databases import get_db
from src.databases.models.base import Base
from src.databases.models.accounts import (
    UserGroupModel,
    UserGroupEnum,
    UserModel,
)
from src.databases.models.movies import Certification, Genre, Movie
from src.schemas import CurrentUser

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create testing engine"""
    engine = create_async_engine(DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(
        dbapi_connection: Any, connection_record: Any
    ) -> None:
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
async def db_session(
    db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create testing database session"""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Async client for requests imitation.
    """

    app.dependency_overrides[get_db] = lambda: db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def cleanup_overrides() -> Generator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def setup_dependencies(db_session: AsyncSession) -> dict[str, int]:
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
        "genre_id": genre.id,
    }


@pytest.fixture
async def test_user(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> UserModel:
    """Creating test user in database"""
    user = UserModel.create(
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
async def test_moderator(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> UserModel:
    """Creating test moderator in database"""
    user = UserModel.create(
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
async def test_movie(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> Movie:
    """Create test movie object in database"""
    movie = Movie(
        name="Test Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=5000,
        description="Sci-fi classic",
        price=15.00,
        certification_id=setup_dependencies["certification_id"],
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


@pytest.fixture
async def test_cart(
    db_session: AsyncSession, test_movie: Movie, test_user: UserModel
) -> Cart:
    """Create test cart object in database"""
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest.fixture
async def test_cart_item(
    db_session: AsyncSession, test_movie: Movie, test_cart: Cart
) -> CartItem:
    """Create test cart item object in database"""
    cart_item = CartItem(cart_id=test_cart.id, movie_id=test_movie.id)
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(cart_item)
    return cart_item


@pytest.fixture
def auth_user_schema(test_user: UserModel) -> CurrentUser:
    """
    Authorized user imitation
    """
    return CurrentUser(
        user_id=test_user.id,
        email=str(test_user.email),
        permission="USER",
        is_active=True,
        profile_id=None,
    )


@pytest.fixture
def auth_moderator_schema(test_moderator: UserModel) -> CurrentUser:
    """
    Authorized moderator imitation
    """
    return CurrentUser(
        user_id=test_moderator.id,
        email=str(test_moderator.email),
        permission="MODERATOR",
        is_active=True,
        profile_id=None,
    )
