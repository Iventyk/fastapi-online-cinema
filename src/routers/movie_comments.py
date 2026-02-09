from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.databases.models.movie_comments import MovieComment
from src.schemas.movie_comments import CommentCreate, CommentRead
from src.securuty.utils import get_current_user
from src.databases.models.accounts import UserModel

router = APIRouter(prefix="/movies", tags=["Comments"])


@router.post("/{movie_id}/comments", response_model=CommentRead)
async def add_comment(
    movie_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> CommentRead:
    comment = MovieComment(
        movie_id=movie_id,
        user_id=user.id,
        text=data.text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentRead.model_validate(comment)


@router.get("/{movie_id}/comments", response_model=List[CommentRead])
async def get_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[CommentRead]:
    result = await db.execute(
        select(MovieComment).where(MovieComment.movie_id == movie_id)
    )
    comments = result.scalars().all()
    return [CommentRead.model_validate(c) for c in comments]


@router.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    result = await db.execute(
        select(MovieComment).where(MovieComment.id == comment_id)
    )
    comment = result.scalar_one_or_none()

    if not comment or comment.user_id != user.id:
        raise HTTPException(status_code=404)

    await db.delete(comment)
    await db.commit()
