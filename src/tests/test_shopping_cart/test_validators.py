from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.databases.models import OrderItem, Order, StatusEnum, UserModel, Movie
from src.schemas import CurrentUser
from src.validators import (
    validate_user,
    validate_user_permission,
    validate_movie,
    validate_movie_purchase_status,
)
from src.exceptions import (
    UserNotExist,
    UserPermissionDenied,
    MovieDoesNotExist,
    RepeatPurchaseNotAllowed,
)


@pytest.mark.asyncio
async def test_validate_user_raise_exception(db_session: AsyncSession) -> None:
    with pytest.raises(UserNotExist):
        await validate_user(
            db=db_session,
            user_id=4,
        )


@pytest.mark.asyncio
async def test_validate_user_success(
    db_session: AsyncSession, test_user: UserModel
) -> None:
    await validate_user(db=db_session, user_id=test_user.id)


@pytest.mark.asyncio
async def test_validate_user_permission_raise_exception(
    auth_user_schema: CurrentUser,
) -> None:
    with pytest.raises(UserPermissionDenied):
        await validate_user_permission(
            user_id=99,
            authenticated_user=auth_user_schema,
        )


@pytest.mark.asyncio
async def test_validate_user_permission_success(
    auth_user_schema: CurrentUser, auth_moderator_schema: CurrentUser
) -> None:
    await validate_user_permission(
        user_id=auth_user_schema.user_id, authenticated_user=auth_user_schema
    )

    await validate_user_permission(
        user_id=auth_user_schema.user_id,
        authenticated_user=auth_moderator_schema,
    )


@pytest.mark.asyncio
async def test_validate_movie_raise_exception(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(MovieDoesNotExist):
        await validate_movie(db=db_session, movie_id=4)


@pytest.mark.asyncio
async def test_validate_movie_success(
    db_session: AsyncSession, test_movie: Movie
) -> None:
    assert (
        await validate_movie(db=db_session, movie_id=test_movie.id)
        == test_movie
    )


@pytest.mark.asyncio
async def test_validate_movie_purchase_status_raise_exception(
    db_session: AsyncSession, test_user: UserModel, test_movie: Movie
) -> None:
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
        movie_id=test_movie.id,
    )
    db_session.add(order_item)
    await db_session.commit()
    await db_session.flush()

    with pytest.raises(RepeatPurchaseNotAllowed):
        await validate_movie_purchase_status(
            db=db_session, user_id=test_user.id, movie_id=test_movie.id
        )


@pytest.mark.asyncio
async def test_validate_movie_purchase_status_success(
    db_session: AsyncSession, test_user: UserModel, test_movie: Movie
) -> None:
    await validate_movie_purchase_status(
        db=db_session, user_id=test_user.id, movie_id=test_movie.id
    )
