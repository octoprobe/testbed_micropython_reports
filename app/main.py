import io
import logging
import pathlib
import shutil
import tarfile
import typing

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.util_github import (
    FormStartJob,
    ReturncodeStartJob,
    gh_start_job,
)
from app.util_github2 import gh_list, render_reports, save_as_workflow_input
from app.util_logging import init_logging
from app.util_validate import validate_repos

from .constants import DIRECTORY_REPORTS
from .render_directory import render_directory_or_file
from .render_log import SEVERITY_DEFAULT

logger = logging.getLogger(__file__)

init_logging(level=logging.INFO)

app = FastAPI()

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TEMPLATES = DIRECTORY_OF_THIS_FILE / "templates"
assert DIRECTORY_TEMPLATES.is_dir()
JINJA2_TEMPLATES = Jinja2Templates(directory=DIRECTORY_TEMPLATES)


@app.get("/index")
def read_root(request: Request):
    return JINJA2_TEMPLATES.TemplateResponse("index.html", {"request": request})


def _jobs_response(
    request: Request,
    form_startjob: FormStartJob,
    form_rc: ReturncodeStartJob,
) -> HTMLResponse:
    return JINJA2_TEMPLATES.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "form_startjob": form_startjob,
            "form_rc": form_rc,
        },
    )


@app.get("/jobs/start")
def jobs_index_get(request: Request):
    return _jobs_response(
        request=request,
        form_startjob=FormStartJob(),
        form_rc=ReturncodeStartJob(),
    )


@app.post("/jobs/start")
def jobs_index_post(
    request: Request, form_startjob: typing.Annotated[FormStartJob, Form()]
):
    # form_data = await request.form()
    # action = form_data.get("action", "start")
    # Need to examine which will be the next job number
    if form_startjob.action == "validate":
        form_rc = validate_repos(form_startjob=form_startjob)
        return _jobs_response(
            request=request,
            form_startjob=form_startjob,
            form_rc=form_rc,
        )

    next_directory_metadata = gh_list()
    if next_directory_metadata is not None:
        save_as_workflow_input(
            form_startjob=form_startjob,
            directory_metadata=next_directory_metadata,
        )
    form_rc = gh_start_job(form_startjob=form_startjob)
    if form_rc.msg_error is not None:
        # It typically takes some time till the new job appears in the list
        # time.sleep(2.0)
        pass
    return _jobs_response(
        request=request,
        form_startjob=form_startjob,
        form_rc=form_rc,
    )


@app.post("/upload")
async def upload_tar_file(
    file: UploadFile = File(...),
    label: str = Form(...),
):
    """
    Endpoint to upload a tar file via HTTPS POST.

    curl -X POST -F "label=github_selfhosted_testrun_107" -F "file=@/home/maerki/Downloads/testresults/github_selfhosted_testrun_107.tgz" -k http://localhost:8000/upload

    curl -X POST -F "label=ch_hans_1-2025-04-22_12-33-22" -F "file=@/home/maerki/work_octoprobe_testbed_micropython/results_yoga_2025-04-21b.tgz" -k https://reports.octoprobe.org/upload

    -k: Skips SSL verification
    """
    max_file_size_bytes = 10_1024_1024  # 10 MB in bytes

    final_dir = DIRECTORY_REPORTS / label
    filename_tgz = final_dir / f"{label}.tgz"
    try:
        # Download tarfile and keep in memory
        tarfile_bytes = await file.read()

        # Check file size
        tarfile_size_bytes = len(tarfile_bytes)
        if tarfile_size_bytes > max_file_size_bytes:
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail=f"File size {tarfile_size_bytes / (1024 * 1024):0.1f} MB exceeds the {max_file_size_bytes / (1024 * 1024):0.1f} MB limit!",
            )

        # Prepare folder
        shutil.rmtree(final_dir, ignore_errors=True)
        final_dir.parent.mkdir(parents=True, exist_ok=True)

        # Untar into tmp_dir
        with tarfile.open(fileobj=io.BytesIO(tarfile_bytes), mode="r:gz") as tar:
            tar.extractall(path=final_dir)

        # Save tar file
        filename_tgz.write_bytes(tarfile_bytes)

        return JSONResponse(
            content={"message": f"File '{filename_tgz}' uploaded successfully."},
            status_code=200,
        )
    except Exception as e:
        logger.exception(e)
        # Clean up directory
        shutil.rmtree(final_dir, ignore_errors=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}"
        ) from e


# Mount the 'uploads' directory for browsing
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def reports(request: Request, read_github: bool = False):
    """
    This top route '/' overrides the following '/{path:path}'!
    """
    # if read_github:
    try:
        gh_list()
    except Exception as e:
        print(f"ERROR: {e}")

    workflow_reports = render_reports()
    return JINJA2_TEMPLATES.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "workflow_reports": workflow_reports,
        },
    )


@app.get("/{path:path}", response_class=HTMLResponse)
async def browse_directory(
    request: Request,
    path: str = "",
    severity: str = SEVERITY_DEFAULT,
):
    """
    Custom endpoint to browse the 'uploads' directory and list files.
    """
    url = request.url_for("browse_directory", path=path)
    return render_directory_or_file(
        request=request, path=path, url=url, severity=severity
    )
