import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.databases.models import (
    ActivationTokenModel,
    UserGroupModel,
    UserGroupEnum,
)


@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient, async_session: AsyncSession):
    default_group = UserGroupModel(name=UserGroupEnum.USER)
    async_session.add(default_group)
    await async_session.commit()

    reg_data = {"email": "test-user1@email.com", "password": "1Qazcde3@"}
    response = await client.post("/accounts/register/", json=reg_data)
    assert response.status_code == 201
    assert response.json()["email"] == "test-user1@email.com"

    login_data = {"email": "test-user1@email.com", "password": "1Qazcde3@"}
    login_resp = await client.post("/accounts/login/", json=login_data)
    assert login_resp.status_code == 403

    result = await async_session.execute(select(ActivationTokenModel))
    token_obj = result.scalar_one()
    token_str = token_obj.token

    act_resp = await client.get(
        f"/accounts/activate/?activation_token={token_str}"
    )
    assert act_resp.status_code == 200

    final_login = await client.post("/accounts/login/", json=login_data)
    assert final_login.status_code == 200
    assert "access_token" in final_login.json()
