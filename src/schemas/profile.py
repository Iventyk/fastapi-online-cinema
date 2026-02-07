from datetime import date

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict

from src.databases.models.accounts import GenderEnum


class ProfileCreateSchema(BaseModel):
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str
    avatar: UploadFile = None


class ProfileReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str
    avatar: str


class ProfileUpdateSchema(BaseModel):
    first_name: str = None
    last_name: str = None
    gender: GenderEnum = None
    date_of_birth: date = None
    info: str = None
    avatar: UploadFile = None