"""

* Endpoint: `/github-webhook`

Register via web:
* https://github.com/<owner>/<repo>/settings/hooks
* Settings -> Webhooks -> Add webhook ->
  * Payload URL: https://reports.octoprobe.org/github-webhook
  * Content Type: application/json
  * Secret: <secret>
  * SSL: Disable # github doesn't seem to recognice letsencrypt
  * Which: Let me select individual events
    * Pull requests
  --> Add webhook
"""

import enum
import hashlib
import hmac
import json
import logging
import os
import pathlib
import typing

from testbed_micropython.report_test import util_testreport

from app import constants

logger = logging.getLogger(__file__)


WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]


class EnumDone(enum.StrEnum):
    TODO = "todo"
    DONE = "done"


def verify_signature(body: bytes, signature: str) -> bool:
    assert isinstance(body, bytes)
    assert isinstance(signature, str)

    expected = (
        "sha256="
        + hmac.new(
            WEBHOOK_SECRET.encode("ascii"),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(expected, signature)


def repo_directory_name(repo: str, enumdone: EnumDone) -> pathlib.Path:
    assert isinstance(repo, str)
    assert len(repo.split("/")) == 2, (
        f"'{repo}' should be something like 'micropython/micropython'!"
    )
    repo_text = repo.replace("/", "-")
    return constants.DIRECTORY_REPORTS_WEBHOOK / repo_text / enumdone.value


def move_files_to_done(repo: str, pr_number: int) -> None:
    """
    Move all files related to 'repo_text' and 'pr_number' into the 'done' folder.
    """
    directory_todo = repo_directory_name(repo=repo, enumdone=EnumDone.TODO)
    directory_done = repo_directory_name(repo=repo, enumdone=EnumDone.DONE)
    directory_done.mkdir(parents=True, exist_ok=True)
    pattern = f"*-{pr_number:06d}.json"
    logger.debug(f"Pattern: {pattern}")
    for filename_todo in directory_todo.glob(pattern):
        filename_done = directory_done / filename_todo.name
        logger.debug(f"{filename_todo} -> {filename_done}")
        filename_todo.rename(filename_done)


def handle_webhook(x_github_event: str, payload: dict[str, typing.Any]) -> None:
    assert isinstance(x_github_event, str)
    assert isinstance(payload, dict)

    action = payload.get("action", "ping")

    pr_number = 0
    repo: str = payload["repository"]["full_name"]
    try:
        pr_number = payload["pull_request"]["number"]
    except KeyError:
        pass

    move_files_to_done(repo=repo, pr_number=pr_number)

    now_text = util_testreport.now_formatted()
    filename = "-".join(
        [
            now_text,
            x_github_event,
            action,
            f"{pr_number:06d}.json",
        ]
    )
    filename_json = repo_directory_name(repo=repo, enumdone=EnumDone.TODO) / filename
    filename_json.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"webhook: repo:{repo}, event:{x_github_event}, action:{action}, #{pr_number}, filename:{filename_json}"
    )
    with filename_json.open("w") as f:
        json.dump(obj=payload, fp=f, indent=4)

    # if action != "synchronize":
    #     return

    # Trigger your application logic here
    # e.g. queue a job, run tests, notify a service, ...
