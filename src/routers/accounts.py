from typing import Annotated

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_new_user,
    get_list_of_users,
    login_user,
    logout_user,
    do_pswd_restore_request,
    activate_user,
    reactivate_user_token,
    change_password, do_pswd_reset_confirm, manual_operation,
)
from src.databases import get_db
from src.config import get_jwt_manager, Settings, get_settings
from src.databases.models import UserGroupEnum
from src.exceptions import (
    BaseAccountException,
    IncorrectCredentials,
    TokenExpiredError,
    InvalidTokenError,
    UserNotExist,
    UserAccountNotActivated,
    UserNotActivated,
    PasswordChangeError,
)
from src.schemas import (
    UserReadSchema,
    UserCreateSchema,
    UserLoginSchema,
    LoginResponseSchema,
    CommonResponseSchema,
    CurrentUser,
    ChangePasswordSchema, ResetPasswordRequestSchema, ForgotPasswordSchema,
    AdminOperatedData,
)
from src.securuty import JWTAuthManagerInterface
from src.services import sync_guest_cart_to_user
from src.securuty.utils import get_current_user

account_router = APIRouter(prefix="/accounts", tags=["Accounts"])


@account_router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
    tags=["Account management"],
)
async def create_account(
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)],
        user_data: UserCreateSchema,
) -> UserReadSchema:
    try:
        return await create_new_user(
            db=db,
            jwt_manager=jwt_manager,
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
    "/login/",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseSchema,
)
async def login_for_accounts(
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)],
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
    except UserNotActivated as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(error)
        )


@account_router.get(
    "/activate/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    tags=["Account management"],
)
async def activate_account(
        activation_token: str,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    try:
        result = await activate_user(
            activation_token=activation_token,
            db=db,
        )
        return result
    except (TokenExpiredError, InvalidTokenError, UserNotExist) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired"
        )
    except IncorrectCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )


@account_router.post(
    "/reactivate-account/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    tags=["Account management"],
)
async def reactivate_account(
        user_data: UserLoginSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)
        ],
) -> CommonResponseSchema:
    result = await reactivate_user_token(
        db=db,
        user_data=user_data,
        jwt_manager=jwt_manager,
    )
    return result


@account_router.get(
    "/logout/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema
)
async def logout_account(
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> CommonResponseSchema:
    try:
        result = await logout_user(db=db, auth_user=auth_user)
        return result
    except (TokenExpiredError, InvalidTokenError, UserNotExist):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired"
        )
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )


@account_router.post(
    "/change_password/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    tags=["Password management"],
)
async def change_account_password(
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        new_password: ChangePasswordSchema,
) -> CommonResponseSchema:
    try:
        result = await change_password(
            db=db,
            auth_user=auth_user,
            new_password=new_password
        )
        return result
    except PasswordChangeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@account_router.post(
    "/password-reset/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    tags=["Password management"],
)
async def reset_password(
        data: ForgotPasswordSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)
        ],
) -> CommonResponseSchema:
    return await do_pswd_restore_request(
        email=data.email,
        db=db,
        jwt_manager=jwt_manager,
    )


@account_router.post(
    "/reset-password/confirm/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    tags=["Password management"],
)
async def reset_password(
        data: ResetPasswordRequestSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    try:
        return await do_pswd_reset_confirm(data=data, db=db)
    except IncorrectCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@account_router.post(
    "/manual-operate/{account_id}/",
    status_code=status.HTTP_200_OK,
    response_model=UserReadSchema,
)
async def manual_operate_account(
        account_id: int,
        account_data: AdminOperatedData,
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UserReadSchema:
    if auth_user.permission != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to perform this action"
        )
    else:
        try:
            return await manual_operation(
                account_id=account_id,
                data=account_data,
                db=db,
            )
        except UserNotExist as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error)
            )