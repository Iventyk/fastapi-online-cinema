from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import create_new_user, get_list_of_users
from src.databases import get_db
from src.exceptions import BaseAccountException
from src.schemas import UserReadSchema, UserCreateSchema

account_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@account_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
)
async def create_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_data: UserCreateSchema,
) -> UserReadSchema:
    try:
        return await create_new_user(
            db=db,
            user_data=user_data,
        )
    except BaseAccountException as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )


@account_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[UserReadSchema],
)
async def get_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserReadSchema]:
    try:
        result = await get_list_of_users(
            db=db,
        )
        return result
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
