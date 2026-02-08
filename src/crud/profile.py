from typing import Annotated, Any, Coroutine
from uuid import uuid4

from fastapi import Form, Depends
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


from src.databases import get_db
from src.config import get_storage
from src.databases.models import UserModel, UserProfileModel
from src.exceptions import (
    UserPermissionDenied,
    UserNotExist,
    UserAccountNotActivated,
    ProfileAlreadyExistsException,
    ProfileDoesNotExistException,
)
from src.schemas import ProfileCreateSchema, CurrentUser
from src.schemas.profile import ProfileReadSchema, ProfileUpdateSchema
from src.securuty.utils import get_current_user
from src.storage import S3StorageInterface


async def _get_profile_by_id(
    account_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProfileModel:
    profile = await db.get(
        UserProfileModel,
        account_id,
        options=[selectinload(UserProfileModel.user)],
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
    s3_storage: Annotated[S3StorageInterface, Depends(get_storage)],
) -> ProfileReadSchema:
    if auth_user.user_id != account_id and auth_user.permission != "admin":
        raise UserPermissionDenied(
            message="You are not allowed to perform this action"
        )
    operated_acc = await db.get(
        UserModel, account_id, options=[selectinload(UserModel.profile)]
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
    avatar_url = "Undefined"
    picture = profile_data.avatar
    if picture:
        file_data = await picture.read()
        file_name = f"avatar/{uuid4()}_{picture.filename}"

        await s3_storage.upload_file(
            file_name=file_name,
            file_data=file_data,
            content_type=picture.content_type,  # type: ignore[arg-type]
        )

        avatar_url = await s3_storage.get_file_url(file_name=file_name)

    db_profile = UserProfileModel(
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=profile_data.gender,
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar=avatar_url,
        user=operated_acc,
    )
    db.add(db_profile)
    await db.commit()
    await db.refresh(db_profile)
    return ProfileReadSchema.model_validate(db_profile)


async def retrieve_user_profile(
    account_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileReadSchema:
    profile = await _get_profile_by_id(account_id, db)

    return ProfileReadSchema.model_validate(profile)


async def update_user_profile(
    account_id: int,
    profile_data: ProfileUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProfileReadSchema:
    profile = await _get_profile_by_id(account_id, db)

    update_dict = profile_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return ProfileReadSchema.model_validate(profile)
