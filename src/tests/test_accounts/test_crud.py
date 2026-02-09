import datetime

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import create_new_user, get_list_of_users, login_user
from src.crud.accounts import (
    get_user_by_email,
    activate_user,
    reactivate_user_token,
    manual_operation,
    refresh_token,
    logout_user,
)
from src.databases.models import UserGroupEnum


@pytest.mark.asyncio
async def test_create_new_user_success(mocker):
    user_data = MagicMock()
    user_data.email = "test@example.com"
    user_data.guest_cart_items = [1, 2]
    user_data.model_dump.return_value = {
        "email": "test@example.com",
        "password": "secure_password",
        "group": "USER",
    }

    db = AsyncMock(spec=AsyncSession)
    jwt_manager = MagicMock()
    jwt_manager.create_activation_token.return_value = "fake_jwt_token"

    mock_get_user = mocker.patch(
        "src.crud.accounts.get_user_by_email", return_value=None
    )
    mock_user_model_create = mocker.patch("src.crud.accounts.UserModel.create")
    mock_activation_model_create = mocker.patch(
        "src.crud.accounts.ActivationTokenModel.create"
    )
    mock_sync_cart = mocker.patch(
        "src.crud.accounts.sync_guest_cart_to_user", new_callable=AsyncMock
    )
    mock_email_task = mocker.patch(
        "src.crud.accounts.send_activation_email_task.delay"
    )

    mock_group = MagicMock(id=1)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_group
    db.execute.return_value = mock_result

    created_user = MagicMock()
    created_user.id = 100
    created_user.email = "test@example.com"
    created_user.is_active = False
    mock_user_model_create.return_value = created_user

    result = await create_new_user(
        db=db, jwt_manager=jwt_manager, user_data=user_data
    )

    assert result.email == "test@example.com"
    assert result.id == 100

    mock_get_user.assert_called_once_with(db=db, email=user_data.email)
    db.commit.assert_called_once()
    mock_sync_cart.assert_called_once()
    mock_email_task.assert_called_once()

    _, kwargs = mock_email_task.call_args
    assert "fake_jwt_token" in kwargs["activation_link"]


@pytest.mark.asyncio
async def test_get_user_by_email_success(mocker):
    db = AsyncMock(spec=AsyncSession)
    email = "test@example.com"

    mock_user = MagicMock()
    mock_user.email = email

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    db.execute.return_value = mock_result

    result = await get_user_by_email(db=db, email=email)

    assert result == mock_user
    assert result.email == email
    db.execute.assert_called_once()
    mock_result.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_list_of_users_success(mocker):
    db = AsyncMock(spec=AsyncSession)
    skip, limit = 0, 10

    mock_user_1 = MagicMock()
    mock_user_1.id = 1
    mock_user_1.email = "user1@test.com"

    mock_user_2 = MagicMock()
    mock_user_2.id = 2
    mock_user_2.email = "user2@test.com"

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_user_1, mock_user_2]
    db.scalars.return_value = mock_result

    mock_schema = mocker.patch(
        "src.crud.accounts.UserReadSchema.model_validate"
    )
    mock_schema.side_effect = lambda x: x

    users = await get_list_of_users(db=db, skip=skip, limit=limit)

    assert len(users) == 2
    assert users[0].email == "user1@test.com"
    db.scalars.assert_called_once()
    mock_result.all.assert_called_once()


@pytest.mark.asyncio
async def test_login_user_success(mocker):
    login_data = MagicMock()
    login_data.email = "test@example.com"
    login_data.password = "correct_password"
    login_data.guest_cart_items = [1, 2]

    db = AsyncMock(spec=AsyncSession)

    jwt_manager = MagicMock()
    jwt_manager.create_access_token.return_value = "fake_access_token"
    jwt_manager.create_refresh_token.return_value = "fake_refresh_token"

    settings = MagicMock()
    settings.ACCESS_KEY_TIMEDELTA_MINUTES = 15
    settings.REFRESH_TOKEN_DAYS = 7

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = True
    mock_user.check_password.return_value = True

    mocker.patch("src.crud.accounts.get_user_by_email", return_value=mock_user)
    mock_refresh_token_create = mocker.patch(
        "src.crud.accounts.RefreshTokenModel.create"
    )
    mock_sync_cart = mocker.patch(
        "src.crud.accounts.sync_guest_cart_to_user", new_callable=AsyncMock
    )

    result = await login_user(
        db=db,
        jwt_manager=jwt_manager,
        settings=settings,
        login_data=login_data,
    )

    assert result.access_token == "fake_access_token"
    assert result.refresh_token == "fake_refresh_token"
    assert result.token_type == "bearer"

    mock_user.check_password.assert_called_once_with("correct_password")

    jwt_manager.create_access_token.assert_called_once()
    jwt_manager.create_refresh_token.assert_called_once()

    db.add.assert_called_once()
    db.commit.assert_called_once()

    mock_sync_cart.assert_called_once_with(
        db=db, user_id=mock_user.id, guest_movie_ids=[1, 2]
    )


@pytest.mark.asyncio
async def test_activate_user_success(mocker):
    db = AsyncMock(spec=AsyncSession)
    token_str = "valid_token"

    mock_email_task = mocker.patch(
        "src.crud.accounts.send_activation_complete_email_task.delay"
    )

    mock_user = MagicMock()
    mock_user.email = "user@example.com"
    mock_user.is_active = False

    mock_token_record = MagicMock()
    mock_token_record.token = token_str
    mock_token_record.user = mock_user
    mock_token_record.expires_at = datetime.datetime.now(
        datetime.timezone.utc
    ) + datetime.timedelta(hours=1)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token_record
    db.execute.return_value = mock_result

    result = await activate_user(activation_token=token_str, db=db)

    assert result.message == "Successfully activate your account"
    assert mock_user.is_active is True

    db.execute.assert_called_once()
    db.delete.assert_called_once_with(mock_token_record)
    db.commit.assert_called_once()

    mock_email_task.assert_called_once_with(
        email="user@example.com",
        login_link="http://127.0.0.1:8000/accounts/login/",
    )


@pytest.mark.asyncio
async def test_reactivate_user_token_success(mocker):
    user_data = MagicMock()
    user_data.email = "test@example.com"
    user_data.password = "password123"

    db = AsyncMock(spec=AsyncSession)
    jwt_manager = MagicMock()
    jwt_manager.create_activation_token.return_value = "new_fake_token"

    mock_user = MagicMock()
    mock_user.is_active = False
    mock_user.check_password.return_value = True
    mock_user.id = 1
    mock_user.email = "test@example.com"

    mocker.patch("src.crud.accounts.get_user_by_email", return_value=mock_user)
    mocker.patch("src.crud.accounts.delete")
    mock_token_create = mocker.patch(
        "src.crud.accounts.ActivationTokenModel.create"
    )
    mock_email_task = mocker.patch(
        "src.crud.accounts.send_activation_email_task.delay"
    )

    result = await reactivate_user_token(user_data, db, jwt_manager)

    assert "new link has been sent" in result.message
    db.execute.assert_called_once()
    db.commit.assert_called_once()
    mock_token_create.assert_called_once()
    mock_email_task.assert_called_once()


@pytest.mark.asyncio
async def test_logout_user(mocker):
    db = AsyncMock(spec=AsyncSession)
    auth_user = MagicMock()
    auth_user.user_id = 99

    mocker.patch("src.crud.accounts.delete")

    result = await logout_user(db, auth_user)

    assert "Successfully logged out" in result.message
    db.execute.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_manual_operation_update_permission(mocker):
    db = AsyncMock(spec=AsyncSession)
    data = MagicMock()
    data.activation = True
    data.permission = UserGroupEnum.ADMIN

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.is_active = False
    mock_user.group.name = UserGroupEnum.USER

    db.get.return_value = mock_user

    mock_new_group = MagicMock()
    mock_new_group.name = UserGroupEnum.ADMIN
    db.scalar.return_value = mock_new_group

    result = await manual_operation(1, db, data)

    assert result.is_active is True
    assert mock_user.group == mock_new_group
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_success(mocker):
    token_schema = MagicMock()
    token_schema.refresh_token = "valid_refresh_token"

    jwt_manager = MagicMock()
    jwt_manager.decode_refresh_token.return_value = {
        "user_id": 10,
        "email": "test@example.com",
    }
    jwt_manager.create_access_token.return_value = "new_access_token"

    settings = MagicMock()
    settings.ACCESS_KEY_TIMEDELTA_MINUTES = 15

    result = await refresh_token(token_schema, jwt_manager, settings)

    assert result.access_token == "new_access_token"
    jwt_manager.decode_refresh_token.assert_called_once_with(
        "valid_refresh_token"
    )
