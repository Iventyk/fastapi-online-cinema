import pytest
import decimal
from pydantic import ValidationError
from src.schemas.orders import (
    OrderCreateSchema,
    OrderItemReadSchema,
    OrderReadSchema,
)
from src.databases.models.orders import StatusEnum
from datetime import datetime


class TestOrderSchemas:

    def test_order_create_schema_success(self):
        data = {"movie_ids": [1, 2, 3]}
        schema = OrderCreateSchema(**data)
        assert schema.movie_ids == [1, 2, 3]

    def test_order_create_schema_empty_list_raises_error(self):
        with pytest.raises(ValidationError) as excinfo:
            OrderCreateSchema(movie_ids=[])
        assert "Order must contain at least one movie ID" in str(excinfo.value)

    def test_order_item_read_decimal_formatting(self):
        raw_data = {
            "id": 1,
            "movie_id": 10,
            "price_at_order": decimal.Decimal("150.55555"),  # Багато знаків
        }
        schema = OrderItemReadSchema.model_validate(raw_data)

        assert schema.price_at_order == decimal.Decimal("150.56")

    def test_order_read_schema_full_success(self):
        raw_data = {
            "id": 1,
            "user_id": 1,
            "created_at": datetime.now(),
            "status": StatusEnum.PENDING,
            "total_amount": decimal.Decimal("99.9"),
            "items": [
                {
                    "id": 1,
                    "movie_id": 10,
                    "price_at_order": decimal.Decimal("99.9"),
                }
            ],
        }
        schema = OrderReadSchema.model_validate(raw_data)
        assert schema.total_amount == decimal.Decimal("99.90")
        assert len(schema.items) == 1
