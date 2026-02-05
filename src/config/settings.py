import os
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,  # ignore register (POSTGRES_DB == postgres_db)
    )

    BASE_DIR: Path = Path(__file__).parent.parent
    PATH_TO_DB: str = str(BASE_DIR / "database" / "source" / "theater.db")
    PATH_TO_MOVIES_CSV: str = str(
        BASE_DIR / "database" / "seed_data" / "imdb_movies.csv"
    )

    DEV_DATABASE_URL: str
    API_V1_PREFIX: str = "/api/v1"
    DEV_SYNC_DATABASE_URL: str

    ACTIVATE_TOKEN_DAYS: int = 1
    RESET_TOKEN_DURATION: int = 1
    REFRESH_TOKEN_DAYS: int = 7
    ACCESS_KEY_TIMEDELTA_MINUTES: int = 60

    SECRET_KEY_ACCESS: str
    SECRET_KEY_REFRESH: str
    JWT_SIGNING_ALGORITHM: str

    EMAIL_HOST: str = "host"
    EMAIL_PORT: int = 25
    EMAIL_HOST_USER: str = "testuser"
    EMAIL_HOST_PASSWORD: str = "test_password"
    EMAIL_USE_TLS: bool = False
    MAILHOG_API_PORT: int = 8025

    S3_STORAGE_HOST: str = Field(
        default="minio-theater", validation_alias="MINIO_HOST"
    )
    S3_STORAGE_PORT: int = Field(default=9000, validation_alias="MINIO_PORT")
    S3_STORAGE_ACCESS_KEY: str = Field(
        default="minioadmin", validation_alias="MINIO_ROOT_USER"
    )
    S3_STORAGE_SECRET_KEY: str = Field(
        default="some_password", validation_alias="MINIO_ROOT_PASSWORD"
    )
    S3_BUCKET_NAME: str = Field(
        default="theater-storage", validation_alias="MINIO_STORAGE"
    )


class Settings(BaseAppSettings):
    POSTGRES_USER: str = "test_user"
    POSTGRES_PASSWORD: str = "test_password"
    POSTGRES_HOST: str = "test_host"
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_DB: str = "test_db"

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


class TestingSettings(BaseAppSettings):
    SECRET_KEY_ACCESS: str = "SECRET_KEY_ACCESS"
    SECRET_KEY_REFRESH: str = "SECRET_KEY_REFRESH"
    JWT_SIGNING_ALGORITHM: str = "HS256"

    def model_post_init(self, __context: dict[str, Any] | None = None) -> None:
        object.__setattr__(self, "PATH_TO_DB", ":memory:")
        object.__setattr__(
            self,
            "PATH_TO_MOVIES_CSV",
            str(self.BASE_DIR / "database" / "seed_data" / "test_data.csv"),
        )
