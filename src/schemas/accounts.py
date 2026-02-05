from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.databases.models import UserGroupEnum
from src.validators import validate_password


class UserBaseSchema(BaseModel):
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    group: UserGroupEnum | None = None
    password: str

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


class UserReadSchema(UserBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class LoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
