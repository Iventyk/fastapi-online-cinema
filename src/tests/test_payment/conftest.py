import pytest
import asyncio
from asyncio import AbstractEventLoop
from typing import AsyncGenerator, Generator
from decimal import Decimal

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import event
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from src.databases.models import Movie, Certification
from src.databases.models.base import Base
from src.databases.models.accounts import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
)
from src.databases.models.orders import Order, StatusEnum, OrderItem
from src.databases.models.payment import Payment, PaymentStatusEnum
from src.databases import get_db
from src.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create testing engine and initialize schema"""
    engine = create_async_engine(DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record) -> None:
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
    """Async client for requests imitation"""

    app.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> UserModel:
    """Create a test user"""
    group = UserGroupModel(name=UserGroupEnum.USER)
    db_session.add(group)
    await db_session.commit()

    user = UserModel.create(
        email="test_payment_user@example.com",
        raw_password="TestPassword123!",
        group_id=group.id,
    )
    user.is_active = True
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_order(db_session, test_user, test_movie):
    order = Order(user_id=test_user.id, status=StatusEnum.PENDING)
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    item = OrderItem(
        order_id=order.id,
        movie_id=test_movie.id,
        price_at_order=Decimal("50.00"),
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)

    return order


@pytest.fixture
async def test_order_item(
    db_session: AsyncSession, test_order: Order, test_movie: Movie
) -> OrderItem:
    item = OrderItem(
        order_id=test_order.id,
        movie_id=test_movie.id,
        price_at_order=Decimal("10.00"),
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def test_payment(
    db_session: AsyncSession, test_user: UserModel, test_order: Order
) -> Payment:
    """Create a test payment"""
    payment = Payment(
        user_id=test_user.id,
        order_id=test_order.id,
        amount=Decimal("10.00"),
        external_payment_id="pi_test_payment",
        status=PaymentStatusEnum.PENDING,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


@pytest.fixture
async def test_certification(db_session: AsyncSession) -> Certification:
    cert = Certification(name="PG-13")
    db_session.add(cert)
    await db_session.commit()
    await db_session.refresh(cert)
    return cert


@pytest.fixture
async def test_movie(
    db_session: AsyncSession, test_certification: Certification
) -> Movie:
    movie = Movie(
        name="Test Movie",
        year=2000,
        time=120,
        imdb=7.5,
        votes=1000,
        description="Test movie description",
        price=10.0,
        certification_id=test_certification.id,
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)
    return movie
