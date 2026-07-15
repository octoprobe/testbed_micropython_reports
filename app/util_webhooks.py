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

from . import util_github, util_github2, util_validate

logger = logging.getLogger(__file__)

REPO_MICROPYTHON = "micropython/micropython"
REPO_EXPERIMENT = "hmaerki/experiment_webhook_PR"

ACTIVATE_FOR_AUTHORS = (
    "agatti",
    "andrewleech",
    "dpgeorge",
    "gadgetoid",
    "hmaerki",
    "micropython",
    "octoprobe-bot",
    "projectgus",
    # "jonnor",
    # "josverl",
    # "mattytrentini",
    # "pimoroni",
    # "ricksorensen",
    # "robert-hh",
)
assert any(a.islower() for a in ACTIVATE_FOR_AUTHORS)


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
    repo_directory = constants.DIRECTORY_REPORTS_WEBHOOK / repo_text / enumdone.value
    repo_directory.mkdir(parents=True, exist_ok=True)
    return repo_directory


def save_webhook(x_github_event: str, payload: dict[str, typing.Any]) -> None:
    assert isinstance(x_github_event, str)
    assert isinstance(payload, dict)

    action = payload.get("action", "ping")

    pr_number = 0
    repo: str = payload["repository"]["full_name"]
    try:
        pr_number = payload["pull_request"]["number"]
    except KeyError:
        pass

    now_text = util_testreport.now_formatted()
    filename = "-".join(
        [
            now_text,
            x_github_event,
            action,
            f"{pr_number:06d}.json",
        ]
    )
    repo_directory = repo_directory_name(repo=repo, enumdone=EnumDone.TODO)
    filename_json = repo_directory / filename
    filename_json.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"webhook: repo:{repo}, event:{x_github_event}, action:{action}, #{pr_number}, filename:{filename_json}"
    )
    with filename_json.open("w") as f:
        json.dump(obj=payload, fp=f, indent=4)


class EnumAction(enum.StrEnum):
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


def run_job3(repo: str, webhook_job: Webhook) -> bool:
    """
    return True if a Octoprobe action has been started
    """
    logger.info(f"run_job3(repo={repo}, pr_number={webhook_job.pr_number})")
    form_startjob = util_github.FormStartJob(
        pr_number=str(webhook_job.pr_number),
        pr_repo=repo,
    )
    form_rc_pr = util_validate.validate_pr(form_startjob=form_startjob)
    if len(form_rc_pr.micropython_ports) == 0:
        logger.info(
            f"{repo=}: {webhook_job.filename}: Skipped as no micropython_ports to be tested!"
        )
        return False

    util_github2.run_job2(form_startjob=form_startjob)
    return True


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

    def purge_to_directory_by_repo(self, repo: str) -> None:
        Webhooks([self]).purge_to_directory_by_repo(repo=repo)


class Webhooks(list[Webhook]):
    @property
    def next_job(self) -> Webhook | None:
        """
        From all hook:
         * filter 'synchronized'.
         * filter by ACTIVATE_FOR_AUTHORS
        Return the newest hook.
        """
        next_jobs = self.next_jobs
        if len(next_jobs) == 0:
            return None
        return next_jobs[0]

    @property
    def next_jobs(self) -> list[Webhook]:
        hooks_synchronized: dict[int, Webhook] = {}
        for hook in sorted(self, key=lambda f: f.filename):
            if hook.action != EnumAction.SYNCHRONIZE.value:
                continue
            if hook.author.lower() not in ACTIVATE_FOR_AUTHORS:
                continue
            hooks_synchronized[hook.pr_number] = hook

        hooks = sorted(
            hooks_synchronized.values(),
            key=lambda h: h.filename,
            reverse=True,
        )
        return hooks

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
            if file.action in EnumAction.SYNCHRONIZE.value:
                # Purge all files OLDER that this one
                return Webhooks(files[i + 1 :])
        assert len(files) > 0
        if files[0].pr_state != EnumPrState.OPEN.value:
            # If the pr is not open anymore: Purge all!
            return Webhooks(files)
        return Webhooks()

    def purge_to_directory(
        self,
        directory_todo: pathlib.Path,
        directory_done: pathlib.Path,
    ) -> None:
        for w in self:
            filename_todo = directory_todo / w.filename
            filename_done = directory_done / w.filename
            logger.debug(f"{directory_todo} -> {directory_done}: Purge {w.filename}")
            filename_todo.rename(filename_done)

    def purge_to_directory_by_repo(self, repo: str) -> None:
        directory_todo = repo_directory_name(repo=repo, enumdone=EnumDone.TODO)
        directory_done = repo_directory_name(repo=repo, enumdone=EnumDone.DONE)
        self.purge_to_directory(
            directory_todo=directory_todo,
            directory_done=directory_done,
        )

    @classmethod
    def purge_by_repo(cls, repo: str) -> None:
        """
        Purge files from folder 'todo' to 'done'.
        """
        hooks = Webhooks.from_directory_by_repo(repo=repo)
        hooks_to_purge = hooks.purge()
        logger.info(f"hooks_to_purge={len(hooks_to_purge)}")
        hooks_to_purge.purge_to_directory_by_repo(repo=repo)

    @classmethod
    def recurring_job(cls, repo: str) -> bool:
        """
        return True if a Octoprobe action has been started
        """
        cls.purge_by_repo(repo=repo)
        hooks = cls.from_directory_by_repo(repo=repo)
        webhook_job = hooks.next_job
        if webhook_job is not None:
            webhook_job.purge_to_directory_by_repo(repo=repo)
            started = run_job3(repo=repo, webhook_job=webhook_job)
            if started:
                return True

        return False

    @classmethod
    def from_directory_by_repo(cls, repo: str) -> Webhooks:
        directory_todo = repo_directory_name(repo=repo, enumdone=EnumDone.TODO)
        return cls.from_directory(directory=directory_todo)

    @classmethod
    def from_directory(cls, directory: pathlib.Path) -> Webhooks:
        hooks = Webhooks()
        for filename in directory.glob("*.json"):
            with filename.open("r") as f:
                dict_json = json.load(f)
                try:
                    webhook = Webhook.factory(filename=filename, dict_json=dict_json)
                    hooks.append(webhook)
                except KeyError as e:
                    logger.warning(f"{filename}: Failed to read: {e}")

        return hooks


@dataclasses.dataclass(frozen=True)
class Repo:
    repo: str

    @property
    def hooks(self) -> Webhooks:
        return Webhooks.from_directory_by_repo(repo=self.repo)

    @property
    def next_jobs(self) -> list[Webhook]:
        hooks = Webhooks.from_directory_by_repo(repo=self.repo)
        return hooks.next_jobs[:20]


REPOS = [Repo(r) for r in (REPO_MICROPYTHON, REPO_EXPERIMENT)]
