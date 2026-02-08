import asyncio
from typing import Any

from src.config.celery_app import celery_instance
from src.config import get_email_sender, get_settings

settings = get_settings()
email_sender = get_email_sender(settings)


@celery_instance.task(name="send_activation_email_task")  # type: ignore[untyped-decorator]
def send_activation_email_task(
    email: str,
    activation_link: str,
) -> Any:
    """
    Celery-task to send activation email.
    """
    return asyncio.run(
        email_sender.send_activation_email(email, activation_link)
    )


@celery_instance.task(name="send_activation_complete_email_task")  # type: ignore[untyped-decorator]
def send_activation_complete_email_task(
    email: str,
    login_link: str,
) -> Any:
    """
    Celery-task to send activation complete email.
    """
    return asyncio.run(
        email_sender.send_activation_complete_email(email, login_link)
    )


@celery_instance.task(name="send_password_reset_email_task")  # type: ignore[untyped-decorator]
def send_password_reset_email_task(
    email: str,
    reset_link: str,
) -> Any:
    """
    Celery-task to send password reset request email.
    """
    return asyncio.run(
        email_sender.send_password_reset_email(email, reset_link)
    )


@celery_instance.task(name="send_password_reset_complete_email_task")  # type: ignore[untyped-decorator]
def send_password_reset_complete_email_task(
    email: str,
    login_link: str,
) -> Any:
    """
    Celery-task to send password reset response complete email.
    """
    return asyncio.run(
        email_sender.send_password_reset_complete_email(email, login_link)
    )
