from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PaymentCreateResponseSchema(BaseModel):
    client_secret: str


class PaymentReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    status: str
    created_at: datetime
