import decimal
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from src.databases.models.orders import StatusEnum


class OrderItemBaseSchema(BaseModel):
    movie_id: int


class OrderBaseSchema(BaseModel):
    pass


class OrderCreateSchema(OrderBaseSchema):
    movie_ids: List[int]

    @field_validator("movie_ids")
    @classmethod
    def check_not_empty(cls, v: int) -> int | None:
        if not v:
            raise ValueError("Order must contain at least one movie ID")
        return v


class OrderItemReadSchema(OrderItemBaseSchema):
    id: int
    price_at_order: decimal.Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderReadSchema(OrderBaseSchema):
    id: int
    user_id: int
    created_at: datetime
    status: StatusEnum
    total_amount: Optional[decimal.Decimal]
    items: List[OrderItemReadSchema]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdateSchema(BaseModel):
    status: StatusEnum
