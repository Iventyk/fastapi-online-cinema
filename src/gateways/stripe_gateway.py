import stripe

from src.config import get_settings
from src.gateways.base import PaymentGatewayInterface

settings = get_settings()

stripe.api_key = settings.STRIPE_API_KEY


class StripeGateway(PaymentGatewayInterface):
    """Stripe payment gateway implementation."""

    async def create_payment_intent(
        self,
        *,
        amount: int,
        currency: str,
        metadata: dict[str, str],
    ) -> dict:
        """
        Create Stripe PaymentIntent (card only, no redirects).
        """
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method_types=["card"],
            metadata=metadata,
        )

        return intent
