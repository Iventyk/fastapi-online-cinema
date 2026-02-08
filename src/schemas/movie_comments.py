from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    text: str


class CommentRead(BaseModel):
    id: int
    text: str
    user_id: int

    class Config:
        from_attributes = True
