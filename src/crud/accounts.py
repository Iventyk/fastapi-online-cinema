from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi.params import Depends
from pydantic import EmailStr
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
    ActivationTokenModel,
    RefreshTokenModel,
)
from src.exceptions import (
    UserAlreadyExist,
    UserGroupNotExist,
    IncorrectCredentials,
    UserNotActivated,
    UserNotExist,
)
from src.schemas import (
    UserCreateSchema,
    UserReadSchema,
    UserLoginSchema,
    LoginResponseSchema,
    CurrentUser,
    CommonResponseSchema,
    AdminOperatedData,
    RefreshTokenSchema,
    RefreshTokenResponseSchema,
)
from src.databases import get_db
from src.config import get_jwt_manager, get_settings, Settings
from src.securuty import JWTAuthManagerInterface
from src.securuty.utils import get_current_user
from src.services import sync_guest_cart_to_user
from src.tasks import (
    send_activation_email_task,
    send_activation_complete_email_task,
)


async def create_new_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    user_data: UserCreateSchema,
) -> UserReadSchema:
    existing_user = await get_user_by_email(db=db, email=user_data.email)

    if existing_user:
        raise UserAlreadyExist(
            message="User with provided email already exists"
        )

    user_dict = user_data.model_dump()

    group_name = user_dict.pop("group") or UserGroupEnum.USER
    result = await db.execute(
        select(UserGroupModel).where(UserGroupModel.name == group_name)
    )
    user_group = result.scalar_one_or_none()
    if not user_group:
        raise UserGroupNotExist(message="Provided group does not exist")

    user = await UserModel.create(
        email=user_dict["email"],
        raw_password=user_dict["password"],
        group_id=user_group.id,
    )

    db.add(user)
    await db.flush()

    token = jwt_manager.create_activation_token()
    activation_token = ActivationTokenModel.create(
        token=token,
        user_id=user.id,
    )
    db.add(activation_token)
    await db.commit()
    await db.refresh(user)

    await sync_guest_cart_to_user(
        db=db,
        user_id=user.id,
        guest_movie_ids=user_data.guest_cart_items,
    )

    activation_link = (
        f"http://127.0.0.1:8000/accounts/activate/?activation_token={token}"
    )

    send_activation_email_task.delay(
        email=user.email, activation_link=activation_link
    )

    return UserReadSchema(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
    )


async def get_user_by_email(
    db: Annotated[AsyncSession, Depends(get_db)],
    email: EmailStr,
) -> UserModel | None:
    result = await db.execute(
        select(UserModel)
        .where(UserModel.email == email)
        .options(selectinload(UserModel.group))
        .options(selectinload(UserModel.profile))
    )
    user = result.scalar_one_or_none()
    return user


async def get_list_of_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 25,
) -> list[UserReadSchema]:
    result = await db.scalars(
        select(UserModel)
        .offset(skip)
        .limit(limit)
        .options(selectinload(UserModel.group))
    )
    users = result.all()
    return [UserReadSchema.model_validate(user) for user in users]


async def login_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
    login_data: UserLoginSchema,
) -> LoginResponseSchema:
    email = login_data.email
    user = await get_user_by_email(db=db, email=email)
    if not user:
        raise IncorrectCredentials(message="Incorrect credentials")

    password = login_data.password
    if not user.check_password(password):
        raise IncorrectCredentials(message="Incorrect credentials")

    if not user.is_active:
        raise UserNotActivated(message="User not activated")

    token_data = {
        "user_id": user.id,
        "email": user.email,
    }
    access_token = jwt_manager.create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=settings.ACCESS_KEY_TIMEDELTA_MINUTES),
    )
    refresh_token = jwt_manager.create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_DAYS),
    )

    db_token = RefreshTokenModel.create(
        token=refresh_token,
        user_id=user.id,
    )
    db.add(db_token)
    await db.commit()

    await sync_guest_cart_to_user(
        db=db,
        user_id=user.id,
        guest_movie_ids=login_data.guest_cart_items,
    )

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


async def activate_user(
    activation_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CommonResponseSchema:
    stmt = (
        select(ActivationTokenModel)
        .options(selectinload(ActivationTokenModel.user))
        .where(ActivationTokenModel.token == activation_token)
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise IncorrectCredentials(message="Invalid activation token")

    user = token_record.user

    if user.is_active:
        await db.delete(token_record)
        await db.commit()
        return CommonResponseSchema(message="User already activated")

    if (
        token_record.expires_at.timestamp()
        < datetime.now(timezone.utc).timestamp()
    ):
        raise IncorrectCredentials(message="Activation token has expired")

    user.is_active = True
    await db.delete(token_record)
    await db.commit()

    login_link = "http://127.0.0.1:8000/accounts/login/"

    send_activation_complete_email_task.delay(
        email=user.email, login_link=login_link
    )

    return CommonResponseSchema(
        message="Successfully activate your account",
    )


async def reactivate_user_token(
    user_data: UserLoginSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
) -> CommonResponseSchema:
    user = await get_user_by_email(db=db, email=user_data.email)

    generic_msg = (
        "If the account exists and is not active, a new link has been sent."
    )

    if not user:
        return CommonResponseSchema(message=generic_msg)

    if user.is_active:
        return CommonResponseSchema(message="User already activated")

    if not user.check_password(user_data.password):
        return CommonResponseSchema(message="Invalid credentials")

    stmt = delete(ActivationTokenModel).where(
        ActivationTokenModel.user_id == user.id
    )
    await db.execute(stmt)

    new_token = jwt_manager.create_activation_token()
    recorded_token = ActivationTokenModel.create(
        token=new_token,
        user_id=user.id,
    )
    db.add(recorded_token)

    await db.commit()

    activation_link = (
        f"http://127.0.0.1:8000/accounts/activate/"
        f"?activation_token={new_token}"
    )

    send_activation_email_task.delay(
        email=user.email, activation_link=activation_link
    )

    return CommonResponseSchema(message=generic_msg)


async def logout_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    auth_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CommonResponseSchema:
    stmt = delete(RefreshTokenModel).where(
        RefreshTokenModel.user_id == auth_user.user_id
    )

    await db.execute(stmt)
    await db.commit()

    return CommonResponseSchema(
        message="Successfully logged out from all devices",
    )


async def manual_operation(
    account_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    data: AdminOperatedData,
) -> UserReadSchema:
    account_to_operate = await db.get(
        UserModel, account_id, options=[joinedload(UserModel.group)]
    )

    if not account_to_operate:
        raise UserNotExist(message="Account with provided id does not exist")

    if data.activation and not account_to_operate.is_active:
        account_to_operate.is_active = True

    if data.permission and account_to_operate.group.name != data.permission:
        group = await db.scalar(
            select(UserGroupModel).where(
                UserGroupModel.name == data.permission
            )
        )
        if not group:
            raise UserGroupNotExist(message="Permission does not exist")
        account_to_operate.group = group
    await db.commit()
    return UserReadSchema(
        id=account_to_operate.id,
        email=account_to_operate.email,
        is_active=account_to_operate.is_active,
        permission=account_to_operate.group.name,
    )


async def refresh_token(
    token: RefreshTokenSchema,
    jwt_manager: Annotated[JWTAuthManagerInterface, Depends(get_jwt_manager)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshTokenResponseSchema:
    payload = jwt_manager.decode_refresh_token(token.refresh_token)

    user_id = payload.get("user_id")
    email = payload.get("email")

    if not user_id or not email:
        raise IncorrectCredentials(message="Invalid token credentials")

    new_token = jwt_manager.create_access_token(
        data={
            "user_id": user_id,
            "email": email,
        },
        expires_delta=timedelta(minutes=settings.ACCESS_KEY_TIMEDELTA_MINUTES),
    )

    return RefreshTokenResponseSchema(access_token=new_token)
