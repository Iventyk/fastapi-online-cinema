from pydantic import BaseModel
from typing import Optional

class DirectorBase(BaseModel):
    name: str

class DirectorCreate(DirectorBase):
    pass

class DirectorRead(DirectorBase):
    id: int
    movies_count: Optional[int] = 0

    class Config:
        from_attributes = True
