import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.crud.password import (
    do_pswd_restore_request,
    change_password,
    do_pswd_reset_confirm
)
from src.schemas import (
    ChangePasswordSchema,
    ResetPasswordRequestSchema,
    CurrentUser
)
from src.exceptions import PasswordChangeError, IncorrectCredentials


@pytest.mark.asyncio
class TestPasswordCRUD:

    @patch("src.crud.password.send_password_reset_email_task.delay")
    @patch("src.crud.password.get_user_by_email")
    async def test_do_pswd_restore_request_success(
            self, mock_get_user, mock_celery_task, async_session
    ):
        mock_user = MagicMock(id=1, is_active=True)
        mock_get_user.return_value = mock_user
        mock_jwt = MagicMock()
        mock_jwt.create_reset_token.return_value = "fake-reset-token"

        async_session.commit = AsyncMock()
        async_session.execute = AsyncMock()

        response = await do_pswd_restore_request(
            db=async_session,
            email="test@example.com",
            jwt_manager=mock_jwt
        )

        assert "reset link has been sent" in response.message
        mock_celery_task.assert_called_once()
        assert async_session.commit.called

    @patch("src.crud.password.get_user_by_email")
    async def test_do_pswd_restore_request_user_not_found(
            self, mock_get_user, async_session
    ):
        mock_get_user.return_value = None
        mock_jwt = MagicMock()
        async_session.commit = AsyncMock()

        response = await do_pswd_restore_request(
            db=async_session, email="unknown@example.com", jwt_manager=mock_jwt
        )

        assert "reset link has been sent" in response.message
        assert not async_session.commit.called

    async def test_change_password_success(self, async_session):
        mock_user = MagicMock()
        mock_user.check_password.return_value = True

        async_session.get = AsyncMock(return_value=mock_user)
        async_session.commit = AsyncMock()

        auth_user = CurrentUser(
            user_id=1,
            email="test@test.com",
            permission="user",
            is_active=True,
            profile_id=1
        )
        data = ChangePasswordSchema(
            old_password="Nomal!1old",
                                    new_password="Nomal!1new"
        )

        response = await change_password(async_session, auth_user, data)

        assert response.message == "Password has been changed successfully"
        assert mock_user.password == "Nomal!1new"
        assert async_session.commit.called