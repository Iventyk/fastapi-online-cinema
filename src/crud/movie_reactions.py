from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from src.databases.models.movie_reactions import MovieReaction


async def set_reaction(
    db: AsyncSession,
    *,
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

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise


async def remove_reaction(
    db: AsyncSession,
    *,
    user_id: int,
    movie_id: int,
) -> bool:
    result = await db.execute(
        select(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )
    reaction = result.scalar_one_or_none()

    if not reaction:
        return False

    try:
        await db.delete(reaction)
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        raise
    return True


async def get_reactions_stats(
    db: AsyncSession,
    *,
    movie_id: int,
) -> tuple[int, int]:
    stmt = select(
        func.sum(func.case((MovieReaction.value == 1, 1), else_=0)),
        func.sum(func.case((MovieReaction.value == -1, 1), else_=0)),
    ).where(MovieReaction.movie_id == movie_id)

    result = await db.execute(stmt)
    likes, dislikes = result.one()

    return likes or 0, dislikes or 0
