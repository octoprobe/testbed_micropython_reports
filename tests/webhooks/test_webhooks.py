import dataclasses
import pathlib

import pytest
from app import util_webhooks

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SAMPLE_DATA = DIRECTORY_OF_THIS_FILE / "sample_data"


@dataclasses.dataclass(frozen=True)
class Ttestparam:
    directory: str
    expected_filenames_to_purge: list[str]

    @property
    def pytest_id(self) -> str:
        return self.directory


_TESTPARAMS = (
    Ttestparam(
        directory="files_pr19349",
        expected_filenames_to_purge=[
            "2026-07-05_12-53-28+0000-pull_request-synchronize-019349.json",
            "2026-07-05_12-43-34+0000-pull_request-synchronize-019349.json",
            "2026-07-02_06-58-08+0000-pull_request-synchronize-019349.json",
            "2026-07-01_07-12-26+0000-pull_request-synchronize-019349.json",
            "2026-06-30_08-36-51+0000-pull_request-synchronize-019349.json",
            "2026-06-25_08-31-30+0000-pull_request-synchronize-019349.json",
            "2026-06-23_15-04-33+0000-pull_request-synchronize-019349.json",
            "2026-06-21_10-09-48+0000-pull_request-reopened-019349.json",
            "2026-06-21_10-09-45+0000-pull_request-closed-019349.json",
            "2026-06-21_09-54-23+0000-pull_request-synchronize-019349.json",
            "2026-06-18_14-26-18+0000-pull_request-synchronize-019349.json",
            "2026-06-17_06-38-14+0000-pull_request-synchronize-019349.json",
            "2026-06-17_01-07-54+0000-pull_request-labeled-019349.json",
            "2026-06-16_19-00-49+0000-pull_request-synchronize-019349.json",
            "2026-06-16_16-38-07+0000-pull_request-review_requested-019349.json",
            "2026-06-16_12-59-29+0000-pull_request-opened-019349.json",
        ],
    ),
    Ttestparam(
        directory="files_pr19290",
        expected_filenames_to_purge=[
            "2026-06-09_10-07-50+0000-pull_request-review_requested-019290.json",
            "2026-06-09_09-51-08+0000-pull_request-synchronize-019290.json",
            "2026-06-09_09-44-30+0000-pull_request-synchronize-019290.json",
            "2026-06-09_09-38-22+0000-pull_request-synchronize-019290.json",
            "2026-06-09_09-32-49+0000-pull_request-synchronize-019290.json",
            "2026-06-09_09-22-35+0000-pull_request-synchronize-019290.json",
            "2026-06-09_04-26-12+0000-pull_request-labeled-019290.json",
        ],
    ),
)


@pytest.mark.parametrize(
    "testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id
)
def test_purge_pr(testparam: Ttestparam) -> None:
    hooks = util_webhooks.Webhooks.from_directory(
        DIRECTORY_OF_THIS_FILE / testparam.directory
    )
    hooks_to_purge = hooks.purge()
    filenames_to_purge = [f.filename for f in hooks_to_purge]
    assert testparam.expected_filenames_to_purge == filenames_to_purge
