import pytest
import decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.accounts import UserModel
from src.databases.models.movies import Movie
from src.databases.models.orders import Order, OrderItem, StatusEnum


def create_dummy_movie(
    certification_id: int, name: str = "Test Movie"
) -> Movie:
    return Movie(
        name=name,
        year=2024,
        time=120,
        imdb=8.5,
        votes=1000,
        description="Test Description",
        certification_id=certification_id,
        price=decimal.Decimal("100.00"),
    )


@pytest.mark.asyncio
async def test_order_relationship_flow(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> None:

    user = UserModel.create(
        email="order_flow@test.com",
        raw_password="Password123!",
        group_id=setup_dependencies["group_id"],
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"])
    db_session.add_all([user, movie])
    await db_session.flush()

    order = Order(
        user_id=user.id, total_amount=movie.price, status=StatusEnum.PENDING
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id, movie_id=movie.id, price_at_order=movie.price
    )
    db_session.add(item)
    await db_session.commit()

    res = await db_session.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .options(
            pytest.importorskip("sqlalchemy.orm").selectinload(Order.items)
        )
    )
    fetched_order = res.scalar_one()

    assert fetched_order.total_amount == decimal.Decimal("100.00")
    assert len(fetched_order.items) == 1
    assert fetched_order.items[0].movie_id == movie.id
    assert fetched_order.status == StatusEnum.PENDING


@pytest.mark.asyncio
async def test_order_cascade_delete(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> None:

    user = UserModel.create(
        email="cascade_test@test.com",
        raw_password="Password123!",
        group_id=setup_dependencies["group_id"],
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"])
    db_session.add_all([user, movie])
    await db_session.flush()

    order = Order(user_id=user.id, total_amount=movie.price)
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id, movie_id=movie.id, price_at_order=movie.price
    )
    db_session.add(item)
    await db_session.commit()

    await db_session.delete(order)
    await db_session.commit()
    db_session.expunge_all()

    item_res = await db_session.execute(
        select(OrderItem).where(OrderItem.id == item.id)
    )
    assert item_res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_order_item_movie_set_null(
    db_session: AsyncSession, setup_dependencies: dict[str, int]
) -> None:

    user = UserModel.create(
        email="setnull_test@test.com",
        raw_password="Password123!",
        group_id=setup_dependencies["group_id"],
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"])
    db_session.add_all([user, movie])
    await db_session.flush()

    order = Order(user_id=user.id, total_amount=movie.price)
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id, movie_id=movie.id, price_at_order=movie.price
    )
    db_session.add(item)
    await db_session.commit()

    item_id = item.id

    await db_session.delete(movie)
    await db_session.commit()
    db_session.expire_all()

    res = await db_session.execute(
        select(OrderItem).where(OrderItem.id == item_id)
    )
    fetched_item = res.scalar_one()
    assert fetched_item.id == item_id
    assert fetched_item.movie_id is None
    assert fetched_item.price_at_order == decimal.Decimal("100.00")
