import enum
import pathlib
import re

STYLESHEET = pathlib.Path(__file__).with_suffix(".css").read_text()


class ListingStyle(enum.StrEnum):
    GRAY = "gray"
    BLACK = "black"
    GREEN = "green"
    FIRMWARE = "firmware"

    @property
    def css_style(self) -> str:
        return f"listing_{self}"


LIST_RE_2_STYLE = [
    # Firmware
    (re.compile(r"/mpbuild$"), ListingStyle.FIRMWARE),
    (re.compile(r"/mpbuild/[^/]+$"), ListingStyle.FIRMWARE),
    (re.compile(r"/firmware.uf2$"), ListingStyle.FIRMWARE),
    (re.compile(r"/firmware.spec$"), ListingStyle.FIRMWARE),
    (re.compile(r"/docker_stdout.txt$"), ListingStyle.FIRMWARE),
    # Directories
    (re.compile(r"/RUN-[^/]+$"), ListingStyle.GREEN),
    (re.compile(r"/testresults$"), ListingStyle.GREEN),
    (re.compile(r"^github_testbed_micropython_\d+$"), ListingStyle.GREEN),
    # Logfiles
    (re.compile(r"/journalctl.txt$"), ListingStyle.BLACK),
    (re.compile(r"/logger_20_info.log$"), ListingStyle.GREEN),
    (re.compile(r"/octoprobe_summary_report.md$"), ListingStyle.BLACK),
    (re.compile(r"/task_report.md$"), ListingStyle.BLACK),
    (re.compile(r"/testresults.txt$"), ListingStyle.BLACK),
    (re.compile(r"/flashing_stdout.txt$"), ListingStyle.BLACK),
]
"""
Map a regular expression on a filename to a css style to be applied to this file/directory.
"""


def get_listing_style(path: str) -> ListingStyle:
    """
    The first matching style will be returned.
    """
    assert isinstance(path, str)

    for re_search, style in LIST_RE_2_STYLE:
        match = re_search.search(path)
        if match is not None:
            return style
    return ListingStyle.GRAY
