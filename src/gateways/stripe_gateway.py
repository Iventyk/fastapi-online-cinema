import stripe
from typing import Any

from src.config import get_settings
from src.gateways.base import PaymentGatewayInterface

settings = get_settings()

stripe.api_key = settings.STRIPE_API_KEY


class StripeGateway(PaymentGatewayInterface):
    """Stripe payment gateway implementation."""

    async def create_payment_intent(
        self, *, amount: int, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata=metadata,
            automatic_payment_methods={"enabled": True},
        )
        return intent  # type: ignore[no-any-return]
