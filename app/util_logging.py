import json
import logging
import logging.config
import pathlib

THIS_FILE = pathlib.Path(__file__)
FILENAME_LOGGING_JSON = THIS_FILE.with_suffix(".json")
assert FILENAME_LOGGING_JSON.is_file()


def init_logging(level: int | None = None) -> None:
    logging.config.dictConfig(json.loads(FILENAME_LOGGING_JSON.read_text()))
    if level is not None:
        logging.getLogger().setLevel(level=level)
