import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
)


@pytest.mark.asyncio
async def test_create_user_with_group(async_session: AsyncSession) -> None:
    group = UserGroupModel(name=UserGroupEnum.USER)
    async_session.add(group)
    await async_session.commit()

    user = await UserModel.create(
        email="user@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )

    async_session.add(user)
    await async_session.commit()

    stmt = select(UserModel).where(UserModel.email == "user@example.com")
    result = await async_session.execute(stmt)
    db_user = result.scalar_one()

    assert db_user.group.id == group.id
    assert db_user.group.name == UserGroupEnum.USER


@pytest.mark.asyncio
async def test_unique_email_constraint(async_session: AsyncSession) -> None:
    group = UserGroupModel(name=UserGroupEnum.USER)
    async_session.add(group)
    await async_session.commit()

    user1 = await UserModel.create(
        email="duplicate@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )
    user2 = await UserModel.create(
        email="duplicate@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )

    async_session.add_all([user1, user2])

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_user_deleted_when_group_deleted(
    async_session: AsyncSession,
) -> None:
    group = UserGroupModel(name=UserGroupEnum.ADMIN)
    async_session.add(group)
    await async_session.commit()

    user = await UserModel.create(
        email="cascade@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )

    async_session.add(user)
    await async_session.commit()

    await async_session.delete(group)
    await async_session.commit()

    stmt = select(UserModel).where(UserModel.email == "cascade@example.com")
    result = await async_session.execute(stmt)

    assert result.scalar_one_or_none() is None
