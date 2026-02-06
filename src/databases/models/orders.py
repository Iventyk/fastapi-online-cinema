from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import (
    Integer,
    func,
    DateTime,
    ForeignKey,
    Enum,
    Numeric,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.databases.models.base import Base
from src.databases.models.accounts import UserModel
from src.databases.models.movies import Movie


class StatusEnum(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False
    )
    total_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_at_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    movie: Mapped["Movie"] = relationship("Movie")
