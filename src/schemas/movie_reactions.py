from pydantic import BaseModel


class MovieReactionRead(BaseModel):
    likes: int
    dislikes: int

    class Config:
        from_attributes = True
