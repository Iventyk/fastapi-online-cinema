from datetime import timedelta
from typing import Annotated

from fastapi.params import Depends
from pydantic import EmailStr
from pydantic_settings import BaseSettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload
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
    UserNotExist,
    IncorrectCredentials,
)
from src.schemas import (
    UserCreateSchema,
    UserReadSchema,
    UserLoginSchema,
    LoginResponseSchema,
)
from src.databases import get_db
from src.config import get_jwt_manager, get_settings, Settings
from src.securuty import JWTAuthManagerInterface
from src.services import sync_guest_cart_to_user


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
    # TODO Future refractor onto celery task: send_activation_email

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
