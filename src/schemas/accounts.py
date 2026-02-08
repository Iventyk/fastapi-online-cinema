from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.databases.models import UserGroupEnum
from src.validators import validate_password


class CurrentUser(BaseModel):
    """Instance of authenticated user"""

    user_id: int
    email: str
    permission: str
    is_active: bool
    profile_id: int | None


class UserBaseSchema(BaseModel):
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    group: UserGroupEnum | None = None
    password: str
    guest_cart_items: Optional[List[int]] = None

    @field_validator("email")
    @classmethod
    def validate_corporate_email(cls, v: str) -> str:
        if "temporary-mail.com" in v:
            raise ValueError("Temporary mails are not allowed")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        try:
            return validate_password(password=v)
        except ValueError:
            raise


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password(password=v)
        return v


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordRequestSchema(BaseModel):
    token: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password(password=v)
        return v


class UserReadSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    permission: UserGroupEnum | None = None


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
    guest_cart_items: Optional[List[int]] = None


class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CommonResponseSchema(BaseModel):
    message: str


class AdminOperatedData(BaseModel):
    activation: bool = False
    permission: UserGroupEnum | None = None


class RefreshTokenSchema(BaseModel):
    refresh_token: str

class RefreshTokenResponseSchema(BaseModel):
    access_token: str
