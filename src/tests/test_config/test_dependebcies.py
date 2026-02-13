import os
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.config import get_settings, get_jwt_manager, get_storage

from src.config.dependencies import get_accounts_email_notificator
from src.config.settings import TestingSettings, Settings, LocalSettings
from unittest.mock import MagicMock

from src.main import app
from src.notifications import EmailSender
from src.security import JWTAuthManager


def test_get_settings_testing() -> None:
    with patch.dict(os.environ, {"ENVIRONMENT": "test"}):
        settings = get_settings()
        assert isinstance(settings, TestingSettings)


def test_get_settings_docker() -> None:
    with patch.dict(os.environ, {"ENVIRONMENT": "docker"}):
        settings = get_settings()
        assert isinstance(settings, Settings)


def test_get_settings_default_local() -> None:
    with patch.dict(os.environ, {}, clear=True):  # очищаємо оточення
        settings = get_settings()
        assert isinstance(settings, LocalSettings)


def test_get_jwt_auth_manager_initialization() -> None:
    mock_settings = MagicMock()
    mock_settings.SECRET_KEY_ACCESS = "access_secret_123"
    mock_settings.SECRET_KEY_REFRESH = "refresh_secret_456"
    mock_settings.JWT_SIGNING_ALGORITHM = "HS256"

    manager = get_jwt_manager(settings=mock_settings)

    assert isinstance(manager, JWTAuthManager)
    assert manager._secret_key_access == "access_secret_123"
    assert manager._secret_key_refresh == "refresh_secret_456"
    assert manager._algorithm == "HS256"


def test_get_s3_storage_client_initialization() -> None:
    mock_settings = MagicMock()
    mock_settings.S3_STORAGE_ENDPOINT = "http://localhost:9000"
    mock_settings.S3_STORAGE_ACCESS_KEY = "test_access_key"
    mock_settings.S3_STORAGE_SECRET_KEY = "test_secret_key"
    mock_settings.S3_BUCKET_NAME = "test_bucket"

    with patch("aioboto3.Session") as mocked_session:
        client = get_storage(settings=mock_settings)

        assert client._endpoint_url == "http://localhost:9000"  # type: ignore[attr-defined]
        assert client._access_key == "test_access_key"  # type: ignore[attr-defined]
        assert client._secret_key == "test_secret_key"  # type: ignore[attr-defined]
        assert client._bucket_name == "test_bucket"  # type: ignore[attr-defined]

        mocked_session.assert_called_once_with(
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
        )


client = TestClient(app)

mock_email_sender = MagicMock()

app.dependency_overrides[get_accounts_email_notificator] = (
    lambda: mock_email_sender
)


def test_get_accounts_email_notificator_initialization() -> None:
    mock_settings = MagicMock()
    mock_settings.EMAIL_HOST = "smtp.gmail.com"
    mock_settings.EMAIL_PORT = 587
    mock_settings.EMAIL_HOST_USER = "user@example.com"
    mock_settings.EMAIL_HOST_PASSWORD = "secret_password"
    mock_settings.EMAIL_USE_TLS = True
    mock_settings.PATH_TO_EMAIL_TEMPLATES_DIR = "/fake/path/templates"

    mock_settings.ACTIVATION_EMAIL_TEMPLATE_NAME = "activation_request.html"
    mock_settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME = (
        "activation_complete.html"
    )
    mock_settings.PASSWORD_RESET_TEMPLATE_NAME = "password_reset_request.html"
    mock_settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME = (
        "password_reset_complete.html"
    )

    with (
        patch("src.notifications.emails.FileSystemLoader") as mock_loader,
        patch("src.notifications.emails.Environment") as mocked_env,
    ):
        notificator = get_accounts_email_notificator(settings=mock_settings)

        assert isinstance(notificator, EmailSender)
        assert notificator._hostname == "smtp.gmail.com"
        assert notificator._email == "user@example.com"
        assert notificator._port == 587

        assert (
            notificator._activation_email_template_name
            == "activation_request.html"
        )
        assert (
            notificator._password_email_template_name
            == "password_reset_request.html"
        )

        mocked_env.assert_called_once()
