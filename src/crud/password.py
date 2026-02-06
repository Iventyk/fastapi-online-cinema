from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases import get_db
from src.config import get_jwt_manager
from src.databases.models import PasswordResetTokenModel, UserModel
from src.exceptions import UserAccountNotActivated, PasswordChangeError
from src.schemas import CurrentUser, CommonResponseSchema, ChangePasswordSchema
from src.securuty import JWTAuthManagerInterface
from src.securuty.utils import get_current_user


async def do_pswd_restore_request(
        db: Annotated[AsyncSession, Depends(get_db)],
        auth_user: Annotated[CurrentUser, Depends(get_current_user)],
        jwt_manager: Annotated[
            JWTAuthManagerInterface, Depends(get_jwt_manager)
        ],
) -> CommonResponseSchema:
    if not auth_user.is_active:
        raise UserAccountNotActivated(message="User account is not activated")

    smtp = await db.execute(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.user_id == auth_user.user_id)
    )
    old_token = smtp.scalar_one_or_none()
    if old_token:
        await db.delete(old_token)
        await db.flush()

    new_token = jwt_manager.create_reset_token()

    reset_token = PasswordResetTokenModel.create(
        user_id=auth_user.user_id,
        token=new_token,
    )

    db.add(reset_token)
    await db.commit()

    # TODO Send reset password email

    return CommonResponseSchema(
        message="Password reset token has been sent successfully",
    )


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
        db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    pass