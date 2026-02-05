from datetime import datetime
from enum import StrEnum, auto
from typing import List

from pydantic import EmailStr
from sqlalchemy import (
    String,
    Boolean,
    Integer,
    func,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.databases.models.base import Base


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum), nullable=False, unique=True
    )

    users: Mapped[List["UserModel"]] = relationship(
        "UserModel", back_populates="group"
    )

    def __repr__(self):
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[EmailStr] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password", String(255), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey(
            "user_groups.id", ondelete="CASCADE"
        ), nullable=True
    )
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    @classmethod
    async def create(
            cls, email: str, raw_password: str, group_id: int | Mapped[int]
    ) -> "UserModel":
        """
        Factory method to create a new UserModel instance.

        This method simplifies the creation of a new user by handling
        password hashing and setting required attributes.
        """
        user = cls(email=email, group_id=group_id)
        user.password = raw_password
        return user

    @property
    def password(self) -> None:
        raise AttributeError(
            "Password is write-only. Use the setter to set the password.")

    @password.setter
    def password(self, password: str) -> None:
        # TODO passhord Hashing and validataion

        self._hashed_password = password
