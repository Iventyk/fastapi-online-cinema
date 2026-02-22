from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from src.databases.dev_engine import get_db
from src.databases.models.movies import Director, Movie
from src.schemas.directors import DirectorCreate, DirectorRead
from src.schemas.movies import MovieListItem

router = APIRouter(prefix="/directors", tags=["Directors"])


@router.get(
    "",
    response_model=List[DirectorRead],
    summary="Get all directors",
    description="Returns all directors with the number of associated movies.",
    responses={
        200: {"description": "List of directors"},
    },
)
async def get_directors(
    db: AsyncSession = Depends(get_db),
) -> List[DirectorRead]:
    stmt = (
        select(
            Director.id,
            Director.name,
            func.count(Movie.id).label("movies_count"),
        )
        .outerjoin(Director.movies)
        .group_by(Director.id)
        .order_by(Director.name)
    )

    result = await db.execute(stmt)
    rows = result.mappings().all()
    return [
        DirectorRead(
            id=row["id"],
            name=row["name"],
            movies_count=row["movies_count"],
        )
        for row in rows
    ]


@router.get(
    "/{director_id}/movies",
    response_model=List[MovieListItem],
    summary="Get movies by director",
    description="Returns all movies created by a specific director.",
    responses={
        200: {"description": "List of movies"},
        404: {"description": "Director not found"},
    },
)
async def get_director_movies(
    director_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[MovieListItem]:
    result = await db.execute(
        select(Director).where(Director.id == director_id)
    )
    director = result.scalar_one_or_none()

    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found",
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
        for m in director.movies
    ]


@router.post(
    "",
    response_model=DirectorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create director",
    description="Creates a new director.",
    responses={
        201: {"description": "Director successfully created"},
        422: {"description": "Validation error"},
    },
)
async def create_director(
    data: DirectorCreate,
    db: AsyncSession = Depends(get_db),
) -> DirectorRead:
    director = Director(name=data.name)
    db.add(director)

    try:
        await db.commit()
        await db.refresh(director)
    except SQLAlchemyError:
        await db.rollback()
        raise

    return DirectorRead(
        id=director.id,
        name=director.name,
        movies_count=0,
    )


@router.delete(
    "/{director_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete director",
    description="Deletes a director by ID.",
    responses={
        204: {"description": "Director deleted"},
        404: {"description": "Director not found"},
    },
)
async def delete_director(
    director_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(Director).where(Director.id == director_id)
    )
    director = result.scalar_one_or_none()

    if not director:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Director not found",
        )

    try:
        await db.delete(director)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
