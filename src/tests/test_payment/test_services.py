import pytest
from unittest.mock import AsyncMock, patch
from src.services.payment import create_payment_for_order
from src.databases.models.payment import PaymentStatusEnum


@pytest.mark.asyncio
@patch(
    "src.services.payment.StripeGateway.create_payment_intent",
    new_callable=AsyncMock,
)
async def test_create_payment_for_order_success(
    mock_stripe_intent, db_session, test_user, test_order
):
    mock_stripe_intent.return_value = {
        "id": "pi_mocked_123",
        "client_secret": "secret_mocked",
    }

    client_secret, payment = await create_payment_for_order(
        db=db_session, user_id=test_user.id, order_id=test_order.id
    )

    assert client_secret == "secret_mocked"
    assert payment.status == PaymentStatusEnum.PENDING
    assert payment.user_id == test_user.id
