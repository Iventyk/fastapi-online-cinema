from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.schemas.movie_reactions import MovieReactionRead
from src.security.utils import get_current_user
from src.databases.models.accounts import UserModel
from src.crud import movie_reactions as crud

router = APIRouter(prefix="/movies", tags=["Movie reactions"])


@router.post("/{movie_id}/like", status_code=status.HTTP_201_CREATED)
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    await crud.set_reaction(
        db,
        user_id=user.id,
        movie_id=movie_id,
        value=1,
    )


@router.post("/{movie_id}/dislike", status_code=status.HTTP_201_CREATED)
async def dislike_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    await crud.set_reaction(
        db,
        user_id=user.id,
        movie_id=movie_id,
        value=-1,
    )


@router.delete("/{movie_id}/reaction", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    deleted = await crud.remove_reaction(
        db,
        user_id=user.id,
        movie_id=movie_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found",
        )


@router.get(
    "/{movie_id}/reactions",
    response_model=MovieReactionRead,
)
async def get_movie_reactions(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> MovieReactionRead:
    likes, dislikes = await crud.get_reactions_stats(
        db,
        movie_id=movie_id,
    )

    return MovieReactionRead(
        likes=likes,
        dislikes=dislikes,
    )
