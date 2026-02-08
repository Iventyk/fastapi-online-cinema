from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.payment import PaymentItem


async def create_payment_item(
    *,
    db: AsyncSession,
    payment_id: int,
    order_item_id: int,
    price_at_payment: Decimal,
) -> PaymentItem:
    item = PaymentItem(
        payment_id=payment_id,
        order_item_id=order_item_id,
        price_at_payment=price_at_payment,
    )
    db.add(item)
    await db.flush()
    return item
