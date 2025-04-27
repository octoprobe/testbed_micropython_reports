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
