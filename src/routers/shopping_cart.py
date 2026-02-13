from typing import Annotated, List

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.crud import (
    create_new_cart_item,
    remove_cart_item,
    get_cart,
    clear_cart,
    get_purchased_items,
)
from src.exceptions import (
    UserNotExist,
    UserPermissionDenied,
    CartItemAlreadyExist,
    MovieDoesNotExist,
    CartItemDoesNotExist,
    CartItemsDoesNotExist,
    RepeatPurchaseNotAllowed,
)
from src.schemas import (
    MovieInCartSchema,
    CartItemCreateSchema,
    CartReadSchema,
    CurrentUser,
)
from src.security.utils import get_current_user

shopping_cart_router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@shopping_cart_router.post(
    "/{user_id}/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieInCartSchema,
    summary="Add a movie to the shopping cart",
    description="""
    Adds a specific movie to the user's shopping cart based on the provided `movie_id`. 

    **Validation Rules:**
    - The **User** must exist.
    - The **Movie** must exist in the database.
    - The item must **not already be in the cart**.
    - The user must **not have already purchased** this movie (Status: PAID or PENDING).

    **Permissions:**
    - Users can only add items to their **own** cart.
    - **Moderators** and **Admins** can add items to any user's cart.
    """,  # noqa: 80
    responses={
        400: {
            "description": "Business logic validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_exist": {
                            "summary": "user not found",
                            "value": {"detail": "User not found."},
                        },
                        "movie_not_found": {
                            "summary": "Movie not found",
                            "value": {"detail": "Movie not found"},
                        },
                        "already_exists": {
                            "summary": "Item already in cart",
                            "value": {"detail": "Cart item already exists"},
                        },
                        "repeat_purchase": {
                            "summary": "Already purchased",
                            "value": {"detail": "Repeat purchase not allowed"},
                        },
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permission."}
                }
            },
        },
    },
)
async def create_cart_item(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cart_item: CartItemCreateSchema,
) -> MovieInCartSchema:
    """
    Controller for adding a movie to the cart.

    Arguments:
        user_id (int): The ID of the target user owner of the cart.
        authenticated_user (CurrentUser): The user performing the request (from JWT). # noqa: 80
        db (AsyncSession): Database session.
        cart_item (CartItemCreateSchema): Payload containing the `movie_id`.
    """
    try:
        return await create_new_cart_item(
            db=db,
            user_id=user_id,
            authenticated_user=authenticated_user,
            cart_item=cart_item,
        )
    except (
        UserNotExist,
        CartItemAlreadyExist,
        MovieDoesNotExist,
        RepeatPurchaseNotAllowed,
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except (UserPermissionDenied,) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )


@shopping_cart_router.delete(
    "/{user_id}/clean/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Shopping cart cleaner",
    description="""
    Clears the user's shopping cart.

    **Validation Rules:**
    - The **User** must exist.
    - The **cart_item** must exist in the database.

    **Permissions:**
    - Users can only clear their **own** cart.
    - **Moderators** and **Admins** can clear any user's cart.
    """,
    responses={
        400: {
            "description": "Business logic validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_exist": {
                            "summary": "user not found",
                            "value": {"detail": "User not found."},
                        },
                        "cart_items_does_not_exist": {
                            "summary": "cart already empty",
                            "value": {"detail": "Cart is already empty"},
                        },
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permission."}
                }
            },
        },
    },
)
async def delete_cart_items(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Controller for clearing users cart.

    Arguments:
        user_id (int): The ID of the target user owner of the cart.
        authenticated_user (CurrentUser): The user performing the request (from JWT). # noqa: 80
        db (AsyncSession): Database session.
    """
    try:
        await clear_cart(
            db=db,
            user_id=user_id,
            authenticated_user=authenticated_user,
        )
    except (UserNotExist,) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except (UserPermissionDenied,) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )
    except (CartItemsDoesNotExist,):
        return


@shopping_cart_router.delete(
    "/{user_id}/{cart_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove movie from the shopping cart",
    description="""
    Remove a specific movie from the user's shopping cart based on the provided `cart_item_id`.

    **Validation Rules:**
    - The **User** must exist.
    - The **cart_item** must exist in the database.

    **Permissions:**
    - Users can only remove items from their **own** cart.
    - **Moderators** and **Admins** can remove items from any user's cart.
    """,  # noqa: 80
    responses={
        400: {
            "description": "Business logic validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_exist": {
                            "summary": "user not found",
                            "value": {"detail": "User not found."},
                        },
                        "cart_item_does_not_exist": {
                            "summary": "cart item not found",
                            "value": {"detail": "Cart item does not exist"},
                        },
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permission."}
                }
            },
        },
    },
)
async def delete_cart_item(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cart_item_id: int,
) -> None:
    """
    Controller for removing a movie from the cart.

    Arguments:
        user_id (int): The ID of the target user owner of the cart.
        authenticated_user (CurrentUser): The user performing the request (from JWT). # noqa: 80
        db (AsyncSession): Database session.
        cart_item_id (int): The ID of the target cart item.
    """
    try:
        await remove_cart_item(
            db=db,
            user_id=user_id,
            authenticated_user=authenticated_user,
            cart_item_id=cart_item_id,
        )

    except (UserNotExist, CartItemDoesNotExist) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except (UserPermissionDenied,) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )


@shopping_cart_router.get(
    "/{user_id}/",
    status_code=status.HTTP_200_OK,
    response_model=CartReadSchema,
    summary="Shows all movies in cart",
    description="""
    Shows movies in user's shopping cart.

    **Validation Rules:**
    - The **User** must exist.

    **Permissions:**
    - Users can only read their **own** cart.
    - **Moderators** and **Admins** can read any user's cart.
    """,
    responses={
        400: {
            "description": "Business logic validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_exist": {
                            "summary": "user not found",
                            "value": {"detail": "User not found"},
                        },
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permission."}
                }
            },
        },
    },
)
async def get_cart_items(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartReadSchema:
    """
    Controller for reading users cart.

    Arguments:
        user_id (int): The ID of the target user owner of the cart.
        authenticated_user (CurrentUser): The user performing the request (from JWT). # noqa: 80
        db (AsyncSession): Database session.
    """
    try:
        return await get_cart(
            db=db,
            user_id=user_id,
            authenticated_user=authenticated_user,
        )
    except (UserNotExist,) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except (UserPermissionDenied,) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )


@shopping_cart_router.get(
    "/{user_id}/purchased/",
    status_code=status.HTTP_200_OK,
    response_model=List[MovieInCartSchema],
    summary="Shows all purchased items",
    description="""
    Shows users purchased movies.

    **Validation Rules:**
    - The **User** must exist.

    **Permissions:**
    - Users can only read their **own** purchased.
    - **Moderators** and **Admins** can read any user's purchased.
    """,
    responses={
        400: {
            "description": "Business logic validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "user_not_exist": {
                            "summary": "user not found",
                            "value": {"detail": "User not found"},
                        },
                    }
                }
            },
        },
        403: {
            "description": "Permission denied",
            "content": {
                "application/json": {
                    "example": {"detail": "Not enough permission."}
                }
            },
        },
    },
)
async def get_purchased_cart(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[MovieInCartSchema]:
    """
    Controller for reading users purchased movies.

    Arguments:
        user_id (int): The ID of the target user owner of the cart.
        authenticated_user (CurrentUser): The user performing the request (from JWT). # noqa: 80
        db (AsyncSession): Database session.
    """
    try:
        return await get_purchased_items(
            db=db,
            user_id=user_id,
            authenticated_user=authenticated_user,
        )
    except (UserNotExist,) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except (UserPermissionDenied,) as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )
