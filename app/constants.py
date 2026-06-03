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

FILENAME_GH_LIST_JSON = "gh_list.json"
FILENAME_EXPIRY = "expiry.json"
FILENAME_INPUTS_JSON = "github_debug/inputs.json"
