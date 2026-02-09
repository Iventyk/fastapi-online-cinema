from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PaymentItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_item_id: int
    price_at_payment: Decimal


class PaymentReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    status: str
    created_at: datetime
    items: list[PaymentItemReadSchema]


class PaymentCreateResponseSchema(BaseModel):
    client_secret: str
