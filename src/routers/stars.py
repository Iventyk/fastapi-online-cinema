from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.movies import Star, Movie
from src.schemas.stars import StarCreate, StarRead
from src.schemas.movies import MovieListItem

router = APIRouter(prefix="/stars", tags=["Stars"])


@router.get("", response_model=List[StarRead])
async def get_stars(db: AsyncSession = Depends(get_db)) -> List[StarRead]:
    stmt = (
        select(
            Star.id,
            Star.name,
            func.count(Movie.id).label("movies_count"),
        )
        .outerjoin(Star.movies)
        .group_by(Star.id)
        .order_by(Star.name)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [
        StarRead(
            id=row["id"],
            name=row["name"],
            movies_count=row["movies_count"],
        )
        for row in rows
    ]


@router.get("/{star_id}/movies")
async def get_star_movies(
    star_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[MovieListItem]:
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalar_one_or_none()

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star not found",
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
        for m in star.movies
    ]


@router.post(
    "",
    response_model=StarRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_star(
    data: StarCreate,
    db: AsyncSession = Depends(get_db),
) -> StarRead:
    star = Star(name=data.name)
    db.add(star)

    try:
        await db.commit()
        await db.refresh(star)
    except SQLAlchemyError:
        await db.rollback()
        raise

    return StarRead(
        id=star.id,
        name=star.name,
        movies_count=0,
    )


@router.delete(
    "/{star_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Star).where(Star.id == star_id))
    star = result.scalar_one_or_none()

    if not star:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star not found",
        )

    try:
        await db.delete(star)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise