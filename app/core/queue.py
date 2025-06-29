from celery import Celery

queue = Celery("adapter_worker", broker="amqp://guest:guest@localhost:5672//", backend="redis://localhost:6379/0")

queue.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
