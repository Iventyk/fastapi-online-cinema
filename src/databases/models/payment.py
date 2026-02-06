from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    ForeignKey,
    DateTime,
    Numeric,
    String,
    func,
    Enum,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

if TYPE_CHECKING:
    from src.databases.models.base import Base
    from src.databases.models.orders import Order
    from src.databases.models.accounts import UserModel
    from src.databases.models.orders import OrderItem


class PaymentStatusEnum(StrEnum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum),
        default=PaymentStatusEnum.SUCCESSFUL,
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="payments"
    )
    order: Mapped["Order"] = relationship("Order", back_populates="payments")
    items: Mapped[list["PaymentItem"]] = relationship(
        "PaymentItem", back_populates="payment", cascade="all, delete-orphan"
    )


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id"), nullable=False, index=True
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id"), nullable=False, index=True
    )
    price_at_payment: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    payment: Mapped["Payment"] = relationship(
        "Payment", back_populates="items"
    )
    order_item: Mapped["OrderItem"] = relationship("OrderItem")
