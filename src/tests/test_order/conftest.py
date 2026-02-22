import asyncio
import decimal
import uuid
from decimal import Decimal
from typing import AsyncGenerator, Generator, Any

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main import app
from src.databases import get_db
from src.databases.models.base import Base
from src.databases.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
)
from src.databases.models.movies import Movie, Certification
from src.databases.models.orders import Order, OrderItem
from src.schemas import CurrentUser
from src.security.utils import get_current_user

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(
        dbapi_connection: Any, connection_record: Any
    ) -> None:
        """Create testing engine"""
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
    """Async client for requests imitation."""
    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def setup_dependencies(db_session: AsyncSession) -> dict[str, int]:
    """
    Creating important additional data: User groups, Movie certificates.
    """
    group = UserGroupModel(name=UserGroupEnum.USER)
    db_session.add(group)

    cert = Certification(name="PG-13")
    db_session.add(cert)

    await db_session.commit()
    return {"group_id": group.id, "certification_id": cert.id}


@pytest.fixture
async def test_user(
    db_session: AsyncSession, setup_dependencies: dict
) -> UserModel:
    """Creating test user in database"""
    user = UserModel.create(
        email="tester@example.com",
        raw_password="Password123!",
        group_id=setup_dependencies["group_id"],
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_movie(
    db_session: AsyncSession, setup_dependencies: dict
) -> Movie:
    """Create test movie object in database"""
    movie = Movie(
        uuid=uuid.uuid4(),
        name="The Matrix",
        year=1999,
        time=136,
        imdb=8.7,
        votes=1000,
        description="Wake up, Neo.",
        price=decimal.Decimal("150.00"),
        certification_id=setup_dependencies["certification_id"],
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


@pytest.fixture
async def test_movie_2(
    db_session: AsyncSession, setup_dependencies: dict
) -> Movie:
    """Create one more test movie object in database"""
    movie = Movie(
        uuid=uuid.uuid4(),
        name="Inception",
        year=2010,
        time=148,
        imdb=8.8,
        votes=2000,
        description="Dream within a dream.",
        price=decimal.Decimal("200.00"),
        certification_id=setup_dependencies["certification_id"],
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie


@pytest.fixture
async def test_order(
    db_session: AsyncSession, test_user: UserModel, test_movie: Movie
) -> Order:
    """Create test order object in database"""
    order = Order(user_id=test_user.id, total_amount=test_movie.price)
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        movie_id=test_movie.id,
        price_at_order=test_movie.price,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(order)
    return order


@pytest.fixture
async def test_order_item(
    db_session: AsyncSession, test_order: Order, test_movie: Movie
) -> OrderItem:
    """Create test order item object in database"""
    order_item = OrderItem(
        order_id=test_order.id,
        movie_id=test_movie.id,
        price_at_order=test_movie.price,
    )
    # test_order.total_amount += test_movie.price
    test_order.total_amount += Decimal(str(test_movie.price or 0.0))

    # total = Decimal(str(price1)) + Decimal(str(price2 or 0.0))

    db_session.add(order_item)
    await db_session.commit()
    await db_session.refresh(order_item)
    return order_item


@pytest.fixture
def auth_user_schema(test_user: UserModel) -> CurrentUser:
    """Authorized user imitation"""
    return CurrentUser(
        user_id=test_user.id,
        email=str(test_user.email),
        permission="USER",
        is_active=True,
        profile_id=None,
    )


@pytest.fixture(autouse=True)
def mock_auth(auth_user_schema):
    """Automatically replacing the user for each test in this package"""
    app.dependency_overrides[get_current_user] = lambda: auth_user_schema
    yield
    app.dependency_overrides.pop(get_current_user, None)
