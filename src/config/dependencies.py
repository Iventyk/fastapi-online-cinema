import os

from src.config.settings import BaseAppSettings, Settings, TestingSettings


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
