from decimal import Decimal
from typing import Annotated, Any, Sequence

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.databases import get_db
from src.databases.models.orders import Order, StatusEnum
from src.databases.models.payment import Payment, PaymentItem, PaymentStatusEnum
from src.gateways.stripe_gateway import StripeGateway
from src.repositories.payment import create_payment, update_payment_status, get_payment_by_external_id
from src.repositories.payment_item import create_payment_item
from src.exceptions.payments import OrderNotPayable
from src.notifications.emails import EmailSender


MIN_CHARGE_USD = Decimal("0.50")


async def create_payment_for_order(
    *,
    db: AsyncSession,
    user_id: int,
    order_id: int,
) -> tuple[str, Payment]:
    """
    Create a Stripe payment intent for an order, save payment and payment items.
    Email confirmation is sent asynchronously via Celery task, not here.
    """
    # Отримати замовлення з товарами
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order or order.status != StatusEnum.PENDING:
        raise OrderNotPayable("Order cannot be paid")

    # Порахувати загальну суму замовлення
    total_amount = sum((item.price_at_order for item in order.items), Decimal("0.00"))

    if total_amount < MIN_CHARGE_USD:
        raise ValueError(
            f"Total amount ${total_amount} is below the minimum charge for USD"
        )

    # Конвертувати у центи та округлити до цілого
    amount_in_cents = int((total_amount * 100).quantize(Decimal("1"), rounding=ROUND_DOWN))

    # Створити Stripe payment intent
    stripe_gateway = StripeGateway()
    intent = await stripe_gateway.create_payment_intent(
        amount=amount_in_cents,
        currency="usd",
        metadata={"order_id": str(order.id), "user_id": str(user_id)},
    )

    # Зберегти Payment у базі
    payment = await create_payment(
        db=db,
        user_id=user_id,
        order_id=order.id,
        amount=total_amount,
        external_payment_id=intent["id"],
    )

    # Зберегти Payment Items
    for item in order.items:
        await create_payment_item(
            db=db,
            payment_id=payment.id,
            order_item_id=item.id,
            price_at_payment=item.price_at_order,
        )

    # Оновити статус замовлення
    order.status = StatusEnum.PAID
    await db.commit()

    return intent["client_secret"], payment


async def handle_stripe_webhook(
    *, db: Annotated[AsyncSession, Depends(get_db)], event: dict[str, Any], email_service: EmailSender
) -> None:
    """
    Handle Stripe webhook events to update Payment and Order status.
    """
    payment_id = event.get("data", {}).get("object", {}).get("id")
    status = event.get("type")

    payment = await get_payment_by_external_id(db=db, external_payment_id=payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if status == "payment_intent.succeeded":
        await update_payment_status(db=db, payment=payment, status=PaymentStatusEnum.SUCCESSFUL)
        payment.order.status = StatusEnum.PAID
        await db.commit()

        # Send email confirmation
        await email_service._send_email(
            recipient=payment.user.email,
            subject="Payment Successful",
            html_content=f"<p>Your payment of ${payment.amount} for order #{payment.order_id} was successful.</p>"
        )

    elif status in ("payment_intent.canceled", "payment_intent.payment_failed"):
        await update_payment_status(db=db, payment=payment, status=PaymentStatusEnum.CANCELED)
        payment.order.status = StatusEnum.CANCELLED
        await db.commit()


async def get_user_payment_history(
    *, db: Annotated[AsyncSession, Depends(get_db)], user_id: int
) -> Sequence[Payment]:
    """
    Retrieve all payments for a user.
    """
    result = await db.execute(select(Payment).where(Payment.user_id == user_id))
    return result.scalars().all()


async def get_all_payments(
    *, db: Annotated[AsyncSession, Depends(get_db)], user_id: int | None = None,
    status: PaymentStatusEnum | None = None
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
