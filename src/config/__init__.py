from src.config.settings import (
    BaseAppSettings,
    LocalSettings,
    Settings,
    TestingSettings,
)

from src.config.dependencies import (
    get_settings,
    get_s3_storage_client as get_storage,
    get_jwt_auth_manager as get_jwt_manager,
    get_accounts_email_notificator as get_email_sender,
)

__all__ = [
    "BaseAppSettings",
    "LocalSettings",
    "Settings",
    "TestingSettings",
    "get_settings",
    "get_storage",
    "get_jwt_manager",
    "get_email_sender",
]
