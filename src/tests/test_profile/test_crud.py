from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from src.crud.profile import create_user_profile, update_user_profile
from src.databases.models.accounts import GenderEnum
from src.schemas import ProfileCreateSchema, CurrentUser, ProfileUpdateSchema
from src.exceptions import UserPermissionDenied


@pytest.mark.asyncio
class TestProfileCRUD:

    @patch("src.crud.profile._upload_avatar_and_get_url")
    async def test_create_user_profile_success(
        self, mock_upload, async_session
    ):
        account_id = 1
        auth_user = CurrentUser(
            user_id=1,
            email="test@test.com",
            permission="user",
            is_active=True,
            profile_id=None,
        )

        mock_avatar = MagicMock(spec=UploadFile)
        mock_upload.return_value = "http://s3.com/avatar.jpg"

        profile_data = ProfileCreateSchema(
            first_name="John",
            last_name="Doe",
            gender=GenderEnum.MALE,
            date_of_birth=date(2000, 1, 1),
            info="Some info",
            avatar=mock_avatar,
        )

        mock_acc = MagicMock(id=1, is_active=True, profile=None)
        async_session.get = AsyncMock(return_value=mock_acc)
        async_session.commit = AsyncMock()

        async def mock_refresh(instance):
            instance.id = 10
            instance.user_id = 1

        async_session.refresh = AsyncMock(side_effect=mock_refresh)
        async_session.add = MagicMock()

        from src.storage import S3StorageInterface

        mock_storage = MagicMock(spec=S3StorageInterface)

        response = await create_user_profile(
            account_id=account_id,
            profile_data=profile_data,
            db=async_session,
            auth_user=auth_user,
            s3_storage=mock_storage,
        )

        assert response.id == 10
        assert response.user_id == 1
        assert response.first_name == "John"
        async_session.add.assert_called_once()
        async_session.commit.assert_called_once()

    async def test_create_profile_permission_denied(self, async_session):
        auth_user = CurrentUser(
            user_id=1,
            email="t@t.com",
            permission="user",
            is_active=True,
            profile_id=None,
        )

        with pytest.raises(UserPermissionDenied):
            await create_user_profile(
                account_id=2,
                profile_data=MagicMock(),
                db=async_session,
                auth_user=auth_user,
                s3_storage=MagicMock(),
            )

    @patch("src.crud.profile._get_profile_by_id")
    @patch("src.crud.profile._upload_avatar_and_get_url")
    async def test_update_user_profile_avatar(
        self, mock_upload, mock_get_profile, async_session
    ):
        existing_profile = MagicMock()
        existing_profile.id = 1
        existing_profile.first_name = "OldName"
        existing_profile.last_name = "OldLastName"
        existing_profile.gender = GenderEnum.MALE
        existing_profile.date_of_birth = date(1990, 1, 1)
        existing_profile.info = "Old Info"
        existing_profile.avatar = "http://s3.com/old.jpg"

        mock_get_profile.return_value = existing_profile

        mock_avatar = MagicMock(spec=UploadFile)
        mock_upload.return_value = "http://s3.com/new-avatar.jpg"

        update_data = ProfileUpdateSchema(
            first_name="Jane", avatar=mock_avatar
        )

        async_session.commit = AsyncMock()
        async_session.refresh = AsyncMock()

        from src.storage import S3StorageInterface

        response = await update_user_profile(
            account_id=1,
            profile_data=update_data,
            db=async_session,
            s3_storage=MagicMock(spec=S3StorageInterface),
        )

        assert existing_profile.first_name == "Jane"
        assert existing_profile.avatar == "http://s3.com/new-avatar.jpg"
        assert response.first_name == "Jane"
        async_session.commit.assert_called_once()
