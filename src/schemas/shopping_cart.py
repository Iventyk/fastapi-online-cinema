from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional


class GenreSchema(BaseModel):
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieInCartSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(validation_alias="name")
    price: Optional[float]
    release_year: int = Field(validation_alias="year")
    genres: List[GenreSchema]


class CartItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie: MovieInCartSchema


class CartReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    items: List[CartItemReadSchema]


class CartItemCreateSchema(BaseModel):
    movie_id: int
