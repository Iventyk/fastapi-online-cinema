from abc import ABC, abstractmethod
from typing import Any


class PaymentGatewayInterface(ABC):
    """Base interface for payment gateways."""

    @abstractmethod
    async def create_payment_intent(
        self, *, amount: int, currency: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Create payment intent."""
