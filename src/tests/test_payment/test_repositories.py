from decimal import Decimal

import pytest
from src.repositories.payment import (
    create_payment,
    update_payment_status,
    get_user_payments,
)
from src.databases.models.payment import PaymentStatusEnum


@pytest.mark.asyncio
async def test_create_payment(db_session, test_user, test_order):
    payment = await create_payment(
        db=db_session,
        user_id=test_user.id,
        order_id=test_order.id,
        amount=Decimal("10.00"),
        external_payment_id="pi_repo_test",
    )

    assert payment.id is not None
    assert payment.status == PaymentStatusEnum.PENDING


@pytest.mark.asyncio
async def test_update_payment_status(db_session, test_payment):
    await update_payment_status(
        db=db_session,
        payment=test_payment,
        status=PaymentStatusEnum.SUCCESSFUL,
    )
    assert test_payment.status == PaymentStatusEnum.SUCCESSFUL


@pytest.mark.asyncio
async def test_get_user_payments(db_session, test_user, test_payment):
    payments = await get_user_payments(db=db_session, user_id=test_user.id)
    assert len(payments) > 0
    assert payments[0].user_id == test_user.id
