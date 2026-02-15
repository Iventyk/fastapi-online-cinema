import pytest
from decimal import Decimal
from src.databases.models.payment import (
    Payment,
    PaymentItem,
    PaymentStatusEnum,
)


@pytest.mark.asyncio
async def test_payment_creation(db_session, test_user, test_order):
    payment = Payment(
        user_id=test_user.id,
        order_id=test_order.id,
        amount=Decimal("20.00"),
        external_payment_id="pi_test_model",
        status=PaymentStatusEnum.PENDING,
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)

    assert payment.id is not None
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.user_id == test_user.id
    assert payment.order_id == test_order.id


@pytest.mark.asyncio
async def test_payment_item_creation(
    db_session, test_payment, test_order, test_order_item
):
    payment_item = PaymentItem(
        payment_id=test_payment.id,
        order_item_id=test_order_item.id,
        price_at_payment=Decimal("20.00"),
    )
    db_session.add(payment_item)
    await db_session.commit()
    await db_session.refresh(payment_item)

    assert payment_item.id is not None
    assert payment_item.payment_id == test_payment.id
    assert payment_item.order_item_id == test_order_item.id
