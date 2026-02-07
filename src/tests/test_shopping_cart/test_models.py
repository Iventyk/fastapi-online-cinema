import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.databases.models.accounts import UserModel
from src.databases.models.movies import Movie
from src.databases.models.shopping_cart import Cart, CartItem


def create_dummy_movie(certification_id: int, name: str = "Test Movie") -> Movie:
    """Helpful function for fast creating valid movie model"""
    return Movie(
        name=name,
        year=2024,
        time=120,
        imdb=8.5,
        votes=1000,
        description="Test Description",
        certification_id=certification_id,
        price=10.00
    )


@pytest.mark.asyncio
async def test_cart_relationship_flow(db_session, setup_dependencies):
    """
    Test relation cycle: User -> Cart -> Items -> Movie
    """
    user = await UserModel.create(
        email="cart_user@test.com",
        raw_password="VeryHardPassword1!",
        group_id=setup_dependencies["group_id"]
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"], "Inception")

    db_session.add(user)
    db_session.add(movie)

    await db_session.flush()

    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(item)
    await db_session.commit()

    result = await db_session.execute(
        select(Cart).where(Cart.user_id == user.id)
    )
    fetched_cart = result.scalar_one()

    items_result = await db_session.execute(
        select(CartItem).where(CartItem.cart_id == fetched_cart.id)
    )
    items = items_result.scalars().all()

    assert fetched_cart.user_id == user.id
    assert len(items) == 1
    assert items[0].movie_id == movie.id


@pytest.mark.asyncio
async def test_cart_item_unique_constraint(db_session, setup_dependencies):
    """
    Checking if one movie can't add twice (IntegrityError).
    """
    user = await UserModel.create(
        email="unique@test.com",
        raw_password="VeryHardPassword1!",
        group_id=setup_dependencies["group_id"]
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"], "Unique Movie")
    db_session.add_all([user, movie])
    await db_session.flush()

    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    item1 = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(item1)
    await db_session.flush()

    item2 = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(item2)

    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_cascade_delete_user_clears_cart(db_session, setup_dependencies):
    """
    Checking cascade='all, delete-orphan' on user deleting.
    Deleting User -> Deleting Cart -> Deleting CartItems.
    """
    user = await UserModel.create(
        email="delete_me@test.com",
        raw_password="VeryHardPassword1!",
        group_id=setup_dependencies["group_id"]
    )
    movie = create_dummy_movie(setup_dependencies["certification_id"])
    db_session.add_all([user, movie])
    await db_session.flush()

    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(item)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()
    db_session.expunge_all()

    cart_res = await db_session.execute(select(Cart).where(Cart.id == cart.id))
    assert cart_res.scalar_one_or_none() is None

    item_res = await db_session.execute(select(CartItem).where(CartItem.id == item.id))
    assert item_res.scalar_one_or_none() is None