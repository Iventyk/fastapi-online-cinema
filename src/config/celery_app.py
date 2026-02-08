from celery import Celery
from celery.schedules import crontab

from src.config import get_settings

settings = get_settings()

celery_instance = Celery(
    "cinema_worker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    include=[
        "src.tasks.email_tasks",
        "src.tasks.token_periodic_tasks",
    ],
)

celery_instance.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Kyiv",
    enable_utc=True,
)

celery_instance.conf.beat_schedule = {
    "clear-expired-refresh-tokens-every-hour": {
        "task": "remove_expired_refresh_tokens_task",
        "schedule": crontab(minute=30),
    },
    "clear-expired-activation-tokens-every-day": {
        "task": "remove_expired_activation_tokens_task",
        "schedule": crontab(minute=0, hour=0),
    },
    "clear-expired-reset-tokens-every-hour": {
        "task": "remove_expired_reset_tokens_task",
        "schedule": crontab(minute=15),
    },
}
