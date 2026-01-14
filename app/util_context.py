import json
import pathlib

from octoprobe.util_constants import DirectoryTag
from testbed_micropython.report_test.util_constants import FILENAME_CONTEXT_JSON

from . import constants, util_path_replace


def get_directory_testresults(logfile: pathlib.Path) -> pathlib.Path:
    logfile_relative = logfile.relative_to(constants.DIRECTORY_REPORTS)
    directoryname_testresults = logfile_relative.parts[0]
    directory_testresults = constants.DIRECTORY_REPORTS / directoryname_testresults
    assert directory_testresults.is_dir(), directory_testresults
    return directory_testresults


def get_path_replace(
    directory_testresults: pathlib.Path,
) -> util_path_replace.PathReplace:
    context_filename = directory_testresults / FILENAME_CONTEXT_JSON
    assert context_filename.is_file(), context_filename
    context_text = context_filename.read_text()
    context_json = json.loads(context_text)

    return util_path_replace.PathReplace(
        directories=context_json["directories"],
        git_ref=context_json["git_ref"],
        urls={
            # DirectoryTag.R: f"https://reports.octoprobe.org/{directory_testresults.name}",
            DirectoryTag.R: f"/{directory_testresults.name}/",
            DirectoryTag.T: "http://t/",
        },
    )
