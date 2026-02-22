from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from src.databases.dev_engine import get_db
from src.databases.models.movies import Genre, Movie
from src.schemas.genres import GenreCreate, GenreRead
from src.schemas.movies import MovieListItem

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get(
    "",
    response_model=List[GenreRead],
    summary="Get all genres",
    description="Returns all genres with number of associated movies.",
    responses={
        200: {"description": "List of genres"},
    },
)
async def get_genres(db: AsyncSession = Depends(get_db)) -> List[GenreRead]:
    stmt = (
        select(
            Genre.id,
            Genre.name,
            func.count(Movie.id).label("movies_count"),
        )
        .outerjoin(Genre.movies)
        .group_by(Genre.id)
        .order_by(Genre.name)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [
        GenreRead(
            id=row["id"],
            name=row["name"],
            movies_count=row["movies_count"],
        )
        for row in rows
    ]


@router.get(
    "/{genre_id}/movies",
    response_model=List[MovieListItem],
    summary="Get movies by genre",
    description="Returns all movies that belong to a specific genre.",
    responses={
        200: {"description": "List of movies for the genre"},
        404: {"description": "Genre not found"},
        500: {"description": "Database error"},
    },
)
async def get_genre_movies(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[MovieListItem]:
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    return [
        MovieListItem(
            id=m.id,
            uuid=m.uuid,
            name=m.name,
            year=m.year,
            time=m.time,
            imdb=m.imdb,
            price=m.price,
        )
        for m in genre.movies
    ]


@router.post(
    "",
    response_model=GenreRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create genre",
    description="Creates a new genre.",
    responses={
        201: {"description": "Genre created"},
        422: {"description": "Validation error"},
    },
)
async def create_genre(
    data: GenreCreate,
    db: AsyncSession = Depends(get_db),
) -> GenreRead:
    genre = Genre(name=data.name)
    db.add(genre)

    try:
        await db.commit()
        await db.refresh(genre)
    except SQLAlchemyError:
        await db.rollback()
        raise

    return GenreRead(
        id=genre.id,
        name=genre.name,
        movies_count=0,
    )


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete genre",
    description="Deletes a genre by ID.",
    responses={
        204: {"description": "Genre deleted"},
        404: {"description": "Genre not found"},
    },
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    try:
        await db.delete(genre)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
