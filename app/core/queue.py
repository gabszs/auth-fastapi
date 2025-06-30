from celery import Celery
from app.core.settings import settings
queue = Celery("adapter_worker", broker=settings.RABBITMQ_URL, backend=f"{settings.REDIS_URL}/0")

queue.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
