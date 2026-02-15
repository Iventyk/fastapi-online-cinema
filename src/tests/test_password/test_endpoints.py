import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models import (
    UserModel,
    PasswordResetTokenModel,
    UserGroupModel,
)


@pytest.mark.asyncio
async def test_password_reset_integration_flow(
    client: AsyncClient, async_session: AsyncSession, mock_celery
):
    group = UserGroupModel(id=1, name="user")
    async_session.add(group)
    await async_session.flush()

    user = UserModel.create(
        email="reset@example.com",
        raw_password="OldPassword123!",
        group_id=group.id,
    )
    user.is_active = True
    async_session.add(user)
    await async_session.commit()

    reset_req = await client.post(
        "/password/reset", json={"email": "reset@example.com"}
    )
    assert reset_req.status_code == 200

    result = await async_session.execute(
        select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )
    token_record = result.scalar_one()
    reset_token = token_record.token

    confirm_data = {
        "token": reset_token,
        "email": "reset@example.com",
        "password": "NewSecurePassword123!",
    }
    confirm_res = await client.post(
        "/password/reset-confirm", json=confirm_data
    )
    assert confirm_res.status_code == 200

    login_data = {
        "email": "reset@example.com",
        "password": "NewSecurePassword123!",
    }
    login_res = await client.post("/accounts/login/", json=login_data)
    assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_change_password_authenticated(
    client: AsyncClient, async_session: AsyncSession
):
    group = UserGroupModel(id=1, name="user")
    async_session.add(group)
    await async_session.flush()

    user = UserModel.create(
        email="change@example.com",
        raw_password="CurrentPassword123!",
        group_id=group.id,
    )
    user.is_active = True
    async_session.add(user)
    await async_session.commit()

    login_res = await client.post(
        "/accounts/login/",
        json={
            "email": "change@example.com",
            "password": "CurrentPassword123!",
        },
    )
    token = login_res.json()["access_token"]

    change_data = {
        "old_password": "CurrentPassword123!",
        "new_password": "FullyNewPassword456!",
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "/password/change", json=change_data, headers=headers
    )

    assert response.status_code == 200

    fail_login = await client.post(
        "/accounts/login/",
        json={
            "email": "change@example.com",
            "password": "CurrentPassword123!",
        },
    )
    assert fail_login.status_code == 400
