from pydantic import BaseModel
from typing import Optional


class StarBase(BaseModel):
    name: str


class StarCreate(StarBase):
    pass


class StarRead(StarBase):
    id: int
    movies_count: Optional[int] = 0

    class Config:
        from_attributes = True
