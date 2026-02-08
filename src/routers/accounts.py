from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Request
from fastapi.params import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import (
    create_new_user,
    login_user,
    logout_user,
    activate_user,
    reactivate_user_token,
    refresh_token,
)
from src.databases import get_db
from src.config import get_jwt_manager, Settings, get_settings
from src.exceptions import (
    BaseAccountException,
    IncorrectCredentials,
    TokenExpiredError,
    InvalidTokenError,
    UserNotExist,

    UserNotActivated,
)
from src.schemas import (
    UserReadSchema,
    UserCreateSchema,
    UserLoginSchema,
    LoginResponseSchema,
    CommonResponseSchema,
    CurrentUser,
    RefreshTokenResponseSchema,
    RefreshTokenSchema
)
from src.securuty import JWTAuthManagerInterface
from src.securuty.utils import get_current_user
from src.config.limiter import limiter

auth_router = APIRouter(prefix="/accounts", tags=["Auth"])


@auth_router.post(
    "/register/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserReadSchema,
    summary="Register a new user",
    description="Create a new account and trigger an activation email."
)
@limiter.limit("5/minute")
async def create_account(
        request: Request,  # noqa
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


@auth_router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponseSchema,
    summary="User Login",
    description="Authenticate user and return access and refresh tokens."
)
@limiter.limit("5/minute")
async def login_for_accounts(
        request: Request,  # noqa
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


@auth_router.get(
    "/logout/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Logout User",
    description="Invalidate the user's current session and refresh token."
)
@limiter.limit("10/minute")
async def logout_account(
        request: Request,  # noqa
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CommonResponseSchema:
    try:
        result = await logout_user(db=db, auth_user=auth_user)
        return result
    except (TokenExpiredError, InvalidTokenError, UserNotExist):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired",
        )
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        )


@auth_router.post(
    "/refresh-token/",
    status_code=status.HTTP_200_OK,
    response_model=RefreshTokenResponseSchema,
    summary="Refresh Access Token",
    description="Get a new access token using a valid refresh token."
)
@limiter.limit("5/minute")
async def refresh_account_token(
        request: Request,  # noqa
        token: RefreshTokenSchema,
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)],
        settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshTokenResponseSchema:
    try:
        return await refresh_token(
            token=token,
            jwt_manager=jwt_manager,
            settings=settings,
        )
    except (TokenExpiredError, InvalidTokenError, IncorrectCredentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired",
        )


@auth_router.get(
    "/activate/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Activate Account",
    description="Verify email and activate user account via token."
)
@limiter.limit("1/minute")
async def activate_account(
        request: Request,  # noqa
        activation_token: str,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    try:
        result = await activate_user(
            activation_token=activation_token,
            db=db,
        )
        return result
    except (TokenExpiredError, InvalidTokenError, UserNotExist):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired",
        )
    except IncorrectCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )


@auth_router.post(
    "/reactivate-account/",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Resend Activation Email",
    description="Request a new activation token if the previous one expired."
)
@limiter.limit("1/minute")
async def reactivate_account(
        request: Request,  # noqa
        user_data: UserLoginSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> CommonResponseSchema:
    result = await reactivate_user_token(
        db=db,
        user_data=user_data,
        jwt_manager=jwt_manager,
    )
    return result
