from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.databases.models import Cart, CartItem


async def sync_guest_cart_to_user(
        db: AsyncSession,
        user_id: int,
        guest_movie_ids: List[int]
) -> None:
    if not guest_movie_ids:
        return

    query = select(Cart).where(
        Cart.user_id == user_id
    ).options(
        selectinload(Cart.items)
    )
    result = await db.execute(query)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()
        existing_movie_ids = set()
    else:
        existing_movie_ids = {item.movie_id for item in cart.items}

    movies_to_add = set(guest_movie_ids) - existing_movie_ids

    for movie_id in movies_to_add:
        new_item = CartItem(
            cart_id=cart.id,
            movie_id=movie_id
        )
        db.add(new_item)

    await db.commit()
