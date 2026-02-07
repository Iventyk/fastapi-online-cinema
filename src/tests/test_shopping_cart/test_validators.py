from decimal import Decimal

import pytest

from src.databases.models import OrderItem, Order, StatusEnum
from src.validators import validate_user, validate_user_permission, validate_movie, validate_movie_purchase_status
from src.exceptions import (
    UserNotExist,
    UserPermissionDenied,
    MovieDoesNotExist,
    RepeatPurchaseNotAllowed,
)


@pytest.mark.asyncio
async def test_validate_user_raise_exception(db_session):
    with pytest.raises(UserNotExist):
        await validate_user(
            db=db_session,
            user_id=4,
        )


@pytest.mark.asyncio
async def test_validate_user_success(db_session, test_user):
    assert await validate_user(
            db=db_session,
            user_id=test_user.id
        ) is None


@pytest.mark.asyncio
async def test_validate_user_permission_raise_exception(auth_user_schema):
    with pytest.raises(UserPermissionDenied):
        await validate_user_permission(
            user_id=99,
            authenticated_user=auth_user_schema,
        )


@pytest.mark.asyncio
async def test_validate_user_permission_success(auth_user_schema, auth_moderator_schema):
    assert await validate_user_permission(
            user_id=auth_user_schema.user_id,
            authenticated_user=auth_user_schema,
        ) is None
    assert await validate_user_permission(
            user_id=auth_user_schema.user_id,
            authenticated_user=auth_moderator_schema,
        ) is None


@pytest.mark.asyncio
async def test_validate_movie_raise_exception(db_session):
    with pytest.raises(MovieDoesNotExist):
        await validate_movie(
            db=db_session,
            movie_id=4
        )


@pytest.mark.asyncio
async def test_validate_movie_success(db_session, test_movie):
    assert await validate_movie(
        db=db_session,
        movie_id=test_movie.id
    ) == test_movie


@pytest.mark.asyncio
async def test_validate_movie_purchase_status_raise_exception(db_session, test_user, test_movie):
    order = Order(
        status=StatusEnum.PAID,
        total_amount=Decimal("10.5"),
        user_id=test_user.id,
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.flush()

    order_item = OrderItem(
        price_at_order=Decimal("10.5"),
        order_id=order.id,
        movie_id=test_movie.id
    )
    db_session.add(order_item)
    await db_session.commit()
    await db_session.flush()

    with pytest.raises(RepeatPurchaseNotAllowed):
        await validate_movie_purchase_status(
            db=db_session,
            user_id=test_user.id,
            movie_id=test_movie.id
        )


@pytest.mark.asyncio
async def test_validate_movie_purchase_status_success(db_session, test_user, test_movie):
    assert await validate_movie_purchase_status(
        db=db_session,
        user_id=test_user.id,
        movie_id=test_movie.id
    ) is None
