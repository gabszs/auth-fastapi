from celery import Celery

app = Celery("adapter_worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://localhost:6379/0")

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
