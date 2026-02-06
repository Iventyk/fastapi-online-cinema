from pydantic import BaseModel


class FavoriteRead(BaseModel):
    movie_id: int

    class Config:
        from_attributes = True