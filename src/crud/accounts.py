from typing import Annotated

from fastapi.params import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models import UserModel, UserGroupModel, UserGroupEnum
from src.exceptions import UserAlreadyExist
from src.schemas import UserCreateSchema, UserReadSchema
from src.databases import get_db


async def create_new_user(
        db: Annotated[AsyncSession, Depends(get_db)],
        user_data: UserCreateSchema,
) -> UserReadSchema:
    existing_user = get_user_by_email(db=db, email=user_data.email)
    if existing_user:
        raise UserAlreadyExist(
            message="User with provided email already exists"
        )

    user_data = user_data.model_dump()
    group_name = user_data.pop("group") or UserGroupEnum.USER
    result = await db.execute(
        select(UserGroupModel).where(UserGroupModel.name == group_name)
    )
    user_group = result.scalar_one_or_none()
    user = await UserModel.create(
        email=user_data.email,
        raw_password=user_data.password,
        group_id=user_group.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
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
    return result.all()
