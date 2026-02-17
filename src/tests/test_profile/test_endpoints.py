from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import MagicMock, patch
from src.databases.models import UserModel, UserGroupModel, UserProfileModel
from src.databases.models.accounts import GenderEnum, UserGroupEnum


@pytest.mark.asyncio
class TestProfileEndpoints:

    async def _setup_user(self, async_session: AsyncSession, email: str):
        """Helper to create group and active user."""
        group = UserGroupModel(name=UserGroupEnum.USER)
        async_session.add(group)
        await async_session.flush()

        user = UserModel.create(
            email=email,
            raw_password="Password123!",
            group_id=group.id,
        )
        user.is_active = True
        async_session.add(user)
        await async_session.commit()
        return user

    @patch("src.crud.profile._upload_avatar_and_get_url")
    async def test_create_profile_endpoint_success(
        self, mock_upload, client: AsyncClient, async_session: AsyncSession
    ):
        user = await self._setup_user(async_session, "profile@example.com")
        mock_upload.return_value = "http://s3.com/avatar.jpg"

        login_res = await client.post(
            "/accounts/login/",
            json={"email": "profile@example.com", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]

        form_data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "male",
            "date_of_birth": "1990-01-01",
            "info": "Hello world",
        }
        files = {"avatar": ("avatar.jpg", b"fake-image-content", "image/jpeg")}

        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            f"/profile/create/{user.id}",
            data=form_data,
            files=files,
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["avatar"] == "http://s3.com/avatar.jpg"
        assert data["user_id"] == user.id

    @patch("src.crud.profile._upload_avatar_and_get_url")
    async def test_partial_update_profile_success(
        self, mock_upload, client: AsyncClient, async_session: AsyncSession
    ):
        user = await self._setup_user(async_session, "update@example.com")
        profile = UserProfileModel(
            user_id=user.id,
            first_name="Old",
            last_name="Name",
            gender=GenderEnum.MALE,
            date_of_birth=date(2000, 1, 1),
            info="Some info",
            avatar="http://old.jpg",
        )
        async_session.add(profile)
        await async_session.commit()

        user.profile_id = user.id

        login_res = await client.post(
            "/accounts/login/",
            json={"email": "update@example.com", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = await client.patch(
            f"/profile/{user.id}",
            data={"first_name": "Newname"},
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["first_name"] == "Newname"
        assert response.json()["last_name"] == "Name"
