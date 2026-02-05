import pytest

from src.databases.models import UserModel


@pytest.mark.asyncio
async def test_user_create_hashes_password():
    user = await UserModel.create(
        email="test@example.com",
        raw_password="StrongPass123!",
        group_id=1,
    )

    assert user.email == "test@example.com"
    assert user.group_id == 1
    assert user._hashed_password is not None
    assert user._hashed_password != "StrongPass123!"


def test_password_is_write_only():
    user = UserModel(email="test@example.com", group_id=1)

    with pytest.raises(AttributeError):
        _ = user.password


def test_check_password_success():
    user = UserModel(email="test@example.com", group_id=1)
    user.password = "StrongPass123!"

    assert user.check_password("StrongPass123!") is True


def test_check_password_failure():
    user = UserModel(email="test@example.com", group_id=1)
    user.password = "StrongPass123!"

    assert user.check_password("WrongPassword") is False


def test_invalid_password_rejected():
    user = UserModel(email="test@example.com", group_id=1)

    with pytest.raises(ValueError):
        user.password = "123"
