from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.limiter import limiter
from src.crud import (
    do_pswd_restore_request,
    change_password,
    do_pswd_reset_confirm,
)
from src.databases import get_db
from src.config import get_jwt_manager
from src.exceptions import (
    IncorrectCredentials,
    UserNotExist,
    PasswordChangeError,
)
from src.schemas import (
    CommonResponseSchema,
    CurrentUser,
    ChangePasswordSchema,
    ResetPasswordRequestSchema,
    ForgotPasswordSchema,
)
from src.securuty import JWTAuthManagerInterface
from src.securuty.utils import get_current_user

password_router = APIRouter(prefix="/password", tags=["Password management"])


@password_router.post(
    "/change",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Change current password",
    description="Updates the password for the currently authenticated user. "
                "Requires the old password for verification."
)
@limiter.limit("1/minute")
async def change_account_password(
        request: Request, # noqa
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        new_password: ChangePasswordSchema,
) -> CommonResponseSchema:
    try:
        result = await change_password(
            db=db, auth_user=auth_user, new_password=new_password
        )
        return result
    except PasswordChangeError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
    except UserNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect provided JWT Token or it expired",
        )


@password_router.post(
    "/reset",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Request password reset",
    description="Triggers a password reset process by sending a temporary "
                "secure token to the user's email."
)
@limiter.limit("1/minute")
async def reset_password(
        request: Request, # noqa
        data: ForgotPasswordSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> CommonResponseSchema:
    return await do_pswd_restore_request(
        email=data.email,
        db=db,
        jwt_manager=jwt_manager,
    )


@password_router.post(
    "/reset-confirm",
    status_code=status.HTTP_200_OK,
    response_model=CommonResponseSchema,
    summary="Confirm password reset",
    description="Sets a new password using a secure token received via email."
)
@limiter.limit("1/minute")
async def confirm_reset_password(
        request: Request, # noqa
        data: ResetPasswordRequestSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    try:
        return await do_pswd_reset_confirm(data=data, db=db)
    except (IncorrectCredentials, UserNotExist) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        )
