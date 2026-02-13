import asyncio
from typing import Any

from src.config.celery_app import celery_instance
from src.config import get_email_sender, get_settings

settings = get_settings()
email_sender = get_email_sender(settings)


@celery_instance.task(
    bind=True,
    name="send_activation_email_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 5},
)
def send_activation_email_task(
    self,
    email: str,
    activation_link: str,
) -> Any:
    """
    Celery task to send activation email with automatic retries.
    """
    try:
        return asyncio.run(
            email_sender.send_activation_email(email, activation_link)
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_instance.task(name="send_activation_complete_email_task")
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


@celery_instance.task(name="send_password_reset_email_task")
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


@celery_instance.task(name="send_password_reset_complete_email_task")
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


@celery_instance.task(name="send_payment_success_email_task")
def send_payment_success_email_task(
    email: str, amount: float, order_id: int
) -> Any:
    return asyncio.run(
        email_sender.send_payment_success_email(email, amount, order_id)  # type: ignore
    )


@celery_instance.task(name="send_payment_failed_email_task")
def send_payment_failed_email_task(
    email: str, amount: float, order_id: int
) -> Any:
    return asyncio.run(
        email_sender.send_payment_failed_email(email, amount, order_id)  # type: ignore
    )
