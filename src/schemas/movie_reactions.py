from pydantic import BaseModel, ConfigDict


class MovieReactionRead(BaseModel):
    likes: int
    dislikes: int

    model_config = ConfigDict(from_attributes=True)
