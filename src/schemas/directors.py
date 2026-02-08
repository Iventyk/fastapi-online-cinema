from pydantic import BaseModel, ConfigDict
from typing import Optional


class DirectorBase(BaseModel):
    name: str


class DirectorCreate(DirectorBase):
    pass


class DirectorRead(DirectorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movies_count: Optional[int] = 0
