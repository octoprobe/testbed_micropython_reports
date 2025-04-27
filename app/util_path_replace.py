from __future__ import annotations

import dataclasses
import html
import itertools
import logging
import re
import typing

from markupsafe import Markup

from .util_html import Segments

logger = logging.Logger(__file__)

RE_ENDOF_PATH = re.compile(r"( |\n|\\n|\'|\"|$)")

RE_LOGGER = re.compile(r"")


@dataclasses.dataclass
class PathMatch:
    """
    Example path_trigger:
      "/home/testresults",
    Example log:
      AA /home/testresults/RUN-TESTS_EXTMOD_HARDWARE/testresults.txt BB
      <a><---b-----------><---------------c------------------------><d>

      a path_before    "AA "
      b path_trigger   "/home/testresults"
      c path_relevant  "/RUN-TESTS_EXTMOD_HARDWARE/testresults.txt"
      d path_after     " BB"
    """

    path_before: str
    path_relevant: str
    path_after: str

    @staticmethod
    def factory(line_before: str, path_trigger: str) -> PathMatch | None:
        # Find path begin
        pos = line_before.find(path_trigger)
        if pos == -1:
            return None

        path_trigger_after = line_before[pos + len(path_trigger) :]

        # Find remaining path
        pos_endof_path = PathMatch.pos_end_of_path(path=path_trigger_after)
        path_relevant = path_trigger_after[0:pos_endof_path]

        for c_check in (")", "'"):
            if path_relevant.endswith(")"):
                logger.warning(f"{c_check}: {path_relevant=}")

        return PathMatch(
            path_before=line_before[0:pos],
            path_relevant=path_relevant,
            path_after=path_trigger_after[pos_endof_path:],
        )

    @staticmethod
    def pos_end_of_path(path: str) -> int:
        match_trigger_after = RE_ENDOF_PATH.search(path)
        assert match_trigger_after is not None
        return match_trigger_after.regs[0][0]

    def href(self, url) -> Markup:
        href = f"{url}/{self.path_relevant}"
        href = href.replace("//", "/").replace("//", "/")
        return Markup(
            f'<a href="{href}">{html.escape(self.path_relevant_readable)}</a>'
        )

    def line_with_href(self, url: str) -> Segments:
        return Segments(
            [
                self.path_before,
                self.href(url),
                self.path_after,
            ]
        )

    def line_without_href(self) -> Segments:
        path_relevant = self.path_relevant.lstrip("/")
        return Segments(
            [
                self.path_before,
                Markup(path_relevant),
                self.path_after,
            ],
        )

    @property
    def path_relevant_readable(self) -> str:
        if self.path_relevant == "":
            return "."
        if self.path_relevant.startswith("/"):
            return self.path_relevant[1:]
        return self.path_relevant


class PathReplace:
    def __init__(
        self, directories: dict[str, str], git_ref: dict[str, str], urls: dict[str, str]
    ) -> None:
        self.directories = directories
        self.git_ref = git_ref
        self.urls = urls

    def expand_href(self, segments: Segments) -> typing.Interable[str | Markup]:
        for segment in segments:
            if isinstance(segment, Markup):
                yield segment
                continue
            assert isinstance(segment, str)
            yield from self.expand_href_line(line=segment)

    def expand_href_line(self, line: str) -> Segments:
        """
        html.escape may only be called ones!
        We have to find the links one by one in sequence!
        Option:
        Use a list of elements:
          str: Still not escaped

        """
        line_orig = line
        for label, path_trigger in self.directories.items():
            url = self.urls.get(label, "")
            for tries in itertools.count():
                match = PathMatch.factory(line_before=line, path_trigger=path_trigger)
                if match is None:
                    break
                if tries > 4:
                    # TODO: Avoid endless loop
                    logger.error("tries>10!")
                    logger.error(f"{line}=")
                    logger.error(f"{line_orig}=")
                    break
                if url == "":
                    return match.line_without_href()
                return self.expand_href(match.line_with_href(url=url))
        return Segments(line)


def self_tests():
    replace = PathReplace(
        directories={
            "R": "/home/testresults",
            "T": "/home/worktree/micropython",
        },
        git_ref={},
        urls={
            "R": "https://r/",
            "T": "http://t/",
        },
    )

    def test_pos(path: str, pos_expected: int) -> None:
        pos = PathMatch.pos_end_of_path(path=path)
        assert pos == pos_expected, (pos, pos_expected)

    test_pos("a ", 1)
    test_pos("a", 1)
    test_pos("a\nx", 1)
    test_pos("a\\nx", 1)
    test_pos("a')", 1)
    test_pos("a'x", 1)
    test_pos('a"x', 1)
    test_pos("ax ", 2)

    def test_expand(line: str, line_expected: str) -> None:
        segments = replace.expand_href(segments=Segments([line]))
        line_result = Segments(segments).as_string()
        if line_result != line_expected:
            print("line:    " + line)
            print("result:  " + line_result)
            print("expected:" + line_expected)
            raise ValueError("Test failed")

    test_expand(
        "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt B",
        'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a> B',
    )
    test_expand(
        "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt",
        'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>',
    )
    test_expand(
        "x=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt')",
        'x=<a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>&#x27;)',
    )
    test_expand(
        "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt B /home/worktree/micropython/.gitignore c",
        'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a> B <a href="http:/t/.gitignore">.gitignore</a> c',
    )
    test_expand(
        "/home/worktree/micropython/.gitignore /home/worktree/micropython/.gitignore",
        '<a href="http:/t/.gitignore">.gitignore</a> <a href="http:/t/.gitignore">.gitignore</a>',
    )
    test_expand(
        "x",
        "x",
    )
    test_expand(
        "",
        "",
    )
    test_expand(
        "/home/worktree/micropython/.gitignore'",
        '<a href="http:/t/.gitignore">.gitignore</a>&#x27;',
    )
    test_expand(
        "A/home/worktree/micropython/.gitignore\nB/home/worktree/micropython/.gitignore\n",
        'A<a href="http:/t/.gitignore">.gitignore</a>\nB<a href="http:/t/.gitignore">.gitignore</a>\n',
    )
    test_expand(
        "--result-dir=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt')",
        '--result-dir=<a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>&#x27;)',
    )
    # test(
    #     # "RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W: Terminating test due to: SubprocessExitCodeException(&#x27;EXEC failed with returncode=1: /home/githubrunner/testbed_micropython/.venv/bin/python3 run-tests.py --test-dirs=extmod_hardware -t=port:/dev/ttyACM13 --jobs=1 --result-dir=/home/githubrunner/actions-runner/_work/testbed_micropython_runner/testbed_micropython_runner/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W\\nlogfile=/home/githubrunner/actions-runner/_work/testbed_micropython_runner/testbed_micropython_runner/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt&#x27;)",
    #     "RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W: Terminating test due to: SubprocessExitCodeException(&#x27;EXEC failed with returncode=1: /home/githubrunner/testbed_micropython/.venv/bin/python3 run-tests.py --test-dirs=extmod_hardware -t=port:/dev/ttyACM13 --jobs=1 --result-dir=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W\\nlogfile=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt&#x27;)",
    #     "x",
    # )


self_tests()
