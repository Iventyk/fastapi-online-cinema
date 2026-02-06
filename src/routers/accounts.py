from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import create_new_user, get_list_of_users, login_user
from src.databases import get_db
from src.config import get_jwt_manager, Settings, get_settings
from src.exceptions import BaseAccountException, IncorrectCredentials
from src.schemas import (
    UserReadSchema,
    UserCreateSchema,
    UserLoginSchema,
    LoginResponseSchema,
)
from src.securuty import JWTAuthManagerInterface
from src.services import sync_guest_cart_to_user

account_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@account_router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
)
async def create_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    user_data: UserCreateSchema,
) -> UserReadSchema:
    try:
        result = await create_new_user(
            db=db,
            jwt_manager=jwt_manager,
            user_data=user_data,
        )
        return result
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


@account_router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseSchema,
)
async def login_for_accounts(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
    login_data: UserLoginSchema,
) -> LoginResponseSchema:
    try:
        result = await login_user(
            db=db,
            jwt_manager=jwt_manager,
            settings=settings,
            login_data=login_data,
        )
        return result
    except IncorrectCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
