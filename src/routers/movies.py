from typing import List, Optional

from sqlalchemy import or_, asc, desc

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.movies import (
    Movie,
    Genre,
    Star,
    Director,
)
from src.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieRead,
    MovieListItem,
)


router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=List[MovieListItem])
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),

    search: Optional[str] = None,

    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    imdb_from: Optional[float] = None,
    imdb_to: Optional[float] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    genre_id: Optional[int] = None,
    certification_id: Optional[int] = None,

    sort_by: Optional[str] = Query(None, pattern="^(price|year|imdb)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),

    db: AsyncSession = Depends(get_db),
):
    stmt = select(Movie).distinct()

    if search:
        stmt = (
            stmt
            .outerjoin(Movie.directors)
            .outerjoin(Movie.stars)
            .where(
                or_(
                    Movie.name.ilike(f"%{search}%"),
                    Movie.description.ilike(f"%{search}%"),
                    Director.name.ilike(f"%{search}%"),
                    Star.name.ilike(f"%{search}%"),
                )
            )
        )

    if year_from:
        stmt = stmt.where(Movie.year >= year_from)

    if year_to:
        stmt = stmt.where(Movie.year <= year_to)

    if imdb_from:
        stmt = stmt.where(Movie.imdb >= imdb_from)

    if imdb_to:
        stmt = stmt.where(Movie.imdb <= imdb_to)

    if price_from:
        stmt = stmt.where(Movie.price >= price_from)

    if price_to:
        stmt = stmt.where(Movie.price <= price_to)

    if certification_id:
        stmt = stmt.where(Movie.certification_id == certification_id)

    if genre_id:
        stmt = stmt.join(Movie.genres).where(Genre.id == genre_id)

    if sort_by:
        column = getattr(Movie, sort_by)
        stmt = stmt.order_by(desc(column) if order == "desc" else asc(column))
    else:
        stmt = stmt.order_by(Movie.id)

    offset = (page - 1) * per_page
    stmt = stmt.offset(offset).limit(per_page)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get(
    "/{movie_id}",
    response_model=MovieRead,
)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return movie


@router.post(
    "",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    data: MovieCreate,
    db: AsyncSession = Depends(get_db),
):
    movie = Movie(
        name=data.name,
        year=data.year,
        time=data.time,
        imdb=data.imdb,
        votes=data.votes,
        meta_score=data.meta_score,
        gross=data.gross,
        description=data.description,
        price=data.price,
        certification_id=data.certification_id,
    )

    if data.genre_ids:
        genres = await db.execute(
            select(Genre).where(Genre.id.in_(data.genre_ids))
        )
        movie.genres = genres.scalars().all()

    if data.star_ids:
        stars = await db.execute(
            select(Star).where(Star.id.in_(data.star_ids))
        )
        movie.stars = stars.scalars().all()

    if data.director_ids:
        directors = await db.execute(
            select(Director).where(Director.id.in_(data.director_ids))
        )
        movie.directors = directors.scalars().all()

    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movie


@router.put(
    "/{movie_id}",
    response_model=MovieRead,
)
async def update_movie(
    movie_id: int,
    data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        if field.endswith("_ids"):
            continue
        setattr(movie, field, value)

    if data.genre_ids is not None:
        genres = await db.execute(
            select(Genre).where(Genre.id.in_(data.genre_ids))
        )
        movie.genres = genres.scalars().all()

    if data.star_ids is not None:
        stars = await db.execute(
            select(Star).where(Star.id.in_(data.star_ids))
        )
        movie.stars = stars.scalars().all()

    if data.director_ids is not None:
        directors = await db.execute(
            select(Director).where(Director.id.in_(data.director_ids))
        )
        movie.directors = directors.scalars().all()

    await db.commit()
    await db.refresh(movie)

    return movie


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    await db.delete(movie)
    await db.commit()
