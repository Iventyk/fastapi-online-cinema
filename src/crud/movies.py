from typing import Annotated

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db

from src.databases.models.movies import Rating
from src.schemas import CurrentUser
from src.schemas.movies import RateMovieSchema, ReadMovieRatingSchema, MovieAverageRatingSchema
from src.validators import (
    validate_movie,
)
from src.securuty.utils import get_current_user


async def rate_movie(
        movie_id: int,
        rate_data: RateMovieSchema,
        authenticated_user: Annotated[CurrentUser, Depends(get_current_user)],
        db: AsyncSession = Depends(get_db),
) -> ReadMovieRatingSchema:
    await validate_movie(db=db, movie_id=movie_id)

    query = select(Rating).where(
        Rating.user_id == authenticated_user.user_id,
        Rating.movie_id == movie_id
    )
    result = await db.execute(query)
    existing_rating = result.scalar_one_or_none()

    if existing_rating:
        if existing_rating.value != rate_data.value:
            existing_rating.value = rate_data.value
            await db.commit()
            await db.refresh(existing_rating)

        return ReadMovieRatingSchema.model_validate(existing_rating)

    else:
        new_rating_obj = Rating(
            user_id=authenticated_user.user_id,
            movie_id=movie_id,
            value=rate_data.value
        )
        db.add(new_rating_obj)
        await db.commit()
        await db.refresh(new_rating_obj)

        return ReadMovieRatingSchema.model_validate(new_rating_obj)


async def get_movie_rating(
        movie_id: int,
        authenticated_user: CurrentUser,
        db: AsyncSession,
) -> MovieAverageRatingSchema:
    await validate_movie(db=db, movie_id=movie_id)

    user_rating_query = select(Rating.value).where(
        Rating.user_id == authenticated_user.user_id,
        Rating.movie_id == movie_id
    )
    user_rating_result = await db.execute(user_rating_query)
    user_value = user_rating_result.scalar_one_or_none()

    stats_query = select(
        func.avg(Rating.value).label("average"),
        func.count(Rating.id).label("count")
    ).where(Rating.movie_id == movie_id)

    stats_result = await db.execute(stats_query)
    stats = stats_result.one()

    avg_val = round(float(stats.average), 1) if stats.average is not None else 0

    return MovieAverageRatingSchema(
        average=avg_val,
        count=stats.count,
        user_value=user_value
    )
