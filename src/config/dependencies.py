import os
from typing import Annotated

from fastapi import Depends

from src.config.settings import BaseAppSettings, Settings, TestingSettings
from src.securuty import JWTAuthManagerInterface, JWTAuthManager
from src.storage import S3StorageInterface, S3StorageClient


def get_settings() -> BaseAppSettings:
    """
    Retrieve the application settings based on the current environment.

    This function reads the 'ENVIRONMENT' environment variable
    (defaulting to 'developing' if not set)
    and returns a corresponding settings instance.
    If the environment is 'testing', it returns an instance
    of TestingSettings; otherwise, it returns an instance of Settings.

    Returns:
        BaseAppSettings:
        The settings instance appropriate for the current environment.
    """

    environment = os.environ.get("ENVIRONMENT", "developing")
    base_url = os.environ.get(
        "DEV_DATABASE_URL", "sqlite+aiosqlite:///bbc_cinema.db"
    )
    if environment == "testing":
        return TestingSettings(
            DEV_DATABASE_URL=base_url,
            DEV_SYNC_DATABASE_URL=base_url,
        )
    return Settings(
        DEV_DATABASE_URL=base_url,
        DEV_SYNC_DATABASE_URL=base_url,
    )


def get_jwt_auth_manager(
    settings: Annotated[BaseAppSettings, Depends(get_settings)],
) -> JWTAuthManagerInterface:
    """
    Create and return a JWT authentication manager instance.

    This function uses the provided application settings to instantiate a
    JWTAuthManager, which implements the JWTAuthManagerInterface.
    The manager is configured with secret keys for access and refresh tokens
    as well as the JWT signing algorithm specified in the settings.

    Args:
        settings (BaseAppSettings, optional): The application settings instance
        Defaults to the output of get_settings().

    Returns:
        JWTAuthManagerInterface: An instance of JWTAuthManager configured with
        the appropriate secret keys and algorithm.
    """
    return JWTAuthManager(
        secret_key_access=settings.SECRET_KEY_ACCESS,
        secret_key_refresh=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
    )


def get_s3_storage_client(
    settings: BaseAppSettings = Depends(get_settings),
) -> S3StorageInterface:
    """
    Retrieve an instance of the S3StorageInterface configured with the application settings.

    This function instantiates an S3StorageClient using the provided settings, which include the S3 endpoint URL,
    access credentials, and the bucket name. The returned client can be used to interact with an S3-compatible
    storage service for file uploads and URL generation.

    Args:
        settings (BaseAppSettings, optional): The application settings,
        provided via dependency injection from `get_settings`.

    Returns:
        S3StorageInterface: An instance of S3StorageClient configured with the appropriate S3 storage settings.
    """
    return S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
    )
