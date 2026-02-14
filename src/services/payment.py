from decimal import Decimal, ROUND_DOWN
from typing import Annotated, Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.databases import get_db
from src.databases.models.orders import Order, StatusEnum
from src.databases.models.payment import Payment, PaymentStatusEnum
from src.gateways.stripe_gateway import StripeGateway
from src.repositories.payment import (
    create_payment,
)
from src.repositories.payment_item import create_payment_item
from src.exceptions.payments import OrderNotPayable

MIN_CHARGE_USD = Decimal("0.50")


async def create_payment_for_order(
    *,
    db: AsyncSession,
    user_id: int,
    order_id: int,
) -> tuple[str, Payment]:
    """
    Create Stripe PaymentIntent and store Payment in PENDING state.
    Order status is NOT changed here.
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order or order.status != StatusEnum.PENDING:
        raise OrderNotPayable("Order cannot be paid")

    total_amount = sum(
        (item.price_at_order for item in order.items),
        Decimal("0.00"),
    )

    if total_amount < MIN_CHARGE_USD:
        raise OrderNotPayable("Order total is below minimum charge")

    amount_in_cents = int(
        (total_amount * 100).quantize(Decimal("1"), rounding=ROUND_DOWN)
    )

    stripe_gateway = StripeGateway()
    intent = await stripe_gateway.create_payment_intent(
        amount=amount_in_cents,
        currency="usd",
        metadata={
            "order_id": str(order.id),
            "user_id": str(user_id),
        },
    )

    try:
        payment = await create_payment(
            db=db,
            user_id=user_id,
            order_id=order.id,
            amount=total_amount,
            external_payment_id=intent["id"],
        )

        for item in order.items:
            await create_payment_item(
                db=db,
                payment_id=payment.id,
                order_item_id=item.id,
                price_at_payment=item.price_at_order,
            )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return intent["client_secret"], payment


async def get_user_payment_history(
    *, db: Annotated[AsyncSession, Depends(get_db)], user_id: int
) -> Sequence[Payment]:
    """
    Retrieve all payments for a user.
    """
    result = await db.execute(
        select(Payment).where(Payment.user_id == user_id)
    )
    return result.scalars().all()


async def get_all_payments(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int | None = None,
    status: PaymentStatusEnum | None = None,
) -> Sequence[Payment]:
    """
    Retrieve all payments with optional filters (admin use).
    """
    query = select(Payment)
    if user_id:
        query = query.where(Payment.user_id == user_id)
    if status:
        query = query.where(Payment.status == status)

    result = await db.execute(query)
    return result.scalars().all()
