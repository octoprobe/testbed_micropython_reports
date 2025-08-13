import os
import pathlib

ENV_DIRECTORY_REPORTS = "DIRECTORY_REPORTS"


DIRECTORY_REPORTS_FALLBACK = "/server/reports"
DIRECTORY_REPORTS = pathlib.Path(
    os.getenv(ENV_DIRECTORY_REPORTS, DIRECTORY_REPORTS_FALLBACK)
)
if not DIRECTORY_REPORTS.is_dir():
    raise ValueError(
        f"Enivornment variable '{ENV_DIRECTORY_REPORTS}' points to '{DIRECTORY_REPORTS}' which is NOT a directory! Fallback is '{DIRECTORY_REPORTS_FALLBACK}'."
    )

DIRECTORY_REPORTS_METADATA = DIRECTORY_REPORTS.with_name("reports_metadata")
DIRECTORY_REPORTS_METADATA.mkdir(parents=False, exist_ok=True)

GITHUB_EVENT = "workflow_dispatch"
GITHUB_PREFIX = "github_"
"""
This corresponds to
  .github/workflows/selfhosted_testrun.yml
    --label='github_${{ github.workflow }}_${{ github.run_number }}'
"""

if True:
    GITHUB_WORKFLOW = "selfhosted_testrun"  # .yaml may be omitted
    GITHUB_REPO = "octoprobe/testbed_micropython"
else:
    GITHUB_WORKFLOW = "testbed_micropython"  # .yaml may be omitted
    GITHUB_REPO = "octoprobe/testbed_micropython_runner_obsolete"

FILENAME_GH_LIST_JSON = "gh_list.json"
FILENAME_EXPIRY = "expiry.json"
FILENAME_INPUTS_JSON = "github_debug/inputs.json"
