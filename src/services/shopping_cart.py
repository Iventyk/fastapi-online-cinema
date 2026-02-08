from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.databases.models import Cart, CartItem, Order, OrderItem, StatusEnum


async def sync_guest_cart_to_user(
    db: AsyncSession, user_id: int, guest_movie_ids: List[int] | None
) -> None:
    if not guest_movie_ids:
        return

    query = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(selectinload(Cart.items))
    )
    result = await db.execute(query)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        existing_cart_ids = set()
    else:
        existing_cart_ids = {item.movie_id for item in cart.items}

    candidate_ids = set(guest_movie_ids) - existing_cart_ids

    if not candidate_ids:
        return

    purchased_query = (
        select(OrderItem.movie_id)
        .join(Order)
        .where(
            Order.user_id == user_id,
            Order.status.in_([StatusEnum.PAID, StatusEnum.PENDING]),
            OrderItem.movie_id.in_(candidate_ids),
        )
    )
    purchased_result = await db.execute(purchased_query)
    purchased_ids = set(purchased_result.scalars().all())

    final_movies_to_add = candidate_ids - purchased_ids

    for movie_id in final_movies_to_add:
        new_item = CartItem(cart_id=cart.id, movie_id=movie_id)
        db.add(new_item)

    if final_movies_to_add:
        await db.commit()
