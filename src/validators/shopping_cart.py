from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.schemas import CurrentUser
from src.securuty import get_current_user
from src.databases.models import (
    UserModel,
    UserGroupEnum,
    Movie,
    StatusEnum,
    Order,
    OrderItem,
)
from src.exceptions import (
    UserNotExist,
    UserPermissionDenied,
    MovieDoesNotExist,
    RepeatPurchaseNotAllowed,
)


async def validate_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
) -> None:
    user = await db.get(UserModel, user_id)
    if not user:
        raise UserNotExist(
            message="User which cart you're trying extend does not exist"
        )


async def validate_user_permission(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    groups = UserGroupEnum
    has_permission = (
        authenticated_user.permission == groups.MODERATOR.name
        or authenticated_user.permission == groups.ADMIN.name
    )  # noqa
    if authenticated_user.user_id != user_id and not has_permission:
        raise UserPermissionDenied("Not enough permission")


async def validate_movie(db: AsyncSession, movie_id: int) -> Movie:
    movie_query = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(selectinload(Movie.genres))
    )
    movie_result = await db.execute(movie_query)
    movie = movie_result.scalar_one_or_none()

    if not movie:
        raise MovieDoesNotExist("Movie not found")
    return movie


async def validate_movie_purchase_status(
    db: AsyncSession, user_id: int, movie_id: int
) -> None:
    query = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == user_id,
            OrderItem.movie_id == movie_id,
            Order.status.in_([StatusEnum.PAID, StatusEnum.PENDING]),
        )
    )

    result = await db.execute(query)
    existing_item = result.scalar_one_or_none()

    if existing_item:
        raise RepeatPurchaseNotAllowed(
            "You have already purchased this movie or currently have a pending order for it."  # noqa
        )
