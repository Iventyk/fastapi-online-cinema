from typing import Annotated, List

from fastapi import Depends
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.exceptions import (
    CartItemAlreadyExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
    CartAlreadyExist,
)
from src.databases.models import (
    Cart,
    CartItem,
    Movie,
    OrderItem,
    Order,
    StatusEnum,
)
from src.schemas import (
    CartReadSchema,
    CartItemCreateSchema,
    MovieInCartSchema,
    CurrentUser,
)
from src.validators import (
    validate_user,
    validate_user_permission,
    validate_movie,
    validate_movie_purchase_status,
)
from src.security.utils import get_current_user


async def create_new_cart_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    cart_item: CartItemCreateSchema,
) -> MovieInCartSchema:
    await validate_user(db=db, user_id=user_id)
    await validate_user_permission(
        user_id=user_id, authenticated_user=authenticated_user
    )
    movie = await validate_movie(db=db, movie_id=cart_item.movie_id)
    await validate_movie_purchase_status(
        db=db, user_id=user_id, movie_id=cart_item.movie_id
    )

    query = select(Cart).where(Cart.user_id == user_id)
    result = await db.execute(query)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()

    new_cart_item = CartItem(cart_id=cart.id, movie_id=cart_item.movie_id)

    db.add(new_cart_item)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise CartItemAlreadyExist("This movie is already in the cart")

    return MovieInCartSchema.model_validate(movie)


async def remove_cart_item(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    cart_item_id: int,
) -> None:
    await validate_user(db=db, user_id=user_id)
    await validate_user_permission(
        user_id=user_id, authenticated_user=authenticated_user
    )

    query_cart = select(Cart).where(Cart.user_id == user_id)
    result_cart = await db.execute(query_cart)
    cart = result_cart.scalar_one_or_none()

    if not cart:
        raise CartItemDoesNotExist("Cart item does not exist")

    query_item = select(CartItem).where(
        CartItem.id == cart_item_id, CartItem.cart_id == cart.id
    )
    result_item = await db.execute(query_item)
    item = result_item.scalar_one_or_none()

    if not item:
        raise CartItemDoesNotExist("Cart item does not exist")

    await db.delete(item)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise CartItemDoesNotExist("Cart item does not exist")


async def clear_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    await validate_user(db=db, user_id=user_id)
    await validate_user_permission(
        user_id=user_id, authenticated_user=authenticated_user
    )

    query = select(Cart.id).where(Cart.user_id == user_id)
    cart_id = await db.scalar(query)

    if not cart_id:
        raise CartItemsDoesNotExist("Cart is already empty")

    delete_query = delete(CartItem).where(CartItem.cart_id == cart_id)
    result = await db.execute(delete_query)

    if result.rowcount == 0:  # type: ignore
        raise CartItemsDoesNotExist("Cart is already empty")

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise CartItemsDoesNotExist("Cart is already empty")


async def get_cart(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CartReadSchema:
    await validate_user(db=db, user_id=user_id)
    await validate_user_permission(
        user_id=user_id, authenticated_user=authenticated_user
    )

    query = (
        select(Cart)
        .where(Cart.user_id == user_id)
        .options(
            selectinload(Cart.items).options(
                joinedload(CartItem.movie).options(selectinload(Movie.genres))
            )
        )
    )

    result = await db.execute(query)
    cart = result.scalar_one_or_none()

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise CartAlreadyExist("Unexpected database error")
        await db.refresh(cart)
        return CartReadSchema(
            id=cart.id, user_id=cart.user_id, items=[]
        )  # type: ignore[call-arg]

    return CartReadSchema.model_validate(cart)


async def get_purchased_items(
    db: AsyncSession,
    user_id: int,
    authenticated_user: CurrentUser,
) -> List[MovieInCartSchema]:
    await validate_user(db=db, user_id=user_id)
    await validate_user_permission(
        user_id=user_id, authenticated_user=authenticated_user
    )

    query = (
        select(Movie)
        .join(OrderItem, OrderItem.movie_id == Movie.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(
            Order.user_id == user_id,
            Order.status == StatusEnum.PAID,
        )
        .options(selectinload(Movie.genres))
    )

    result = await db.execute(query)

    purchased_movies = result.scalars().all()

    return [
        MovieInCartSchema.model_validate(movie) for movie in purchased_movies
    ]
