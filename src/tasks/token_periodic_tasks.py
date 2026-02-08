import asyncio
from datetime import datetime, timezone
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.config.celery_app import celery_instance
from src.config import get_settings
from src.databases.models import (
    TokenBaseModel,
    ActivationTokenModel, PasswordResetTokenModel, RefreshTokenModel,
)

settings = get_settings()


async def _remove_expired_tokens(
        token_type: type[TokenBaseModel],
):
    local_engine = create_async_engine(
        url=settings.DATABASE_URL,
        poolclass=NullPool
    )

    LocalSession = async_sessionmaker(
        bind=local_engine,
        autoflush=False,
        expire_on_commit=False
    )

    async with LocalSession() as db:
        try:
            table_name = token_type.__tablename__

            stmt = delete(token_type).where(
                token_type.expires_at < datetime.now(timezone.utc)
            )
            result = await db.execute(stmt)
            await db.commit()

            print(
                f"--- [CLEANUP SUCCESS] Table '{table_name}': Deleted {result.rowcount} tokens. ---")
        except Exception as e:
            await db.rollback()
            print(
                f"--- [CLEANUP ERROR] Failed for {token_type.__name__}: {e} ---")
            raise e
        finally:
            await db.close()
            await local_engine.dispose()


@celery_instance.task(name="remove_expired_activation_tokens_task")
def remove_expired_activation_tokens_task():
    """
    Isolated sync coverage for async task with own db session
    Remove expired email activation tokens
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_remove_expired_tokens(
            token_type=ActivationTokenModel
        ))
    finally:
        loop.close()


@celery_instance.task(name="remove_expired_reset_tokens_task")
def remove_expired_reset_tokens_task():
    """
    Isolated sync coverage for async task with own db session
    Remove expired email tokens for resets passwords
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_remove_expired_tokens(
            token_type=PasswordResetTokenModel
        ))
    finally:
        loop.close()

@celery_instance.task(name="remove_expired_refresh_tokens_task")
def remove_expired_refresh_tokens_task():
    """
    Isolated sync coverage for async task with own db session
    Remove expired refresh tokens
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_remove_expired_tokens(
            token_type=RefreshTokenModel
        ))
    finally:
        loop.close()