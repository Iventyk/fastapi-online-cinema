from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.movie_reactions import MovieReaction
from src.databases.models.movies import Movie
from src.securuty.utils import get_current_user
from src.databases.models.accounts import UserModel

router = APIRouter(prefix="/movies", tags=["Movie reactions"])


@router.post("/{movie_id}/like", status_code=status.HTTP_201_CREATED)
async def like_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    await _set_reaction(db, user.id, movie_id, value=1)


@router.post("/{movie_id}/dislike", status_code=status.HTTP_201_CREATED)
async def dislike_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    await _set_reaction(db, user.id, movie_id, value=-1)


@router.delete("/{movie_id}/reaction", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(MovieReaction).where(
            MovieReaction.user_id == user.id,
            MovieReaction.movie_id == movie_id,
        )
    )
    reaction = result.scalar_one_or_none()

    if not reaction:
        raise HTTPException(
            status_code=404,
            detail="Reaction not found",
        )

    await db.delete(reaction)
    await db.commit()


@router.get("/{movie_id}/reactions")
async def get_movie_reactions(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(
            func.sum(func.case((MovieReaction.value == 1, 1), else_=0)).label("likes"),
            func.sum(func.case((MovieReaction.value == -1, 1), else_=0)).label("dislikes"),
        )
        .where(MovieReaction.movie_id == movie_id)
    )

    result = await db.execute(stmt)
    row = result.one()

    return {
        "likes": row.likes or 0,
        "dislikes": row.dislikes or 0,
    }


async def _set_reaction(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    value: int,
) -> None:
    result = await db.execute(
        select(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )
    reaction = result.scalar_one_or_none()

    if reaction:
        reaction.value = value
    else:
        db.add(
            MovieReaction(
                user_id=user_id,
                movie_id=movie_id,
                value=value,
            )
        )

    await db.commit()

