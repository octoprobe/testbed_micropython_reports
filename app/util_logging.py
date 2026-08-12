import json
import logging
import logging.config
import pathlib

from app.constants import DIRECTORY_REPORTS_WEBHOOK

THIS_FILE = pathlib.Path(__file__)
FILENAME_LOGGING_JSON = THIS_FILE.with_suffix(".json")
assert FILENAME_LOGGING_JSON.is_file()


def init_logging(level: int | None = None) -> None:
    DIRECTORY_REPORTS_WEBHOOK.mkdir(parents=True, exist_ok=True)
    config = json.loads(FILENAME_LOGGING_JSON.read_text())
    config["handlers"]["file_info"]["filename"] = str(
        DIRECTORY_REPORTS_WEBHOOK / "logger_info.txt"
    )
    config["handlers"]["file_debug"]["filename"] = str(
        DIRECTORY_REPORTS_WEBHOOK / "logger_debug.txt"
    )
    config["handlers"]["file_uvicorn"]["filename"] = str(
        DIRECTORY_REPORTS_WEBHOOK / "logger_uvicorn_access.txt"
    )
    logging.config.dictConfig(config)
    if level is not None:
        logging.getLogger().setLevel(level=level)
