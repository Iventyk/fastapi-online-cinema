from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models.movie_comments import MovieComment


async def create_comment(
    db: AsyncSession,
    *,
    movie_id: int,
    user_id: int,
    text: str,
) -> MovieComment:
    comment = MovieComment(
        movie_id=movie_id,
        user_id=user_id,
        text=text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_movie_comments(
    db: AsyncSession,
    *,
    movie_id: int,
) -> list[MovieComment]:
    result = await db.execute(
        select(MovieComment).where(MovieComment.movie_id == movie_id)
    )
    return list(result.scalars().all())


async def delete_comment(
    db: AsyncSession,
    *,
    comment_id: int,
    user_id: int,
) -> bool:
    result = await db.execute(
        select(MovieComment).where(MovieComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment or comment.user_id != user_id:
        return False

    await db.delete(comment)
    await db.commit()
    return True
