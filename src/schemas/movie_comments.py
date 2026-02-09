from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    text: str


class CommentRead(BaseModel):
    id: int
    text: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)
