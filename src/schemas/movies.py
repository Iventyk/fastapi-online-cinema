from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class GenreSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class StarSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DirectorSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CertificationSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MovieCreate(BaseModel):
    name: str
    year: int
    time: int

    imdb: Decimal
    votes: int

    meta_score: Optional[float] = None
    gross: Optional[float] = None

    description: str
    price: Optional[float] = None

    certification_id: int

    genre_ids: List[int] = Field(default_factory=list)
    star_ids: List[int] = Field(default_factory=list)
    director_ids: List[int] = Field(default_factory=list)


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None

    imdb: Optional[Decimal] = None
    votes: Optional[int] = None

    meta_score: Optional[float] = None
    gross: Optional[float] = None

    description: Optional[str] = None
    price: Optional[float] = None

    certification_id: Optional[int] = None

    genre_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None


class MovieListItem(BaseModel):
    id: int
    uuid: UUID

    name: str
    year: int
    time: int

    imdb: Decimal
    price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MovieRead(BaseModel):
    id: int
    uuid: UUID

    name: str
    year: int
    time: int

    imdb: Decimal
    votes: int
    meta_score: Optional[float]
    gross: Optional[float]

    description: str
    price: Optional[float]

    certification: CertificationSchema
    genres: List[GenreSchema]
    stars: List[StarSchema]
    directors: List[DirectorSchema]

    model_config = ConfigDict(from_attributes=True)
