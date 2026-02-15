from datetime import datetime
from decimal import Decimal
from typing import Annotated, List, Optional, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.databases import get_db
from src.databases.models.orders import Order, OrderItem, StatusEnum
from src.databases.models.movies import Movie

from src.databases.models.payment import (
    PaymentItem,
    Payment,
    PaymentStatusEnum,
)
from src.exceptions import MovieAlreadyPurchased, MovieDoesNotExist
from src.exceptions.orders import (
    OrderNotFound,
    OrderCancellationNotPossible,
    PendingOrderExists,
    OrderAlreadyPaid,
)


async def get_already_purchased_ids(
    db: AsyncSession, user_id: int, movie_ids: list[int]
) -> set[int]:
    stmt = (
        select(OrderItem.movie_id)
        .join(PaymentItem, OrderItem.id == PaymentItem.order_item_id)
        .join(Payment, PaymentItem.payment_id == Payment.id)
        .where(
            Payment.user_id == user_id,
            Payment.status == PaymentStatusEnum.SUCCESSFUL,
            OrderItem.movie_id.in_(movie_ids),
        )
    )
    result = await db.execute(stmt)
    return set(result.scalars().all())


async def get_unavailable_movie_ids(
    db: Annotated[AsyncSession, Depends(get_db)], movie_ids: list[int]
) -> set[int]:
    stmt = select(Movie.id).where(Movie.id.in_(movie_ids))
    result = await db.execute(stmt)
    existing_ids = set(result.scalars().all())

    return set(movie_ids) - existing_ids


async def get_movies_prices(
    db: Annotated[AsyncSession, Depends(get_db)], movie_ids: list[int]
) -> dict[int, Decimal]:
    stmt = select(Movie.id, Movie.price).where(Movie.id.in_(movie_ids))
    result = await db.execute(stmt)

    return {row.id: row.price for row in result.all()}


async def check_pending_duplicates(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    movie_ids: List[int],
) -> List[int] | None:
    stmt = (
        select(OrderItem.movie_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.user_id == user_id,
            Order.status == StatusEnum.PENDING,
            OrderItem.movie_id.in_(movie_ids),
        )
    )
    result = await db.execute(stmt)
    existing_pending = result.scalars().all()
    return list(existing_pending)


async def create_order(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    movie_ids: List[int],
) -> dict[str, Any]:
    purchased = await get_already_purchased_ids(db, user_id, movie_ids)
    unavailable = await get_unavailable_movie_ids(db, movie_ids)

    pending_list = await check_pending_duplicates(db, user_id, movie_ids)
    pending = set(pending_list) if pending_list else set()

    to_exclude = purchased.union(unavailable).union(pending)
    valid_ids = [m_id for m_id in movie_ids if m_id not in to_exclude]

    if not valid_ids:
        if purchased:
            raise MovieAlreadyPurchased(
                "All selected movies are already purchased"
            )
        if pending:
            raise PendingOrderExists(
                "You already have pending orders with some movies"
            )
        raise MovieDoesNotExist("None of the selected movies are available")

    prices = await get_movies_prices(db, valid_ids)

    try:
        async with db.begin_nested():
            total_amount = (
                Decimal(sum(prices.values())) if prices else Decimal("0.00")
            )
            new_order = Order(user_id=user_id, total_amount=total_amount)
            db.add(new_order)
            await db.flush()

            for movie_id, price in prices.items():
                item = OrderItem(
                    order_id=new_order.id,
                    movie_id=movie_id,
                    price_at_order=price,
                )
                db.add(item)

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise e

    stmt = (
        select(Order)
        .where(Order.id == new_order.id)
        .options(selectinload(Order.items))
    )

    result = await db.execute(stmt)
    new_order = result.scalar_one()

    return {
        "order": new_order,
        "removed_purchased": list(purchased),
        "removed_unavailable": list(unavailable),
        "removed_pending": list(pending),
        "message": "Some items were excluded..." if to_exclude else "Success",
    }


async def get_user_orders(
    db: Annotated[AsyncSession, Depends(get_db)], user_id: int
) -> List[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
    result = await db.execute(stmt)

    return list(result.scalars().all())


async def get_all_orders_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Optional[int] = None,
    status: Optional[StatusEnum] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Order]:
    stmt = select(Order).options(selectinload(Order.items))

    if user_id:
        stmt = stmt.where(Order.user_id == user_id)
    if status:
        stmt = stmt.where(Order.status == status)
    if date_from:
        stmt = stmt.where(Order.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Order.created_at <= date_to)

    stmt = stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def cancel_order(
    db: Annotated[AsyncSession, Depends(get_db)], order_id: int, user_id: int
) -> Order:
    stmt = (
        select(Order)
        .where(Order.id == order_id, Order.user_id == user_id)
        .options(selectinload(Order.items))
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise OrderNotFound("Order not found")

    if order.status == StatusEnum.CANCELLED:
        raise OrderCancellationNotPossible("Order is already cancelled")

    if order.status == StatusEnum.PAID:
        raise OrderAlreadyPaid(
            "Paid orders can only be cancelled via a refund request"
        )

    if order.status != StatusEnum.PENDING:
        raise OrderCancellationNotPossible("This order cannot be cancelled")

    try:
        order.status = StatusEnum.CANCELLED
        await db.commit()
        await db.refresh(order)
        return order
    except Exception as e:
        await db.rollback()
        raise e


async def revalidate_order_prices(
    db: Annotated[AsyncSession, Depends(get_db)], order_id: int
) -> Order:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise OrderNotFound()

    if order.status != StatusEnum.PENDING:
        return order

    try:
        new_total = Decimal("0.00")

        for item in order.items:
            movie_stmt = select(Movie.price).where(Movie.id == item.movie_id)
            movie_result = await db.execute(movie_stmt)
            current_price = movie_result.scalar_one_or_none()

            if current_price is not None:
                item.price_at_order = Decimal(str(current_price))
                new_total += item.price_at_order

        order.total_amount = new_total

        await db.commit()
        await db.refresh(order)
        return order
    except Exception as e:
        await db.rollback()
        raise e
