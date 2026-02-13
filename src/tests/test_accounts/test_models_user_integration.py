import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.databases.models import (
    UserModel,
    UserGroupModel,
    UserGroupEnum,
)

settings = get_settings()


@pytest.mark.asyncio
async def test_create_user_with_group(async_session: AsyncSession) -> None:
    group = UserGroupModel(name=UserGroupEnum.USER)
    async_session.add(group)
    await async_session.commit()

    user = UserModel.create(
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

    user1 = UserModel.create(
        email="duplicate@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )
    user2 = UserModel.create(
        email="duplicate@example.com",
        raw_password="StrongPass123!",
        group_id=group.id,
    )

    async_session.add_all([user1, user2])

    with pytest.raises(IntegrityError):
        await async_session.commit()


@pytest.mark.asyncio
async def test_token_expiration_logic(async_session: AsyncSession) -> None:
    from src.databases.models.accounts import RefreshTokenModel
    from datetime import datetime, timezone, timedelta

    user_id = 1
    token_str = "refresh-token-hex"
    refresh_token = RefreshTokenModel.create(user_id, token_str)

    expected_expiry = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_DAYS
    )

    assert (
        abs((refresh_token.expires_at - expected_expiry).total_seconds()) < 2
    )
