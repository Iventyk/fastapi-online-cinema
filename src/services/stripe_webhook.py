from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.orders import StatusEnum
from src.databases.models.payment import PaymentStatusEnum
from src.repositories.payment import (
    get_payment_by_external_id,
)
from src.tasks.email_tasks import send_payment_success_email_task


async def handle_stripe_webhook(
    *,
    db: AsyncSession,
    event: dict[str, Any],
) -> None:
    """
    Handle Stripe webhook events and update payment/order state.
    Emails are sent asynchronously via Celery tasks.
    """
    if event["type"] not in (
        "payment_intent.succeeded",
        "payment_intent.canceled",
        "payment_intent.payment_failed",
    ):
        return

    intent = event["data"]["object"]
    external_id = intent["id"]

    payment = await get_payment_by_external_id(
        db=db,
        external_payment_id=external_id,
    )

    if not payment:
        return

    try:
        if event["type"] == "payment_intent.succeeded":
            payment.status = PaymentStatusEnum.SUCCESSFUL
            payment.order.status = StatusEnum.PAID
            await db.commit()

            # Celery task для email
            send_payment_success_email_task.delay(
                email=payment.user.email,
                amount=float(payment.amount),
                order_id=payment.order_id,
            )

        elif event["type"] in (
            "payment_intent.canceled",
            "payment_intent.payment_failed",
        ):
            payment.status = PaymentStatusEnum.CANCELED
            payment.order.status = StatusEnum.CANCELLED
            await db.commit()

    except Exception:
        await db.rollback()
        raise
