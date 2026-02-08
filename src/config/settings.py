import os
from pathlib import Path
from typing import Any, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,  # ignore register (POSTGRES_DB == postgres_db)
    )

    BASE_DIR: Path = Path(__file__).parent.parent
    ENVIRONMENT: str = "local"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite+aiosqlite:///{self.BASE_DIR}/bbc_cinema.db"

    PATH_TO_DB: str = str(BASE_DIR / "src" / "bbc_cinema.db")

    @property
    def PATH_TO_MOVIES_CSV(self) -> str:
        return str(
            self.BASE_DIR / "database" / "seed_data" / "imdb_movies.csv"
        )

    PATH_TO_EMAIL_TEMPLATES_DIR: str = str(
        BASE_DIR / "notifications" / "templates"
    )
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete.html"

    ACTIVATE_TOKEN_DAYS: int = 1
    RESET_TOKEN_DURATION: int = 1
    REFRESH_TOKEN_DAYS: int = 7
    ACCESS_KEY_TIMEDELTA_MINUTES: int = 60

    SECRET_KEY_ACCESS: str = "placeholder_access"
    SECRET_KEY_REFRESH: str = "placeholder_refresh"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    EMAIL_HOST: str = Field(
        default="mailhog_cinema", validation_alias="EMAIL_HOST"
    )
    EMAIL_PORT: int = Field(default=1025, validation_alias="EMAIL_PORT")
    EMAIL_HOST_USER: str = Field(
        default="bbc_cinema", validation_alias="EMAIL_HOST_USER"
    )
    EMAIL_HOST_PASSWORD: str = Field(
        default="bbc_cinema_password", validation_alias="EMAIL_HOST_PASSWORD"
    )
    EMAIL_USE_TLS: bool = Field(
        default=False, validation_alias="EMAIL_USE_TLS"
    )
    MAILHOG_API_PORT: int = 8025

    REDIS_HOST: str = Field(
        default="additional_db", validation_alias="REDIS_HOST"
    )
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT")

    S3_STORAGE_HOST: str = Field(
        default="minio-cinema", validation_alias="MINIO_HOST"
    )
    S3_STORAGE_PORT: int = Field(default=9000, validation_alias="MINIO_PORT")
    S3_STORAGE_ACCESS_KEY: str = Field(
        default="minioadmin", validation_alias="MINIO_ROOT_USER"
    )
    S3_STORAGE_SECRET_KEY: str = Field(
        default="bbc_cinema_password", validation_alias="MINIO_ROOT_PASSWORD"
    )
    S3_BUCKET_NAME: str = Field(
        default="ddc-cinema-storage", validation_alias="MINIO_STORAGE"
    )

    @property
    def S3_STORAGE_ENDPOINT(self) -> str:
        return f"http://{self.S3_STORAGE_HOST}:{self.S3_STORAGE_PORT}"


class LocalSettings(BaseAppSettings):
    """DEV_SETTINGS: Local SQLite"""

    ENVIRONMENT: str = "local"

    @property
    def DATABASE_URL(self) -> str:
        return "sqlite+aiosqlite:///bbc_cinema.db"


class Settings(BaseAppSettings):
    ENVIRONMENT: str = "docker"

    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST")
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB")

    SECRET_KEY_ACCESS: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY_ACCESS", os.urandom(32).hex()
        )
    )
    SECRET_KEY_REFRESH: str = Field(
        default_factory=lambda: os.getenv(
            "SECRET_KEY_REFRESH", os.urandom(32).hex()
        )
    )
    JWT_SIGNING_ALGORITHM: str = "HS256"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def _get_db_url(self) -> str:
        if self.ENVIRONMENT == "docker":
            return (
                f"postgresql+asyncpg://{self.POSTGRES_USER}"
                f":{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}"
                f":{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
            )
        return f"sqlite+aiosqlite:///{self.BASE_DIR}/bbc_cinema.db"


class TestingSettings(BaseAppSettings):
    """TEST_SETTINGS: SQLite in-memory"""

    ENVIRONMENT: str = "test"

    SECRET_KEY_ACCESS: str = "test_secret"
    SECRET_KEY_REFRESH: str = "test_secret"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return "sqlite+aiosqlite:///:memory:"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def PATH_TO_MOVIES_CSV(self) -> str:
        return str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv")
