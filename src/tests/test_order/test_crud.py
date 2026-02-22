import pytest
from pytest_mock import MockerFixture
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud.orders import (
    create_order,
    get_user_orders,
    cancel_order,
    revalidate_order_prices,
)
from src.databases.models.orders import Order, StatusEnum
from src.databases.models.movies import Movie
from src.databases.models.accounts import UserModel
from src.exceptions import MovieAlreadyPurchased, MovieDoesNotExist
from src.exceptions.orders import (
    OrderNotFound,
    PendingOrderExists,
    OrderAlreadyPaid,
)


@pytest.mark.asyncio
async def test_create_order_success(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    test_movie_2: Movie,
) -> None:
    movie_ids = [test_movie.id, test_movie_2.id]
    result = await create_order(
        db=db_session, user_id=test_user.id, movie_ids=movie_ids
    )

    assert result["message"] == "Success"
    order = result["order"]
    assert order.user_id == test_user.id
    assert order.status == StatusEnum.PENDING

    expected_total = (test_movie.price or 0.0) + (test_movie_2.price or 0.0)
    assert order.total_amount == expected_total
    assert len(order.items) == 2


@pytest.mark.asyncio
async def test_create_order_with_unavailable_movie(
    db_session: AsyncSession,
    test_user: UserModel,
) -> None:
    with pytest.raises(MovieDoesNotExist):
        await create_order(
            db=db_session, user_id=test_user.id, movie_ids=[999, 1000]
        )


@pytest.mark.asyncio
async def test_create_order_partial_exclusion(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
) -> None:
    movie_ids = [test_movie.id, 999]
    result = await create_order(
        db=db_session, user_id=test_user.id, movie_ids=movie_ids
    )

    assert result["order"].total_amount == test_movie.price
    assert 999 in result["removed_unavailable"]
    assert result["message"] == "Some items were excluded..."


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_cancel_order_success(
    db_session: AsyncSession,
    test_user: UserModel,
    test_order: Order,
) -> None:
    await cancel_order(
        db=db_session, order_id=test_order.id, user_id=test_user.id
    )

    res = await db_session.execute(
        select(Order)
        .where(Order.id == test_order.id)
        .options(selectinload(Order.items))
    )
    order_in_db = res.scalar_one()

    assert order_in_db.status == StatusEnum.CANCELLED


@pytest.mark.asyncio
async def test_cancel_order_not_found(
    db_session: AsyncSession,
    test_user: UserModel,
) -> None:
    with pytest.raises(OrderNotFound):
        await cancel_order(db=db_session, order_id=999, user_id=test_user.id)


@pytest.mark.asyncio
async def test_revalidate_order_prices(
    db_session: AsyncSession,
    test_order: Order,
    test_movie: Movie,
) -> None:
    new_price = Decimal("500.00")
    test_movie.price = float(new_price)
    await db_session.commit()

    await db_session.refresh(test_movie)

    updated_order = await revalidate_order_prices(
        db=db_session, order_id=test_order.id
    )

    await db_session.refresh(updated_order, ["items"])

    assert updated_order.items[0].price_at_order == new_price
    assert updated_order.total_amount == new_price


@pytest.mark.asyncio
async def test_get_user_orders(
    db_session: AsyncSession,
    test_user: UserModel,
    test_order: Order,
) -> None:
    orders = await get_user_orders(db=db_session, user_id=test_user.id)
    assert len(orders) >= 1
    assert orders[0].id == test_order.id


@pytest.mark.asyncio
async def test_create_order_already_purchased(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    mocker: MockerFixture,
) -> None:
    movie_id = test_movie.id
    user_id = test_user.id

    mocker.patch(
        "src.crud.orders.get_already_purchased_ids", return_value={movie_id}
    )

    with pytest.raises(MovieAlreadyPurchased):
        await create_order(
            db=db_session, user_id=user_id, movie_ids=[movie_id]
        )


@pytest.mark.asyncio
async def test_create_order_pending_duplicate(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
) -> None:

    await create_order(
        db=db_session, user_id=test_user.id, movie_ids=[test_movie.id]
    )

    with pytest.raises(PendingOrderExists):
        await create_order(
            db=db_session, user_id=test_user.id, movie_ids=[test_movie.id]
        )


@pytest.mark.asyncio
async def test_cancel_already_paid_order(
    db_session: AsyncSession,
    test_user: UserModel,
    test_order: Order,
) -> None:
    test_order.status = StatusEnum.PAID
    await db_session.commit()

    with pytest.raises(OrderAlreadyPaid):
        await cancel_order(
            db=db_session, order_id=test_order.id, user_id=test_user.id
        )
