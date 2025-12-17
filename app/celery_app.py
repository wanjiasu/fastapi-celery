from celery import Celery
from celery.schedules import crontab
from .settings import settings

celery = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

celery.conf.beat_schedule = {
    "import-leagues-daily": {
        "task": "tasks.import_leagues",
        "schedule": crontab(minute=0, hour=1),
    }
}
