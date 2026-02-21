from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.dev_engine import get_db
from src.schemas.movie_comments import CommentCreate, CommentRead
from src.security.utils import get_current_user
from src.databases.models.accounts import UserModel
from src.crud import movie_comments as crud

router = APIRouter(prefix="/movies", tags=["Comments"])


@router.post(
    "/{movie_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to movie",
    description="Adds a new comment to a movie. Requires authentication.",
    responses={
        201: {"description": "Comment successfully created"},
        401: {"description": "Unauthorized"},
        404: {"description": "Movie not found"},
        422: {"description": "Validation error"},
    },
)
async def add_comment(
    movie_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> CommentRead:
    comment = await crud.create_comment(
        db,
        movie_id=movie_id,
        user_id=user.id,
        text=data.text,
    )
    return CommentRead.model_validate(comment)


@router.get(
    "/{movie_id}/comments",
    response_model=List[CommentRead],
    summary="Get movie comments",
    description="Returns all comments for a specific movie.",
    responses={
        200: {"description": "List of comments"},
        404: {"description": "Movie not found"},
    },
)
async def get_comments(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[CommentRead]:
    comments = await crud.get_movie_comments(
        db,
        movie_id=movie_id,
    )
    return [CommentRead.model_validate(c) for c in comments]


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="Deletes a user's own comment.",
    responses={
        204: {"description": "Comment deleted"},
        401: {"description": "Unauthorized"},
        404: {"description": "Comment not found"},
    },
)
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: UserModel = Depends(get_current_user),
) -> None:
    deleted = await crud.delete_comment(
        db,
        comment_id=comment_id,
        user_id=user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
