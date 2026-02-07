from decimal import Decimal
from unittest.mock import AsyncMock
from pytest_mock import MockerFixture

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.crud.shopping_cart import (
    create_new_cart_item,
    get_cart,
    remove_cart_item,
    clear_cart,
    get_purchased_items,
)
from src.databases.models import Order, StatusEnum, OrderItem, UserModel, Movie
from src.schemas import CartItemCreateSchema, CurrentUser
from src.databases.models.shopping_cart import Cart, CartItem
from src.exceptions import (
    CartItemAlreadyExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
)

CRUD_MODULE = "src.crud.shopping_cart"


@pytest.fixture
def mock_validators(mocker: MockerFixture) -> None:
    mocker.patch(
        f"{CRUD_MODULE}.validate_user",
        new_callable=AsyncMock,
        return_value=None,
    )
    mocker.patch(
        f"{CRUD_MODULE}.validate_user_permission",
        new_callable=AsyncMock,
        return_value=None,
    )
    mocker.patch(
        f"{CRUD_MODULE}.validate_movie_purchase_status",
        new_callable=AsyncMock,
        return_value=None,
    )


@pytest.mark.asyncio
async def test_add_item_to_cart_success(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mocker: MockerFixture,
    mock_validators: MockerFixture,
) -> None:
    mocker.patch(
        f"{CRUD_MODULE}.validate_movie",
        new_callable=AsyncMock,
        return_value=test_movie,
    )

    cart_item_schema = CartItemCreateSchema(movie_id=test_movie.id)

    result = await create_new_cart_item(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
        cart_item=cart_item_schema,
    )

    assert result.title == test_movie.name

    query = select(Cart).where(Cart.user_id == test_user.id)
    cart_res = await db_session.execute(query)
    cart = cart_res.scalar_one()

    item_query = select(CartItem).where(CartItem.cart_id == cart.id)
    item_res = await db_session.execute(item_query)
    items = item_res.scalars().all()

    assert len(items) == 1
    assert items[0].movie_id == test_movie.id


@pytest.mark.asyncio
async def test_add_duplicate_item_raises_error(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mocker: MockerFixture,
    mock_validators: MockerFixture,
) -> None:
    mocker.patch(
        f"{CRUD_MODULE}.validate_movie",
        new_callable=AsyncMock,
        return_value=test_movie,
    )
    cart_item_schema = CartItemCreateSchema(movie_id=test_movie.id)

    await create_new_cart_item(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
        cart_item=cart_item_schema,
    )

    with pytest.raises(CartItemAlreadyExist):
        await create_new_cart_item(
            db=db_session,
            user_id=test_user.id,
            authenticated_user=auth_user_schema,
            cart_item=cart_item_schema,
        )


@pytest.mark.asyncio
async def test_get_cart_creates_empty_if_not_exists(
    db_session: AsyncSession,
    test_user: UserModel,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:

    initial_cart = await db_session.execute(
        select(Cart).where(Cart.user_id == test_user.id)
    )
    assert initial_cart.scalar_one_or_none() is None

    cart_schema = await get_cart(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
    )

    assert cart_schema.items == []

    final_cart = await db_session.execute(
        select(Cart).where(Cart.user_id == test_user.id)
    )
    assert final_cart.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_remove_cart_item(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()

    item = CartItem(cart_id=cart.id, movie_id=test_movie.id)
    db_session.add(item)
    await db_session.commit()

    await remove_cart_item(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
        cart_item_id=item.id,
    )

    db_session.expire_all()
    res = await db_session.execute(
        select(CartItem).where(CartItem.id == item.id)
    )
    assert res.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_remove_not_existing_cart_item(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()

    with pytest.raises(CartItemDoesNotExist):
        await remove_cart_item(
            db=db_session,
            user_id=test_user.id,
            authenticated_user=auth_user_schema,
            cart_item_id=1,
        )


@pytest.mark.asyncio
async def test_clear_cart(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()
    item = CartItem(cart_id=cart.id, movie_id=test_movie.id)
    db_session.add(item)
    await db_session.commit()

    cart_id = cart.id

    await clear_cart(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
    )

    db_session.expire_all()

    cart_res = await db_session.execute(select(Cart).where(Cart.id == cart_id))
    assert cart_res.scalar_one_or_none() is not None

    items_res = await db_session.execute(
        select(CartItem).where(CartItem.cart_id == cart_id)
    )
    assert len(items_res.scalars().all()) == 0


@pytest.mark.asyncio
async def test_clear_empty_cart(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:
    cart = Cart(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()

    with pytest.raises(CartItemsDoesNotExist):
        await clear_cart(
            db=db_session,
            user_id=test_user.id,
            authenticated_user=auth_user_schema,
        )


@pytest.mark.asyncio
async def test_get_purchased_items(
    db_session: AsyncSession,
    test_user: UserModel,
    test_movie: Movie,
    auth_user_schema: CurrentUser,
    mock_validators: MockerFixture,
) -> None:
    purchased_items_empty = await get_purchased_items(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
    )
    assert purchased_items_empty == []

    order = Order(
        user_id=test_user.id,
        status=StatusEnum.PAID,
        total_amount=test_movie.price,
    )
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(
        order_id=order.id,
        movie_id=test_movie.id,
        price_at_order=Decimal(str(test_movie.price)),
    )
    db_session.add(order_item)
    await db_session.commit()

    purchased_items = await get_purchased_items(
        db=db_session,
        user_id=test_user.id,
        authenticated_user=auth_user_schema,
    )

    assert len(purchased_items) == 1
    assert purchased_items[0].title == test_movie.name
