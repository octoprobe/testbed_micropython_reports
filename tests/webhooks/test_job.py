import dataclasses
import pathlib

import pytest
from app import util_webhooks

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_SAMPLE_DATA = DIRECTORY_OF_THIS_FILE / "sample_data"


@dataclasses.dataclass(frozen=True)
class Ttestparam:
    directory: str
    expected_webhook_filename: str | None

    @property
    def pytest_id(self) -> str:
        return self.directory


_TESTPARAMS = (
    Ttestparam(
        directory="sample_data",
        expected_webhook_filename="2026-07-07_08-16-00+0000-pull_request-synchronize-016798.json",
    ),
    Ttestparam(
        directory="files_pr19349",
        expected_webhook_filename="2026-07-06_19-25-58+0000-pull_request-synchronize-019349.json",
    ),
    Ttestparam(
        directory="files_pr19290",
        expected_webhook_filename="2026-06-12_06-58-11+0000-pull_request-synchronize-019290.json",
    ),
    Ttestparam(
        directory="files_pr19589",
        expected_webhook_filename="2026-08-12_13-25-04+0000-pull_request-synchronize-019589.json",
    ),
)


@pytest.mark.parametrize(
    "testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id
)
def test_next_job(testparam: Ttestparam) -> None:
    hooks = util_webhooks.Webhooks.from_directory(
        DIRECTORY_OF_THIS_FILE / testparam.directory
    )
    webhook_job = hooks.next_job
    if testparam.expected_webhook_filename is None:
        assert webhook_job is None
        return

    assert webhook_job is not None
    assert webhook_job.filename == testparam.expected_webhook_filename
