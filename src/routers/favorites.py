from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.favorites import Favorite
from src.databases.models.movies import Movie
from src.schemas.movies import MovieListItem
from src.securuty.utils import get_current_user
from src.databases.models.accounts import UserModel

router = APIRouter(prefix="/favorites", tags=["Favorites"])

@router.post("/{movie_id}", status_code=status.HTTP_201_CREATED)
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
    await db.commit()


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
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

    await db.delete(favorite)
    await db.commit()


@router.get("", response_model=List[MovieListItem])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> List[MovieListItem]:
    stmt = (
        select(Movie)
        .join(Favorite)
        .where(Favorite.user_id == user.id)
    )

    result = await db.execute(stmt)
    return result.scalars().all()
