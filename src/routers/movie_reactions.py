from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.schemas.movie_reactions import MovieReactionRead
from src.security.utils import get_current_user
from src.databases.models.accounts import UserModel
from src.crud import movie_reactions as crud

router = APIRouter(prefix="/movies", tags=["Movie reactions"])


@router.post(
    "/{movie_id}/like",
    status_code=status.HTTP_201_CREATED,
    summary="Like a movie",
    description="Sets user's reaction to LIKE (+1)."
    " If reaction exists, it will be updated.",
    responses={
        201: {"description": "Movie liked"},
        401: {"description": "Unauthorized"},
        404: {"description": "Movie not found"},
    },
)
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


@router.post(
    "/{movie_id}/dislike",
    status_code=status.HTTP_201_CREATED,
    summary="Dislike a movie",
    description="Sets user's reaction to DISLIKE (-1)."
    "If reaction exists, it will be updated.",
    responses={
        201: {"description": "Movie disliked"},
        401: {"description": "Unauthorized"},
        404: {"description": "Movie not found"},
    },
)
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


@router.delete(
    "/{movie_id}/reaction",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove movie reaction",
    description="Removes user's reaction (like/dislike) from a movie.",
    responses={
        204: {"description": "Reaction removed"},
        401: {"description": "Unauthorized"},
        404: {"description": "Reaction not found"},
    },
)
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
    summary="Get movie reactions statistics",
    description="Returns total likes and dislikes for a movie.",
    responses={
        200: {"description": "Reaction statistics"},
        404: {"description": "Movie not found"},
    },
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
