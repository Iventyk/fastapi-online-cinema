from decimal import Decimal
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.databases import get_db
from src.databases.models.orders import Order, StatusEnum
from src.gateways.stripe_gateway import StripeGateway
from src.repositories.payment import create_payment
from src.repositories.payment_item import create_payment_item
from src.exceptions.payments import OrderNotPayable


async def create_payment_for_order(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: int,
    order_id: int,
) -> str:
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

    stripe_gateway = StripeGateway()
    intent = await stripe_gateway.create_payment_intent(
        amount=int(total_amount * 100),
        currency="usd",
        metadata={"order_id": str(order.id), "user_id": str(user_id)},
    )

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

    #await db.commit()

    return intent["client_secret"]
