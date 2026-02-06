from pydantic import BaseModel
from typing import Optional


class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreRead(GenreBase):
    id: int
    movies_count: Optional[int] = 0

    class Config:
        from_attributes = True
