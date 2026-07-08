"""

* Endpoint: `/github-webhook`

Register via web:
* https://github.com/<owner>/<repo>/settings/hooks
* Settings -> Webhooks -> Add webhook ->
  * Payload URL: https://reports.octoprobe.org/github-webhook
  * Content Type: application/json
  * Secret: <secret>
  * SSL: Disable # github doesn't seem to recognize letsencrypt
  * Let me select individual events
    * Pull requests
  --> Add webhook
"""

from __future__ import annotations

import dataclasses
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


class EnumDone(enum.StrEnum):
    TODO = "todo"
    DONE = "done"


def verify_signature(body: bytes, signature: str) -> bool:
    assert isinstance(body, bytes)
    assert isinstance(signature, str)

    webhook_secret = os.environ["WEBHOOK_SECRET"]

    expected = (
        "sha256="
        + hmac.new(
            webhook_secret.encode("ascii"),
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


class EnumPrAction(enum.StrEnum):
    EDITED = "edited"
    LABELED = "labeled"
    OPENED = "opened"
    CONVERTED_TO_DRAFT = "converted_to_draft"
    REOPENED = "reopened"
    REVIEW_REQUESTED = "review_requested"
    CLOSED = "closed"
    MILESTONED = "milestoned"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    SYNCHRONIZE = "synchronize"
    UNASSIGEND = "unassigned"
    ASSIGNED = "assigned"


class EnumPrState(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"


@dataclasses.dataclass(frozen=True, repr=True)
class Webhook:
    filename: str
    action: str
    repo: str
    pr_number: int
    pr_url: str
    pr_state: str
    branch_name: str
    author: str
    commit: str

    @staticmethod
    def factory(filename: pathlib.Path, dict_json: dict[str, typing.Any]) -> Webhook:
        return Webhook(
            filename=filename.name,
            action=dict_json["action"],
            repo=dict_json["repository"]["name"],
            pr_number=dict_json["pull_request"]["number"],
            pr_url=dict_json["pull_request"]["url"],
            pr_state=dict_json["pull_request"]["state"],
            branch_name=dict_json["pull_request"]["head"]["ref"],
            author=dict_json["pull_request"]["head"]["user"]["login"],
            commit=dict_json["pull_request"]["head"]["sha"],
        )


class Webhooks(list[Webhook]):
    @property
    def pr_numbers(self) -> list[int]:
        pr_numbers: set[int] = set()
        for w in self:
            pr_numbers.add(w.pr_number)
        return sorted(pr_numbers)

    def purge(self) -> Webhooks:
        to_purge = Webhooks()
        for pr_number in self.pr_numbers:
            to_purge.extend(self.purge_pr(pr_number=pr_number))
        return to_purge

    def purge_pr(self, pr_number: int) -> Webhooks:
        files = [w for w in self if w.pr_number == pr_number]
        files.sort(key=lambda f: f.filename, reverse=True)
        for i, file in enumerate(files):
            if file.action in EnumPrAction.SYNCHRONIZE.value:
                # Purge all files OLDER that this one
                return Webhooks(files[i + 1 :])
        assert len(files) > 0
        if files[0].pr_state != EnumPrState.OPEN.value:
            # If the pr is not open anymore: Purge all!
            return Webhooks(files)
        return Webhooks()


def get_list_hooks() -> Webhooks:
    directory_todo = repo_directory_name(
        # repo="hmaerki/experiment_webhook_PR",
        repo="micropython/micropython",
        enumdone=EnumDone.TODO,
    )
    return get_list_hooks2(directory=directory_todo)


def get_list_hooks2(directory) -> Webhooks:
    list_hooks = Webhooks()
    for filename in directory.glob("*.json"):
        with filename.open("r") as f:
            dict_json = json.load(f)
            try:
                webhook = Webhook.factory(filename=filename, dict_json=dict_json)
                list_hooks.append(webhook)
            except KeyError as e:
                logger.warning(f"{filename}: Failed to read: {e}")

    return list_hooks
