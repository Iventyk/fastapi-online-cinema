from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.databases.models.payment import PaymentStatusEnum
from src.schemas.payment import PaymentCreateResponseSchema, PaymentReadSchema
from src.services.payment import (
    create_payment_for_order,
    get_user_payment_history,
    get_all_payments,
)
from src.security.utils import get_current_user, CurrentUser
from src.databases.models import UserGroupEnum

payment_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_router.post("/{order_id}", response_model=PaymentCreateResponseSchema)
async def create_payment(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
):
    client_secret, _ = await create_payment_for_order(
        db=db,
        user_id=auth_user.user_id,
        order_id=order_id,
    )

    return PaymentCreateResponseSchema(client_secret=client_secret)


@payment_router.get(
    "/",
    response_model=list[PaymentReadSchema],
    summary="Get current user's payments",
)
async def get_my_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[PaymentReadSchema]:
    payments = await get_user_payment_history(db=db, user_id=auth_user.user_id)
    return [PaymentReadSchema.model_validate(payment) for payment in payments]


@payment_router.get(
    "/admin",
    response_model=list[PaymentReadSchema],
    summary="Get all payments (Admin only)",
)
async def get_all_user_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
    user_id: int | None = Query(None, description="Filter by user ID"),
    status: PaymentStatusEnum | None = Query(
        None, description="Filter by status"
    ),
) -> list[PaymentReadSchema]:
    if auth_user.permission != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=403, detail="Admin privileges required"
        )

    payments = await get_all_payments(db=db, user_id=user_id, status=status)

    return [PaymentReadSchema.model_validate(payment) for payment in payments]
