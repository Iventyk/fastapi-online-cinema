from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.limiter import limiter
from src.crud import get_list_of_users, manual_operation
from src.databases import get_db
from src.databases.models import UserGroupEnum
from src.exceptions import (
    UserNotExist,
    UserGroupNotExist,
)
from src.schemas import (
    UserReadSchema,
    CurrentUser,
    AdminOperatedData,
)
from src.security.utils import get_current_user

account_router = APIRouter(prefix="/accounts", tags=["Accounts management"])


@account_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[UserReadSchema],
    summary="Get all accounts",
    description="Retrieve a list of all registered users. "
    "Access restricted to Moderators and Admins.",
)
@limiter.limit("20/minute")
async def get_accounts(
    request: Request,  # noqa
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[UserReadSchema]:
    if auth_user.permission not in ["moderator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect permission for current user",
        )
    try:
        result = await get_list_of_users(
            db=db,
        )
        return result
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )


@account_router.post(
    "/manual-operate/{account_id}/",
    status_code=status.HTTP_200_OK,
    response_model=UserReadSchema,
    summary="Manual account operation",
    description="Update account status or group manually. "
    "Access restricted to Admins only.",
)
@limiter.limit("20/minute")
async def manual_operate_account(
    request: Request,  # noqa
    account_id: int,
    account_data: AdminOperatedData,
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UserReadSchema:
    if auth_user.permission != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perform this action",
        )
    else:
        try:
            return await manual_operation(
                account_id=account_id,
                data=account_data,
                db=db,
            )
        except (UserNotExist, UserGroupNotExist) as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
            )
