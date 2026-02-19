from uuid import UUID, uuid4
from typing import List, Optional, TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import (
    Table,
    Column,
    String,
    Integer,
    Float,
    Text,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    DECIMAL,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .base import Base
from src.databases.models.favorites import Favorite
from src.databases.models.movie_reactions import MovieReaction
from src.databases.models.movie_comments import MovieComment

if TYPE_CHECKING:
    from src.databases.models import CartItem


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "genre_id",
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True
    ),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
        lazy="selectin",
    )


class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_stars,
        back_populates="stars",
        lazy="selectin",
    )


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_directors,
        back_populates="directors",
        lazy="selectin",
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        back_populates="certification",
        lazy="selectin",
    )


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint(
            "name", "year", "time", name="uq_movie_name_year_time"
        ),
        CheckConstraint("imdb >= 0 AND imdb <= 10", name="imdb_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[UUID] = mapped_column(
        default=uuid4,
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    time: Mapped[int] = mapped_column(Integer, nullable=False)

    imdb: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False, index=True)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)

    meta_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Optional[float]] = mapped_column(
        DECIMAL(10, 2), nullable=True
    )

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id", ondelete="RESTRICT"),
        nullable=False,
    )

    certification: Mapped["Certification"] = relationship(
        back_populates="movies",
        lazy="selectin",
    )

    genres: Mapped[List["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
        lazy="selectin",
    )

    stars: Mapped[List["Star"]] = relationship(
        secondary=movie_stars,
        back_populates="movies",
        lazy="selectin",
    )

    directors: Mapped[List["Director"]] = relationship(
        secondary=movie_directors,
        back_populates="movies",
        lazy="selectin",
    )

    favorited_by: Mapped[List["Favorite"]] = relationship(
        "Favorite",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="movie"
    )

    reactions: Mapped[list["MovieReaction"]] = relationship(
        "MovieReaction",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    comments: Mapped[list["MovieComment"]] = relationship(
        "MovieComment",
        back_populates="movie",
        cascade="all, delete-orphan",
    )
