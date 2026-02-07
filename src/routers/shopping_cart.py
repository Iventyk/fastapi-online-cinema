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
from src.securuty.utils import get_current_user

shopping_cart_router = APIRouter(prefix="/cart", tags=["Carts"])


@shopping_cart_router.post(
    "/{user_id}/",
    status_code=status.HTTP_201_CREATED,
    response_model=MovieInCartSchema,
)
async def create_cart_item(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cart_item: CartItemCreateSchema,
) -> MovieInCartSchema:
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
    "/{user_id}/{cart_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_cart_item(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cart_item_id: int,
) -> None:
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


@shopping_cart_router.delete(
    "/{user_id}/clean/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_cart_items(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
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


@shopping_cart_router.get(
    "/{user_id}/",
    status_code=status.HTTP_200_OK,
    response_model=CartReadSchema,
)
async def get_cart_items(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CartReadSchema:
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
)
async def get_purchased_cart(
    user_id: int,
    authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[MovieInCartSchema]:
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
