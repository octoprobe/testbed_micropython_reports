import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_REPORTS = DIRECTORY_OF_THIS_FILE.parent / "reports"
DIRECTORY_REPORTS.mkdir(parents=True, exist_ok=True)
