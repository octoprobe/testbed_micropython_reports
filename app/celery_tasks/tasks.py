import os

from celery import Celery

app = Celery(
    "testbed_micropython_reports",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)


@app.task
def ping() -> str:
    return "pong"
