import logging
import os

from celery import Celery

from . import util_github2

logger = logging.getLogger(__file__)

app = Celery(
    "testbed_micropython_reports",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)

app.conf.beat_schedule = {
    "recurring_job": {
        "task": "app.util_celery_tasks.recurring_job",
        # "schedule": 300.0,
        "schedule": 10.0,
    }
}


@app.task
def ping() -> str:
    logger.info("pong")
    return "pong"


@app.task
def recurring_job() -> str:
    util_github2.gh_list2()
    return "recurring_job"
