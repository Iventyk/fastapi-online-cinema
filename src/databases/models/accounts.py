from datetime import datetime, date, timezone, timedelta
from enum import StrEnum, auto
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import (
    String,
    Boolean,
    Integer,
    func,
    DateTime,
    ForeignKey,
    Enum,
    Date,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship, mapped_column

from src.config import get_settings
from src.databases.models.base import Base
from src.validators import validate_password
from src.security import hash_password, verify_password
from src.databases.models.favorites import Favorite

if TYPE_CHECKING:
    from src.databases.models import Cart, Order, Payment


settings = get_settings()


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MALE = auto()
    FEMALE = auto()


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

    def __repr__(self) -> str:
        return f"<UserGroupModel(id={self.id}, name={self.name})>"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
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
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=True
    )
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )
    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )

    activation_token: Mapped[Optional["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    password_reset_token: Mapped[Optional["PasswordResetTokenModel"]] = (
        relationship(
            "PasswordResetTokenModel",
            back_populates="user",
            cascade="all, delete-orphan",
        )
    )

    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    profile: Mapped[Optional["UserProfileModel"]] = relationship(
        "UserProfileModel", back_populates="user", cascade="all, delete-orphan"
    )

    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite",
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<UserModel(id={self.id}, email={self.email}, "
            f"is_active={self.is_active})>"
        )

    def has_group(self, group_name: UserGroupEnum) -> bool:
        return self.group.name == group_name

    @classmethod
    def create(
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
            "Password is write-only. Use the setter to set the password."
        )

    @password.setter
    def password(self, password: str) -> None:
        hashed_password = hash_password(password)

        self._hashed_password = hashed_password

    def check_password(self, password: str) -> bool:
        return verify_password(password, self._hashed_password)


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[GenderEnum]] = mapped_column(Enum(GenderEnum))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    info: Mapped[Optional[str]] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="profile"
    )

    def __repr__(self) -> str:
        return (
            f"<UserProfileModel(id={self.id}, first_name={self.first_name}, "
            f"last_name={self.last_name}, "
            f"gender={self.gender}, date_of_birth={self.date_of_birth})>"
        )


class TokenBaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc) + timedelta(days=1),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


class ActivationTokenModel(TokenBaseModel):
    __tablename__ = "activation_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="activation_token"
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_activation_token_for_user"),
    )

    @classmethod
    def create(
        cls, user_id: int | Mapped[int], token: str
    ) -> "ActivationTokenModel":
        """
        Factory method to create a new RefreshTokenModel instance.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.ACTIVATE_TOKEN_DAYS
        )
        return cls(user_id=user_id, expires_at=expires_at, token=token)

    def __repr__(self) -> str:
        return (
            f"<ActivationTokenModel(id={self.id}, "
            f"token={self.token}, expires_at={self.expires_at})>"
        )


class PasswordResetTokenModel(TokenBaseModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="password_reset_token"
    )

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_reset_token_for_user"),
    )

    @classmethod
    def create(
        cls, user_id: int | Mapped[int], token: str
    ) -> "PasswordResetTokenModel":
        """
        Factory method to create a new RefreshTokenModel instance.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.RESET_TOKEN_DURATION
        )
        return cls(user_id=user_id, expires_at=expires_at, token=token)

    def __repr__(self) -> str:
        return (
            f"<PasswordResetTokenModel(id={self.id}, "
            f"token={self.token}, expires_at={self.expires_at})>"
        )


class RefreshTokenModel(TokenBaseModel):
    __tablename__ = "refresh_tokens"

    user: Mapped[UserModel] = relationship(
        "UserModel", back_populates="refresh_tokens"
    )
    token: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        # default=generate_secure_token
    )

    @classmethod
    def create(
        cls, user_id: int | Mapped[int], token: str
    ) -> "RefreshTokenModel":
        """
        Factory method to create a new RefreshTokenModel instance.
        """
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_DAYS
        )
        return cls(user_id=user_id, expires_at=expires_at, token=token)

    def __repr__(self) -> str:
        return (
            f"<RefreshTokenModel(id={self.id}, "
            f"token={self.token}, expires_at={self.expires_at})>"
        )
