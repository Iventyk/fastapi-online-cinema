import pytest
from sqlalchemy import select
from src.databases.models import CartItem, Cart
from src.services import sync_guest_cart_to_user


@pytest.mark.asyncio
async def test_sync_guest_cart_to_user(db_session, test_user, test_movie):
    await sync_guest_cart_to_user(
        db=db_session,
        user_id=test_user.id,
        guest_movie_ids=[test_movie.id]
    )

    query = (
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == test_user.id)
    )
    result = await db_session.execute(query)
    items = result.scalars().all()

    assert len(items) == 1
    assert items[0].movie_id == test_movie.id
