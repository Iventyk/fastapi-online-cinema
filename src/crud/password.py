from typing import Annotated

from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.crud.accounts import get_user_by_email
from src.databases import get_db
from src.config import get_jwt_manager
from src.databases.models import PasswordResetTokenModel, UserModel
from src.exceptions import UserAccountNotActivated, PasswordChangeError, \
    IncorrectCredentials
from src.schemas import CurrentUser, CommonResponseSchema, \
    ChangePasswordSchema, ResetPasswordRequestSchema
from src.securuty import JWTAuthManagerInterface
from src.securuty.utils import get_current_user


async def do_pswd_restore_request(
        db: Annotated[AsyncSession, Depends(get_db)],
        email: EmailStr,
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)
        ],
) -> CommonResponseSchema:
    user = await get_user_by_email(db=db, email=email)

    success_msg = ("If an account with this email exists, "
                   "a reset link has been sent.")

    if not user or not user.is_active:
        return CommonResponseSchema(message=success_msg)

    await db.execute(
        delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id)
    )

    new_token = jwt_manager.create_reset_token()
    reset_token_record = PasswordResetTokenModel.create(
        user_id=user.id,
        token=new_token,
    )

    db.add(reset_token_record)
    await db.commit()

    # TODO: BackgroundTasks: Send Email
    # send_reset_email(user.email, new_token)

    return CommonResponseSchema(message=success_msg)


async def change_password(
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        new_password: ChangePasswordSchema,
) -> CommonResponseSchema:
    user = await db.get(UserModel, auth_user.user_id)

    if not user.check_password(password=new_password.old_password):
        raise PasswordChangeError("Incorrect password")

    try:
        user.password = new_password.new_password
        await db.commit()
    except SQLAlchemyError:
        raise PasswordChangeError("Incorrect password")

    return CommonResponseSchema(
        message="Password has been changed successfully",
    )

async def do_pswd_reset_confirm(
        data: ResetPasswordRequestSchema,
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    smtp = await db.execute(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.token == data.token)
        .options(joinedload(PasswordResetTokenModel.user))
    )
    existing_token = smtp.scalar_one_or_none()
    if not existing_token:
        raise IncorrectCredentials(message="Incorrect Token")

    user = await db.get(UserModel, existing_token.user_id)

    user.password = data.password
    await db.commit()
    return CommonResponseSchema(
        message="User password has been restored successfully",
    )