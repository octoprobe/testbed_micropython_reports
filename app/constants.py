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
