from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.movies import Genre, Movie
from src.schemas.genres import GenreCreate, GenreRead

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=List[GenreRead])
async def get_genres(db: AsyncSession = Depends(get_db)):
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
    return result.mappings().all()


@router.get("/{genre_id}/movies")
async def get_genre_movies(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    return genre.movies


@router.post(
    "",
    response_model=GenreRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_genre(
    data: GenreCreate,
    db: AsyncSession = Depends(get_db),
):
    genre = Genre(name=data.name)
    db.add(genre)
    await db.commit()
    await db.refresh(genre)

    return GenreRead(
        id=genre.id,
        name=genre.name,
        movies_count=0,
    )


@router.delete(
    "/{genre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Genre).where(Genre.id == genre_id))
    genre = result.scalar_one_or_none()

    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found",
        )

    await db.delete(genre)
    await db.commit()
