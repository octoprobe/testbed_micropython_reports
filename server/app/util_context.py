import pathlib
from . import util_path_replace
from . import constants
import json

DIRECTORY_NAME_TESTRESULTS = "testresults"
FILENAME_CONTEXT_JSON = "context.json"


def get_directory_testresults(logfile: pathlib.Path) -> pathlib.Path:
    logfile_relative = logfile.relative_to(constants.DIRECTORY_REPORTS)
    directoryname_testresults = logfile_relative.parts[0]
    directory_testresults = constants.DIRECTORY_REPORTS / directoryname_testresults
    assert directory_testresults.is_dir(), directory_testresults
    return directory_testresults


def get_path_replace(
    directory_testresults: pathlib.Path,
) -> util_path_replace.PathReplace:
    context_filename = (
        directory_testresults / DIRECTORY_NAME_TESTRESULTS / FILENAME_CONTEXT_JSON
    )
    assert context_filename.is_file(), context_filename
    context_text = context_filename.read_text()
    context_json = json.loads(context_text)

    return util_path_replace.PathReplace(
        directories=context_json["directories"],
        git_ref=context_json["git_ref"],
        urls={
            # "R": f"https://reports.octoprobe.org/{directory_testresults.name}",
            "R": f"/{directory_testresults.name}/{DIRECTORY_NAME_TESTRESULTS}/",
            "T": "http://t/",
        },
    )
