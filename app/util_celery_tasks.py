import logging
import os

from celery import Celery

from . import util_github2, util_webhooks

logger = logging.getLogger(__file__)

app = Celery(
    "testbed_micropython_reports",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
)

# Keep startup broker retries explicit for Celery 6+ compatibility.
app.conf.broker_connection_retry_on_startup = "true"

app.conf.beat_schedule = {
    "recurring_job": {
        "task": "app.util_celery_tasks.recurring_job",
        "schedule": 300.0,
        # "schedule": 10.0,
    }
}


@app.task
def ping() -> str:
    logger.info("pong")
    return "pong"


def run_recurring_job() -> None:
    try:
        gh_list = util_github2.get_gh_list()
    except Exception:
        logger.exception("util_github2.gh_list() failed")
        return

    if gh_list.in_progress:
        logger.info("Octoprobe test in progress...")
        return

    for repo in util_webhooks.REPOS:
        if util_webhooks.Webhooks.recurring_job(repo=repo.repo):
            return


@app.task
def recurring_job() -> str:
    run_recurring_job()
    return "recurring_job"


if __name__ == "__main__":
    run_recurring_job()
