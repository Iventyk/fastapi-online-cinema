from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from src.databases.dev_engine import get_db
from src.databases.models.favorites import Favorite
from src.databases.models.movies import Movie
from src.schemas.movies import MovieListItem
from src.security.utils import get_current_user
from src.databases.models.accounts import UserModel

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.post(
    "/{movie_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to favorites",
    description="Adds a movie to the authenticated user's favorites.",
    responses={
        201: {"description": "Movie added to favorites"},
        400: {"description": "Movie already in favorites"},
        401: {"description": "Unauthorized"},
    },
)
async def add_to_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    exists = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.movie_id == movie_id,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in favorites",
        )

    db.add(Favorite(user_id=user.id, movie_id=movie_id))

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove movie from favorites",
    description="Removes a movie from the authenticated user's favorites list.",
    responses={
        204: {"description": "Movie successfully removed from favorites"},
        401: {"description": "Unauthorized"},
        404: {"description": "Favorite not found"},
        500: {"description": "Database error"},
    },
)
async def remove_from_favorites(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == user.id,
            Favorite.movie_id == movie_id,
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found",
        )

    try:
        await db.delete(favorite)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise


@router.get(
    "",
    response_model=List[MovieListItem],
    summary="Get user favorites",
    description="Returns all favorite movies of the authenticated user.",
    responses={
        200: {"description": "List of favorite movies"},
        401: {"description": "Unauthorized"},
    },
)
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> List[MovieListItem]:
    stmt = select(Movie).join(Favorite).where(Favorite.user_id == user.id)

    result = await db.execute(stmt)
    movies = result.scalars().all()

    return [MovieListItem.model_validate(movie) for movie in movies]
