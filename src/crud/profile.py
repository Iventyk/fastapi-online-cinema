from typing import Annotated, Any, Coroutine

from fastapi import Form, Depends
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.databases.models import UserModel, UserProfileModel
from src.exceptions import (
    UserPermissionDenied,
    UserNotExist,
    UserAccountNotActivated,
    ProfileAlreadyExistsException,
    ProfileDoesNotExistException
)
from src.schemas import ProfileCreateSchema, CurrentUser
from src.schemas.profile import ProfileReadSchema, ProfileUpdateSchema
from src.securuty.utils import get_current_user


async def _get_profile_by_id(
        account_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> type[UserProfileModel]:
    profile = await db.get(
        UserProfileModel,
        account_id,
        options=[
            selectinload(UserProfileModel.user)
        ]
    )
    if not profile:
        raise ProfileDoesNotExistException(
            message="Account with provided id does not exist"
        )
    return profile


async def create_user_profile(
        account_id: int,
        profile_data: Annotated[ProfileCreateSchema, Form()],
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProfileReadSchema:
    if auth_user.user_id != account_id and auth_user.permission != "admin":
        raise UserPermissionDenied(
            message="You are not allowed to perform this action"
        )
    operated_acc = await db.get(
        UserModel,
        account_id,
        options=[
            selectinload(UserModel.profile)
        ]
    )
    if not operated_acc:
        raise UserNotExist(message="Account with provided id does not exist")

    if not operated_acc.is_active:
        raise UserAccountNotActivated(
            message="Account with provided id does not activated"
        )

    if operated_acc.profile:
        raise ProfileAlreadyExistsException(
            message="Account with provided id already has profile"
        )
    # picture = profile_data.picture

    # TODO Upload profile picture and return url

    db_profile = UserProfileModel(
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar="Not implemented yet",
        user=operated_acc,
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return ProfileReadSchema(
        id=db_profile.id,
        user_id=db_profile.user_id,
        first_name=db_profile.first_name,
        last_name=db_profile.last_name,
        gender=db_profile.gender,
        date_of_birth=db_profile.date_of_birth,
        info=db_profile.info,
        avatar=db_profile.avatar,
    )


async def retrieve_user_profile(
        account_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileReadSchema:
    profile = await _get_profile_by_id(account_id, db)

    return ProfileReadSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=profile.avatar,
    )


async def update_user_profile(
        account_id: int,
        profile_data: ProfileUpdateSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileReadSchema:
    profile = await _get_profile_by_id(account_id, db)

    profile_data = profile_data.model_dump(exclude_unset=True)
    for key, value in profile_data.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return ProfileReadSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=profile.avatar,
    )