from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.payment import Payment, PaymentStatusEnum


async def create_payment(
    *,
    db: AsyncSession,
    user_id: int,
    order_id: int,
    amount: Decimal,
    external_payment_id: str,
) -> Payment:
    payment = Payment(
        user_id=user_id,
        order_id=order_id,
        amount=amount,
        external_payment_id=external_payment_id,
        status=PaymentStatusEnum.SUCCESSFUL,
    )
    db.add(payment)
    await db.flush()
    return payment


async def update_payment_status(
    *,
    db: AsyncSession,
    payment: Payment,
    status: PaymentStatusEnum,
) -> None:
    payment.status = status
    await db.flush()


async def get_user_payments(
    *, db: AsyncSession, user_id: int
) -> Sequence[Payment]:
    result = await db.execute(
        select(Payment).where(Payment.user_id == user_id)
    )
    return result.scalars().all()


async def get_payment_by_external_id(
    *, db: AsyncSession, external_payment_id: str
) -> Payment | None:
    result = await db.execute(
        select(Payment).where(
            Payment.external_payment_id == external_payment_id
        )
    )
    return result.scalar_one_or_none()
