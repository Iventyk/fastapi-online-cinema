import pytest
from decimal import Decimal
from src.main import app
from src.schemas import CurrentUser
from src.databases.models.payment import Payment, PaymentStatusEnum
from src.security.utils import get_current_user


@pytest.mark.asyncio
async def test_create_payment_endpoint(
    client,
    test_user,
    test_order,
    monkeypatch,
):
    """
    Test POST /payments/{order_id} endpoint
    with mocked payment service and authorized user.
    """

    async def mock_create_payment_for_order(*, db, user_id, order_id):
        payment = Payment(
            user_id=user_id,
            order_id=order_id,
            amount=Decimal("10.00"),
            external_payment_id="pi_client_secret_mock",
            status=PaymentStatusEnum.PENDING,
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return "pi_client_secret_mock", payment

    monkeypatch.setattr(
        "src.routers.payments.create_payment_for_order",
        mock_create_payment_for_order,
    )

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=test_user.id,
        email=str(test_user.email),
        permission="USER",
        is_active=True,
        profile_id=None,
    )

    response = await client.post(f"/payments/{test_order.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["client_secret"] == "pi_client_secret_mock"

    app.dependency_overrides.clear()
