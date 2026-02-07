from datetime import date
from typing import Optional
from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator

from src.databases.models.accounts import GenderEnum


class ProfileBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProfileCreateSchema(ProfileBase):
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str
    avatar: Optional[UploadFile] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip().capitalize()

    @field_validator("date_of_birth")
    @classmethod
    def check_age(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


class ProfileReadSchema(ProfileBase):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str
    avatar: Optional[str] = "default_avatar.png"


class ProfileUpdateSchema(ProfileBase):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
    avatar: Optional[UploadFile] = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def validate_optional_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Name cannot be empty")
            return v.strip().capitalize()
        return v
