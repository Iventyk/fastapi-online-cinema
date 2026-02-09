from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.schemas.movies import (
    MovieCreate,
    MovieUpdate,
    MovieRead,
    MovieListItem,
)
from src.crud import movies as crud

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=list[MovieListItem])
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
) -> List[MovieListItem]:
    movies = await crud.get_movies(
        db,
        page=page,
        per_page=per_page,
        search=search,
        year_from=year_from,
        year_to=year_to,
        imdb_from=imdb_from,
        imdb_to=imdb_to,
        price_from=price_from,
        price_to=price_to,
        genre_id=genre_id,
        certification_id=certification_id,
        sort_by=sort_by,
        order=order,
    )

    return [MovieListItem.model_validate(m) for m in movies]


@router.get("/{movie_id}", response_model=MovieRead)
async def get_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieRead:
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    return MovieRead.model_validate(movie)


@router.post(
    "",
    response_model=MovieRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_movie(
    data: MovieCreate,
    db: AsyncSession = Depends(get_db),
) -> MovieRead:
    movie = await crud.create_movie(db, data=data)
    return MovieRead.model_validate(movie)


@router.put("/{movie_id}", response_model=MovieRead)
async def update_movie(
    movie_id: int,
    data: MovieUpdate,
    db: AsyncSession = Depends(get_db),
) -> MovieRead:
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    movie = await crud.update_movie(db, movie=movie, data=data)
    return MovieRead.model_validate(movie)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )

    await crud.delete_movie(db, movie=movie)
