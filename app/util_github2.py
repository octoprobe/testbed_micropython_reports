from __future__ import annotations

import dataclasses
import datetime
import json
import pathlib
import re

from markupsafe import Markup
from octoprobe.util_cached_git_repo import GitSpec

from app.constants import (
    DIRECTORY_REPORTS,
    DIRECTORY_REPORTS_METADATA,
    FILENAME_GH_LIST_JSON,
    FILENAME_INPUTS_JSON,
    GITHUB_PREFIX,
    GITHUB_WORKFLOW,
)
from app.util_github import FormStartJob, gh_list2


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
    def started_at_markup(self) -> str:
        return self.started_at.strftime("%Y-%m-%d_%H:%M")

    @property
    def duration(self) -> datetime.timedelta:
        return self.convert_time(self.updatedAt) - self.started_at

    @property
    def duration_markup(self) -> Markup:
        seconds = self.duration.seconds
        # seconds = 7975  # 2h, 12min, 55sec

        def split(value: int) -> list[int]:
            if value < 60:
                return [value]
            return split(value // 60) + [value % 60]

        def split2(seconds: int) -> list[int]:
            h = seconds // 3600
            seconds -= h * 3600
            m = seconds // 60
            seconds -= m * 60
            return [h, m, seconds]

        elements = split2(seconds)
        return Markup(":".join([format(e, "02d") for e in elements]))

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


@dataclasses.dataclass(slots=True)
class WorkflowReport:
    base_directory: BaseDirectory
    job: WorkflowJob | None
    input: WorkflowInput | None

    def __post_init__(self) -> None:
        assert isinstance(self.base_directory, BaseDirectory)
        assert isinstance(self.job, WorkflowJob | None)
        assert isinstance(self.input, WorkflowInput | None)

    @classmethod
    def factory(cls, base_directory: str) -> WorkflowReport:
        workflow_job = None
        workflow_input = None

        gh_list_json = (
            DIRECTORY_REPORTS_METADATA / base_directory / FILENAME_GH_LIST_JSON
        )
        if gh_list_json.is_file():
            try:
                json_text = gh_list_json.read_text()
                json_dict = json.loads(json_text)
                workflow_job = WorkflowJob(**json_dict)
            except FileNotFoundError as e:
                raise FileNotFoundError(f"{gh_list_json}: {e}") from e
            except Exception as e:
                raise Exception(f"{gh_list_json}: {e}") from e

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
            except FileNotFoundError as e:
                raise FileNotFoundError(f"{inputs_json}: {e}") from e
            except Exception as e:
                raise Exception(f"{inputs_json}: {e}") from e
        return WorkflowReport(
            base_directory=BaseDirectory(base_directory=base_directory),
            job=workflow_job,
            input=workflow_input,
        )

    @property
    def github_action_markup(self) -> Markup:
        number = self.base_directory.number
        if self.job is None:
            return Markup(str(number))

        return Markup(
            f'<a href="{self.job.url}" target="_blank" title="github action">{number}</a>'
        )

    @property
    def conclusion_status_markup(self) -> Markup:
        if self.job is None:
            return Markup("???")
        if self.job.status in ("in_progress", "queued"):
            return Markup(self.job.status)
        if not (DIRECTORY_REPORTS / self.base_directory.base_directory).is_dir():
            return Markup("missing")
        link = f"/{self.base_directory.base_directory}/octoprobe_summary_report.html"
        return Markup(
            f'<a href="{link}" target="_blank" title="Summary Report">{self.job.conclusion}</a>'
        )


def gh_list() -> pathlib.Path | None:
    """
    Saves the state of each job in 'directory_metadata / FILENAME_GH_LIST_JSON'.
    Returns directory_metadata for the next job beeing started.
    """
    next_directory_metadata: pathlib.Path | None = None
    jobs = gh_list2()
    for json_job in jobs:
        workflow_job = WorkflowJob(**json_job)
        if next_directory_metadata is None:
            next_directory_metadata = WorkflowJob.static_directory_metadata(
                name=workflow_job.name, number=workflow_job.number + 1
            )
        json_text = json.dumps(json_job, indent=4, sort_keys=True)
        filename = workflow_job.directory_metadata / FILENAME_GH_LIST_JSON
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(json_text)

    return next_directory_metadata


def render_reports() -> list:
    def report_names_sorted() -> set[str]:
        set_reports = set()
        for d in (DIRECTORY_REPORTS, DIRECTORY_REPORTS_METADATA):
            for f in d.glob(pattern="*"):
                if f.is_dir():
                    if f.name.find(GITHUB_WORKFLOW) >= 0:
                        set_reports.add(f.name)
        return set_reports

    return sorted(
        [
            WorkflowReport.factory(base_directory)
            for base_directory in report_names_sorted()
        ],
        key=lambda wr: wr.base_directory.sortable,
        reverse=True,
    )
