from datetime import datetime
from typing import Annotated, List, Optional, Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.crud import (
    create_order,
    get_user_orders,
    cancel_order,
    get_all_orders_admin,
)
from src.databases.models import StatusEnum, UserGroupEnum
from src.exceptions import (
    MovieDoesNotExist,
    MovieAlreadyPurchased,
    OrderNotFound,
    OrderCancellationNotPossible,
    PendingOrderExists,
    OrderAlreadyPaid,
)
from src.schemas import (
    CurrentUser,
    OrderReadSchema,
    OrderCreateSchema,
    OrderCreateResponseSchema,
)
from src.securuty.utils import get_current_user

order_router = APIRouter(prefix="/orders", tags=["Orders"])


@order_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderCreateResponseSchema,
)
async def create_new_order(
    order_data: OrderCreateSchema,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    try:
        order = await create_order(
            db=db, user_id=current_user.user_id, movie_ids=order_data.movie_ids
        )
        return order

    except (MovieAlreadyPurchased, MovieDoesNotExist, PendingOrderExists) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        )


@order_router.get("/all/", response_model=List[OrderReadSchema])
async def list_my_orders(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    return await get_user_orders(db, current_user.user_id)


@order_router.get("/admin/all/", response_model=List[OrderReadSchema])
async def list_all_orders_for_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    user_id: Optional[int] = None,
    order_status: Optional[StatusEnum] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> Any:
    if current_user.permission not in [
        UserGroupEnum.ADMIN,
        UserGroupEnum.MODERATOR,
    ]:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view all orders",
        )

    return await get_all_orders_admin(
        db=db,
        user_id=user_id,
        status=order_status,
        date_from=date_from,
        date_to=date_to,
    )


@order_router.patch("/{order_id}/cancel", response_model=OrderReadSchema)
async def cancel_my_order(
    order_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    try:
        return await cancel_order(db, order_id, current_user.user_id)
    except OrderNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except OrderAlreadyPaid as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(e),
                "refund_url": f"/payment/{order_id}/refund",
            },
        )
    except OrderCancellationNotPossible as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
