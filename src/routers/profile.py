from typing import Annotated

from fastapi import APIRouter, status, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_user_profile,
    retrieve_user_profile,
    update_user_profile,
)
from src.crud.profile import delete_profile
from src.databases import get_db
from src.exceptions import (
    UserPermissionDenied,
    UserNotExist,
    UserAccountNotActivated,
    ProfileAlreadyExistsException,
    ProfileDoesNotExistException,
)
from src.schemas import (
    CurrentUser,
    ProfileReadSchema,
    ProfileCreateSchema,
    ProfileUpdateSchema, CommonResponseSchema,
)
from src.securuty.utils import get_current_user
from src.storage import S3StorageInterface
from src.config import get_storage

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.post(
    "/create/{account_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=ProfileReadSchema,
)
async def create_profile(
        account_id: int,
        profile_data: Annotated[ProfileCreateSchema, Form()],
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        s3_storage: Annotated[S3StorageInterface, Depends(get_storage)],
) -> ProfileReadSchema:
    try:
        return await create_user_profile(
            account_id=account_id,
            profile_data=profile_data,
            db=db,
            auth_user=auth_user,
            s3_storage=s3_storage,
        )
    except UserPermissionDenied as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )
    except UserNotExist as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        )
    except UserAccountNotActivated as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(error)
        )
    except ProfileAlreadyExistsException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )


@profile_router.get(
    "/{account_id}",
    response_model=ProfileReadSchema,
    status_code=status.HTTP_200_OK,
)
async def get_profile(
        account_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ProfileReadSchema:
    if auth_user.profile_id != account_id and auth_user.permission not in [
        "moderator",
        "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile",
        )
    try:
        return await retrieve_user_profile(account_id=account_id, db=db)
    except ProfileDoesNotExistException as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        )


@profile_router.put(
    "/{account_id}",
    response_model=ProfileReadSchema,
    status_code=status.HTTP_200_OK,
)
async def update_profile(
        account_id: int,
        profile_data: Annotated[ProfileUpdateSchema, Form()],
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        s3_storage: Annotated[S3StorageInterface, Depends(get_storage)],
) -> ProfileReadSchema:
    if auth_user.profile_id != account_id and auth_user.permission not in [
        "moderator",
        "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile",
        )

    return await update_user_profile(
        account_id=account_id,
        profile_data=profile_data,
        db=db,
        s3_storage=s3_storage
    )


@profile_router.patch(
    "/{account_id}",
    response_model=ProfileReadSchema,
    status_code=status.HTTP_200_OK,
)
async def partial_update_profile(
        account_id: int,
        profile_data: Annotated[ProfileUpdateSchema, Form()],
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        s3_storage: Annotated[S3StorageInterface, Depends(get_storage)],
) -> ProfileReadSchema:
    if auth_user.profile_id != account_id and auth_user.permission not in [
        "moderator",
        "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile",
        )

    return await update_user_profile(
        account_id=account_id,
        profile_data=profile_data,
        db=db,
        s3_storage=s3_storage
    )
@profile_router.delete(
    "/{account_id}",
    response_model=CommonResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_user_profile(
        account_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CommonResponseSchema:
    if auth_user.profile_id != account_id and auth_user.permission not in [
        "moderator", "admin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this profile",
        )
    try:
        return await delete_profile(account_id=account_id, db=db)
    except ProfileDoesNotExistException as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        )