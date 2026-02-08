from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.schemas.payment import PaymentCreateResponseSchema
from src.services.payment import create_payment_for_order

payment_router = APIRouter(prefix="/payments", tags=["Payments"])


@payment_router.post("/{order_id}", response_model=PaymentCreateResponseSchema)
async def create_payment(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentCreateResponseSchema:
    client_secret = await create_payment_for_order(
        db=db,
        user_id=1,  # ⛔ TODO: replace with real auth
        order_id=order_id,
    )
    return PaymentCreateResponseSchema(client_secret=client_secret)
