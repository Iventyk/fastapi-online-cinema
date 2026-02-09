from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.schemas.payment import PaymentCreateResponseSchema, PaymentReadSchema, PaymentItemReadSchema
from src.services.payment import create_payment_for_order, get_user_payment_history, get_all_payments
from src.securuty.utils import get_current_user, CurrentUser
from src.notifications.emails import EmailSender
from src.databases.models import UserGroupEnum

payment_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_router.get("/admin", response_model=list[PaymentReadSchema])
async def get_all_user_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
    user_id: int | None = None,
    status: str | None = None,
) -> list[PaymentReadSchema]:
    """
    Get all payments (admin only) with optional filters.
    """
    if auth_user.permission != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    payments = await get_all_payments(
        db=db,
        user_id=user_id,
        status=status,
    )
    return payments


@payment_router.post("/{order_id}", response_model=PaymentCreateResponseSchema)
async def create_payment(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
    email_service: EmailSender = Depends(),
) -> PaymentCreateResponseSchema:
    """
    Create a payment for the given order and return client secret.
    """
    client_secret = await create_payment_for_order(
        db=db, user_id=auth_user.id, order_id=order_id, email_service=email_service
    )
    return PaymentCreateResponseSchema(client_secret=client_secret)


@payment_router.get("/", response_model=list[PaymentReadSchema])
async def get_my_payments(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[PaymentReadSchema]:
    """
    Get all payments for the current user.
    """
    payments = await get_user_payment_history(db=db, user_id=auth_user.id)
    return payments
