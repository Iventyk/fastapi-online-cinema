from typing import Optional

from sqlalchemy import select, or_, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.movies import Movie, Genre, Star, Director
from src.schemas.movies import MovieCreate, MovieUpdate

async def get_movies(
    db: AsyncSession,
    *,
    page: int,
    per_page: int,
    search: Optional[str],
    year_from: Optional[int],
    year_to: Optional[int],
    imdb_from: Optional[float],
    imdb_to: Optional[float],
    price_from: Optional[float],
    price_to: Optional[float],
    genre_id: Optional[int],
    certification_id: Optional[int],
    sort_by: Optional[str],
    order: str,
) -> list[Movie]:
    stmt = select(Movie).distinct()

    if search:
        stmt = (
            stmt.outerjoin(Movie.directors)
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


async def get_movie_by_id(
    db: AsyncSession,
    *,
    movie_id: int,
) -> Movie | None:
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    return result.scalar_one_or_none()



async def create_movie(
    db: AsyncSession,
    *,
    data: MovieCreate,
) -> Movie:
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
        movie.genres = list(genres.scalars())

    if data.star_ids:
        stars = await db.execute(
            select(Star).where(Star.id.in_(data.star_ids))
        )
        movie.stars = list(stars.scalars())

    if data.director_ids:
        directors = await db.execute(
            select(Director).where(Director.id.in_(data.director_ids))
        )
        movie.directors = list(directors.scalars())

    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie


async def update_movie(
    db: AsyncSession,
    *,
    movie: Movie,
    data: MovieUpdate,
) -> Movie:
    for field, value in data.model_dump(exclude_unset=True).items():
        if field.endswith("_ids"):
            continue
        setattr(movie, field, value)

    if data.genre_ids is not None:
        genres = await db.execute(
            select(Genre).where(Genre.id.in_(data.genre_ids))
        )
        movie.genres = list(genres.scalars())

    if data.star_ids is not None:
        stars = await db.execute(
            select(Star).where(Star.id.in_(data.star_ids))
        )
        movie.stars = list(stars.scalars())

    if data.director_ids is not None:
        directors = await db.execute(
            select(Director).where(Director.id.in_(data.director_ids))
        )
        movie.directors = list(directors.scalars())

    await db.commit()
    await db.refresh(movie)
    return movie


async def delete_movie(
    db: AsyncSession,
    *,
    movie: Movie,
) -> None:
    await db.delete(movie)
    await db.commit()
