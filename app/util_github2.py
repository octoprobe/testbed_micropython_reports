from __future__ import annotations

import dataclasses
import datetime
import json
import logging
import pathlib
import re
import shutil
import time

from markupsafe import Markup
from octoprobe.util_cached_git_repo import GitMetadata, GitSpec
from testbed_micropython.report_test import util_constants
from testbed_micropython.report_test.util_baseclasses import ResultContext
from testbed_micropython.report_test.util_push_testresults import (
    DirectoryManualWorkflow,
)

from app.constants import (
    DIRECTORY_REPORTS,
    DIRECTORY_REPORTS_METADATA,
    FILENAME_EXPIRY,
    FILENAME_GH_LIST_JSON,
    FILENAME_INPUTS_JSON,
    GITHUB_PREFIX,
    GITHUB_WORKFLOW,
)
from app.util_github import FormStartJob, gh_list2

logger = logging.getLogger(__file__)


@dataclasses.dataclass(slots=True)
class WorkflowInput:
    arguments: str = ""
    "Example: --only-board=ADA_ITSYBITSY_M0"
    email_testreport: str = ""
    "Example: buhtig.hans.maerki@ergoinfo.ch"
    repo_firmware: str = ""
    "Example: https://github.com/micropython/micropython.git@master"
    repo_tests: str = ""
    "Example: https://github.com/dpgeorge/micropython.git@tools-pyboard-add-serial-timeout"
    pullrequests: str = ""
    "TODO: Remove - obsolete"

    def __post_init__(self) -> None:
        pass

    @property
    def repo_firmware_markup(self) -> Markup:
        "Example: https://github.com/micropython/micropython.git@master"
        return self._repo_to_markup(self.repo_firmware)

    @property
    def repo_tests_markup(self) -> Markup:
        "Example: https://github.com/dpgeorge/micropython.git@tools-pyboard-add-serial-timeout"
        return self._repo_to_markup(self.repo_tests)

    @staticmethod
    def _repo_to_markup(git_ref: str) -> Markup:
        git_spec = GitSpec.parse(git_ref=git_ref)
        return Markup(f'<a href="{git_spec.url_link}" target="_blank">{git_ref}</a>')


def save_as_workflow_input(
    form_startjob: FormStartJob,
    directory_metadata: pathlib.Path,
) -> None:
    def space(text: str | None) -> str:
        return "" if text is None else text

    workflow_input = WorkflowInput(
        arguments=space(form_startjob.arguments),
        email_testreport=form_startjob.username,
        repo_firmware=space(form_startjob.repo_firmware),
        repo_tests=space(form_startjob.repo_tests),
    )
    json_text = json.dumps(dataclasses.asdict(workflow_input), indent=4, sort_keys=True)
    filename = directory_metadata / FILENAME_INPUTS_JSON
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(json_text)


@dataclasses.dataclass(slots=True)
class WorkflowJob:
    attempt: int
    "Example: 1"
    conclusion: str
    "Example: failure"
    createdAt: str  # pylint: disable=invalid-name
    "Example: 2025-05-27T02:00:25Z"
    event: str
    "Example: workflow_dispatch"
    name: str
    "Example: selfhosted_testrun"
    number: int
    "Example: 4"
    startedAt: str  # pylint: disable=invalid-name
    "Example: 2025-05-27T02:00:25Z"
    status: str
    "Example: completed"
    updatedAt: str  # pylint: disable=invalid-name
    "Example: 2025-05-27T04:01:16Z"
    url: str
    "Example: https://github.com/octoprobe/testbed_micropython/actions/runs/15265040909"

    def __post_init__(self) -> None:
        pass

    @staticmethod
    def convert_time(text: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(text)
        # Convert ISO 8601 string with 'Z' (UTC) to datetime.datetime
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.UTC
        )

    @property
    def started_at(self) -> datetime.datetime:
        # Convert ISO 8601 string with 'Z' (UTC) to datetime.datetime
        return self.convert_time(self.startedAt)

    @property
    def started_at_text(self) -> str:
        return self.started_at.strftime(util_constants.FORMAT_HTTP_STARTED_AT)

    @property
    def duration(self) -> datetime.timedelta:
        return self.convert_time(self.updatedAt) - self.started_at

    @property
    def duration_text(self) -> str:
        # seconds = 7975  # 2h, 12min, 55sec

        return util_constants.seconds_to_duration(seconds=self.duration.seconds)

    @property
    def base_directory(self) -> str:
        return self.static_base_directory(name=self.name, number=self.number)
        return f"{GITHUB_PREFIX}{self.name}_{self.number}"

    @classmethod
    def static_base_directory(cls, name: str, number: int) -> str:
        return f"{GITHUB_PREFIX}{name}_{number}"

    @property
    def directory_metadata(self) -> pathlib.Path:
        return self.static_directory_metadata(name=self.name, number=self.number)

    @classmethod
    def static_directory_metadata(cls, name: str, number: int) -> pathlib.Path:
        return DIRECTORY_REPORTS_METADATA / cls.static_base_directory(
            name=name, number=number
        )


EXPIRY_TRASH = "trash"
EXPIRY_NEVER = "never"


@dataclasses.dataclass(slots=True)
class WorkflowExpiry:
    tag: str
    "hmaerki"
    expiry: str
    "Example: 2025-05-27"

    @property
    def expired(self) -> bool:
        """
        Compare the expiry date with the current time.
        Return whether this report has expired.
        """
        if self.expiry == EXPIRY_NEVER:
            return False

        if self.expiry == EXPIRY_TRASH:
            return True

        now_date = WorkflowExpiry.format_expiry(0)
        return now_date > self.expiry

    @staticmethod
    def format_expiry(days: int) -> str:
        """
        Return the expiry date in the form "2025-08-16"
        """
        d = time.time() + days * 24 * 3600
        return datetime.datetime.fromtimestamp(d).strftime("%Y-%m-%d")

    @staticmethod
    def default() -> WorkflowExpiry:
        return WorkflowExpiry(tag="", expiry=WorkflowExpiry.format_expiry(30))

    def write(self, workflow_unique_id: str) -> None:
        base_directory = workflow_unique_id
        filename = DIRECTORY_REPORTS_METADATA / base_directory / FILENAME_EXPIRY
        filename.parent.mkdir(parents=True, exist_ok=True)
        json_text = json.dumps(dataclasses.asdict(self), indent=4)
        filename.write_text(json_text)

    def trash(self, workflow_unique_id: str) -> bool:
        base_directory = workflow_unique_id
        directory = DIRECTORY_REPORTS / base_directory
        if directory.is_dir():
            shutil.rmtree(directory, ignore_errors=True)
            return True
        return False

    @staticmethod
    def read_or_default(workflow_unique_id: str) -> WorkflowExpiry:
        base_directory = workflow_unique_id
        expiry_json = DIRECTORY_REPORTS_METADATA / base_directory / FILENAME_EXPIRY
        if expiry_json.is_file():
            try:
                json_text = expiry_json.read_text()
                json_dict = json.loads(json_text)
                return WorkflowExpiry(**json_dict)
            except Exception as e:
                logger.debug(f"{expiry_json}: {e!r}")

        workflow_expiry = WorkflowExpiry.default()
        workflow_expiry.write(workflow_unique_id=workflow_unique_id)
        return workflow_expiry


class BaseDirectory:
    """
    Example          self.text    self.number self.sortable
    testresults_100  testresults_ 100         testresults_00100
    testresults_92   testresults_ 92          testresults_00092
    testresults_97   testresults_ 97          testresults_00097
    """

    RE_NUMBER = re.compile(r"(?P<text>[^\d]+)(?P<number>\d+)")
    """
    "testresults_100" -> "testresults_", "100"
    """

    def __init__(self, base_directory: str) -> None:
        assert isinstance(base_directory, str)
        self.base_directory = base_directory

        self.is_github_workflow = GITHUB_WORKFLOW in self.base_directory
        """
        True if: github_selfhosted_testrun_420
        False if: local_hostname_20250116-185542
        """

        self.manual_workflow = DirectoryManualWorkflow.factory_directory(base_directory)
        """
        None if: github_selfhosted_testrun_420
        otherwise: local_hostname_20250116-185542
        """

        assert (self.manual_workflow is None) is (self.is_github_workflow)

        # local_hostname_20250116-185542
        self.number = 0
        self.text = self.base_directory

        if self.manual_workflow is None:
            # github_selfhosted_testrun_420
            match = self.RE_NUMBER.match(base_directory)
            assert match is not None, base_directory
            _number = match.group("number")
            assert _number is not None, base_directory
            self.number = int(_number)
            self.text = match.group("text")
            assert self.text is not None, base_directory

    @property
    def sortable(self) -> str:
        return f"{self.text}_{self.number:010d}"
        # if self.is_github_workflow:
        #     return f"{self.text}_{self.number:010d}"
        # return self.base_directory


@dataclasses.dataclass(slots=True)
class WorkflowReport:
    base_directory: BaseDirectory
    job: WorkflowJob | None
    expiry: WorkflowExpiry
    input: WorkflowInput | None
    result_context: ResultContext | None

    def __post_init__(self) -> None:
        assert isinstance(self.base_directory, BaseDirectory)
        assert isinstance(self.job, WorkflowJob | None)
        assert isinstance(self.expiry, WorkflowExpiry)
        assert isinstance(self.input, WorkflowInput | None)
        assert isinstance(self.result_context, ResultContext | None)

    @classmethod
    def factory(cls, base_directory: str) -> WorkflowReport:
        workflow_job: WorkflowJob | None = None
        workflow_input: WorkflowInput | None = None
        workflow_expiry = WorkflowExpiry.default()
        result_context: ResultContext | None = None

        gh_list_json = (
            DIRECTORY_REPORTS_METADATA / base_directory / FILENAME_GH_LIST_JSON
        )
        if gh_list_json.is_file():
            try:
                json_text = gh_list_json.read_text()
                json_dict = json.loads(json_text)
                workflow_job = WorkflowJob(**json_dict)
            except Exception as e:
                logger.debug(f"{gh_list_json}: {e!r}")

        workflow_expiry = WorkflowExpiry.read_or_default(
            workflow_unique_id=base_directory
        )

        inputs_json = DIRECTORY_REPORTS / base_directory / FILENAME_INPUTS_JSON
        if not inputs_json.is_file():
            # Metadata fallback
            inputs_json = (
                DIRECTORY_REPORTS_METADATA / base_directory / FILENAME_INPUTS_JSON
            )
        if inputs_json.is_file():
            try:
                json_text = inputs_json.read_text()
                json_dict = json.loads(json_text)
                workflow_input = WorkflowInput(**json_dict)
            except Exception as e:
                logger.debug(f"{gh_list_json}: {e!r}")

        context_json = (
            DIRECTORY_REPORTS / base_directory / util_constants.FILENAME_CONTEXT_JSON
        )
        if context_json.is_file():
            try:
                json_text = context_json.read_text()
                json_dict = json.loads(json_text)
                result_context = ResultContext.from_dict(json_dict=json_dict)
            except Exception as e:
                logger.debug(f"{gh_list_json}: {e!r}")

        return WorkflowReport(
            base_directory=BaseDirectory(base_directory=base_directory),
            job=workflow_job,
            expiry=workflow_expiry,
            input=workflow_input,
            result_context=result_context,
        )

    @property
    def github_action_markup(self) -> Markup:
        if self.base_directory.manual_workflow is not None:
            # For example 'local_hostname_20250116_185542'
            return Markup(self.base_directory.manual_workflow.date_short)
        number = self.base_directory.number
        if self.job is None:
            return Markup(str(number))

        return Markup(
            f'<a href="{self.job.url}" target="_blank" title="github action">{number}</a>'
        )

    @property
    def is_github_workflow(self) -> bool:
        return self.base_directory.is_github_workflow

    @property
    def conclusion_status_markup(self) -> Markup:
        def markup(conclusion: str) -> Markup:
            link = (
                f"/{self.base_directory.base_directory}/octoprobe_summary_report.html"
            )
            return Markup(
                f'<a href="{link}" target="_blank" title="Summary Report">{conclusion}</a>'
            )

        if not self.is_github_workflow:
            # This reports where sent from a manually started 'mptest'
            return markup(conclusion="success")
        if self.job is None:
            return Markup("???")
        if self.job.status in ("in_progress", "queued"):
            return Markup(self.job.status)
        if not (DIRECTORY_REPORTS / self.base_directory.base_directory).is_dir():
            return Markup("missing")
        return markup(conclusion=self.job.conclusion)

    @property
    def repo_tests_commit_markup(self) -> Markup:
        if self.result_context is None:
            return Markup()
        return self._commit_markup(self.result_context.ref_tests_metadata)

    @property
    def repo_firmware_commit_markup(self) -> Markup:
        if self.result_context is None:
            return Markup()
        return self._commit_markup(self.result_context.ref_firmware_metadata)

    def _commit_markup(self, metadata: GitMetadata | None) -> Markup:
        if metadata is None:
            return Markup()
        assert isinstance(metadata, GitMetadata), metadata
        try:
            href_commit = f'<a href={metadata.url_commit_hash} target="_blank" title="{metadata.commit_comment}">{metadata.commit_comment}</a>'
            return Markup(href_commit)
        except:  # noqa: E722  # pylint: disable=bare-except
            return Markup()

    @property
    def unique_id(self) -> str:
        return self.base_directory.base_directory

    @property
    def expiry_dialog_id(self) -> str:
        return f"expiry-dialog-{self.base_directory.base_directory}"

    @property
    def select_option_markup(self) -> Markup:
        """
        <option value="{{ workflow_report.expiry.expiry }}">{{ workflow_report.expiry.expiry }}</option>
        <option value="never">never</option>
        <option value="trash">trash</option>
        """
        values: list[tuple[str, str]] = []

        assert self.expiry is not None
        values.append((self.expiry.expiry, self.expiry.expiry))
        for days, text in (
            (1, "1 day"),
            (7, "1 week"),
            (30, "1 month"),
            (180, "6 month"),
        ):
            date_text = WorkflowExpiry.format_expiry(days)
            values.append((date_text, text))
        values.append((EXPIRY_NEVER, "Never"))
        values.append((EXPIRY_TRASH, "Trash now!!!"))

        return Markup("".join([f'<option value="{d}">{t}</option>' for d, t in values]))

    @property
    def expired(self) -> bool:
        return self.expiry.expired

    @property
    def trash_if_expired(self) -> bool:
        if self.expiry.expired:
            return self.expiry.trash(workflow_unique_id=self.unique_id)

        return False

    @property
    def started_at_text(self) -> str:
        if self.job is None:
            assert self.base_directory.manual_workflow is not None
            return self.base_directory.manual_workflow.datetime_text
        return self.job.started_at_text

    @property
    def duration_text(self) -> str:
        if self.result_context is not None:
            return Markup(self.result_context.time_duration_text)
        if self.job is None:
            return "-"
        return self.job.duration_text

    @property
    def repo_firmware_markup(self) -> Markup | str:
        if self.input is None:
            assert self.result_context is not None
            return self.result_context.ref_firmware
        return self.input.repo_firmware_markup

    @property
    def repo_tests_markup(self) -> Markup | str:
        if self.input is None:
            assert self.result_context is not None
            return self.result_context.ref_tests
        return self.input.repo_tests_markup

    @property
    def email_testreport(self) -> str:
        if self.input is None:
            return self.base_directory.base_directory
        return self.input.email_testreport

    @property
    def arguments(self) -> str:
        if self.input is None:
            assert self.result_context is not None
            return self.result_context.commandline
        return self.input.arguments


def gh_list() -> pathlib.Path | None:
    """
    Saves the state of each job in 'directory_metadata / FILENAME_GH_LIST_JSON'.
    Returns directory_metadata for the next job beeing started.
    """
    next_directory_metadata: pathlib.Path | None = None
    jobs = gh_list2()
    for json_job in jobs:
        workflow_job = WorkflowJob(**json_job)  # type: ignore[arg-type]
        if next_directory_metadata is None:
            next_directory_metadata = WorkflowJob.static_directory_metadata(
                name=workflow_job.name, number=workflow_job.number + 1
            )
        json_text = json.dumps(json_job, indent=4, sort_keys=True)
        filename = workflow_job.directory_metadata / FILENAME_GH_LIST_JSON
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json_text)

    return next_directory_metadata


def list_reports(including_expired=False) -> list:
    def report_names() -> set[str]:
        set_reports = set()
        for d in (DIRECTORY_REPORTS, DIRECTORY_REPORTS_METADATA):
            for f in d.glob(pattern="*"):
                if f.is_dir():
                    set_reports.add(f.name)
        return set_reports

    workflows = [
        WorkflowReport.factory(base_directory) for base_directory in report_names()
    ]
    if not including_expired:
        workflows = [w for w in workflows if not w.expired]
    return sorted(
        workflows,
        key=lambda wr: wr.base_directory.sortable,
        reverse=True,
    )
