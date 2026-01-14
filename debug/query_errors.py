"""
Goal: Quickly summarize error patterns

https://reports.octoprobe.org/github_selfhosted_testrun_327/RUN-TESTS_STANDARD,a@5f2c-RPI_PICO_W/unicode_unicode_ure.py.out
  could not enter raw repl
  CRASH

https://reports.octoprobe.org/github_selfhosted_testrun_327/RUN-TESTS_STANDARD,b@2d2d-LOLIN_D1_MINI/basics_assign_expr_syntaxerror.py.out
  could not enter raw repl
  CRASH

https://reports.octoprobe.org/github_selfhosted_testrun_348/RUN-TESTS_STANDARD_NATIVE,c@5f2c-RPI_PICO_W/basics_int_bytes_int64.py.out
  enter_raw_repl failed
"""

from __future__ import annotations

import dataclasses
import pathlib
import re

import click

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_REPORTS = DIRECTORY_OF_THIS_FILE.parent / "reports"
assert DIRECTORY_REPORTS.is_dir()

RE_TESTRUN_DIRECTORY = re.compile(r"^([a-z_]+)(?P<number>\d+)$")
"""
github_selfhosted_testrun_20
github_selfhosted_testrun_201
"""


@dataclasses.dataclass(frozen=True, repr=True)
class TestrunDirectory:
    path: pathlib.Path
    number: int

    @staticmethod
    def factory(directory: pathlib.Path) -> TestrunDirectory:
        assert isinstance(directory, pathlib.Path)
        match = RE_TESTRUN_DIRECTORY.match(directory.name)
        assert match is not None, directory.name
        return TestrunDirectory(
            path=directory,
            number=int(match.group("number")),
        )


RE_RESULT_DIRECTORY = re.compile(
    r"^(?P<label>[A-Z_-]+),(?P<testrun>[a-z])@(?P<tentacle>.*)$"
)
"""
RUN-TESTS_NET_HOSTED,a@472b-ESP32_S3_DEVKIT
"""


@dataclasses.dataclass(frozen=True, repr=True)
class ReportTentacle:
    testrun: int
    tentacle: str
    repl_errors: int = 0


@dataclasses.dataclass(frozen=True, repr=True)
class Report:
    testruns: tuple[int, ...]
    tentacles: tuple[str, ...]
    testnames: tuple[str, ...]
    patterns: tuple[str, ...]

    reports: list[ReportTentacle] = dataclasses.field(default_factory=list)

    def process(self, directory_reports: pathlib.Path):
        """Query error patterns from octoprobe test results."""
        directories = list(directory_reports.glob("github_selfhosted_testrun_*"))
        directories = [d for d in directories if d.is_dir()]
        directories = [TestrunDirectory.factory(d) for d in directories]
        directories = [d for d in directories if d.number in self.testruns]
        directories = sorted(directories, key=lambda d: d.number, reverse=True)

        for testrun_directory in directories:
            self.process_project(testrun_directory=testrun_directory)

    def process_project(self, testrun_directory: TestrunDirectory) -> None:
        failures = GroupFailures(testrun_directory=testrun_directory)

        for directory in testrun_directory.path.glob("RUN-*"):
            group_result = GroupResult.factory(directory=directory)
            if group_result.label not in self.testnames:
                continue
            if group_result.tentacle not in self.tentacles:
                continue
            failures.group_results.append(group_result)
            # print(f"  {group_result}")
            for filename in directory.glob("*.out"):
                text = filename.read_text(errors="ignore")
                for pattern in self.patterns:
                    if pattern in text:
                        group_result.failures.append(filename.name)
                        break
            self.reports.append(
                ReportTentacle(
                    testrun=testrun_directory.number,
                    tentacle=group_result.tentacle,
                    repl_errors=len(group_result.failures),
                )
            )

        # print(f"  {testrun_directory.number} repl_errors={failures.repl_errors}")

    def print(self) -> None:
        for tentacle in self.tentacles:
            print(f"Tentacle '{tentacle}")
            for testrun in self.testruns:
                repl_errors = 0
                for report in self.reports:
                    if report.tentacle != tentacle:
                        continue
                    if report.testrun != testrun:
                        continue
                    repl_errors += report.repl_errors
                print(f"  {testrun} {repl_errors}")


@dataclasses.dataclass(frozen=True, repr=True)
class GroupResult:
    path: pathlib.Path
    label: str
    testrun: str
    tentacle: str
    failures: list[str] = dataclasses.field(default_factory=list)

    @staticmethod
    def factory(directory: pathlib.Path) -> GroupResult:
        assert isinstance(directory, pathlib.Path)
        match = RE_RESULT_DIRECTORY.match(directory.name)
        assert match is not None, directory.name
        return GroupResult(
            path=directory,
            label=match.group("label"),
            testrun=match.group("testrun"),
            tentacle=match.group("tentacle"),
        )

    @property
    def repl_errors(self) -> int:
        return len(self.failures)


@dataclasses.dataclass(frozen=True, repr=True)
class GroupFailures:
    testrun_directory: TestrunDirectory
    group_results: list[GroupResult] = dataclasses.field(default_factory=list)

    @property
    def repl_errors(self) -> int:
        return sum([r.repl_errors for r in self.group_results])


@click.command()
@click.option(
    "--testrun",
    multiple=True,
    type=int,
    help="can be used multiple times",
)
@click.option(
    "--testname",
    multiple=True,
    type=str,
    help="can be used multiple times",
)
@click.option(
    "--tentacle",
    multiple=True,
    type=str,
    help="can be used multiple times",
)
@click.option(
    "--pattern",
    multiple=True,
    type=str,
    help="can be used multiple times",
)
def main(
    testrun: tuple[int, ...],
    testname: tuple[str, ...],
    tentacle: tuple[str, ...],
    pattern: tuple[str, ...],
) -> None:
    report = Report(
        testruns=testrun,
        testnames=testname,
        tentacles=tentacle,
        patterns=pattern,
    )
    report.process(DIRECTORY_REPORTS)
    report.print()


if __name__ == "__main__":
    main()
