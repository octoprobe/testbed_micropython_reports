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

from app import util_logging, util_validate
from app.util_github import (
    FormStartJob,
    ReturncodeStartJob,
    gh_start_job,
)
from app.util_github2 import (
    WorkflowExpiry,
    gh_list,
    list_reports,
    save_as_workflow_input,
)

from .constants import DIRECTORY_REPORTS
from .render_directory import render_directory_or_file
from .render_log import SEVERITY_DEFAULT

logger = logging.getLogger(__file__)

util_logging.init_logging(level=logging.INFO)

app = FastAPI()

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TEMPLATES = DIRECTORY_OF_THIS_FILE / "templates"
assert DIRECTORY_TEMPLATES.is_dir()
JINJA2_TEMPLATES = Jinja2Templates(directory=DIRECTORY_TEMPLATES)


@app.get("/index")
def read_root(request: Request):
    return JINJA2_TEMPLATES.TemplateResponse("index.html", {"request": request})


def _index_start(
    request: Request,
    form_startjob: FormStartJob,
    form_rc: ReturncodeStartJob,
    file_html: str,
) -> HTMLResponse:
    return JINJA2_TEMPLATES.TemplateResponse(
        file_html,
        {
            "request": request,
            "form_startjob": form_startjob,
            "form_rc": form_rc,
        },
    )


@app.post("/jobs/start_pr")
def jobs_start_pr_POST(
    request: Request, form_startjob: typing.Annotated[FormStartJob, Form()]
):
    # form_data = await request.form()
    # action = form_data.get("action", "start")
    # Need to examine which will be the next job number
    assert isinstance(form_startjob, FormStartJob)

    form_rc_pr = util_validate.validate_pr(form_startjob=form_startjob)

    if form_startjob.action == "validate":
        return _index_start(
            request=request,
            form_startjob=form_startjob,
            form_rc=form_rc_pr,
            file_html="jobs_pr.html",
        )

    if form_rc_pr.msg_error:
        return _index_start(
            request=request,
            form_startjob=form_startjob,
            form_rc=form_rc_pr,
            file_html="jobs_pr.html",
        )

    next_directory_metadata = gh_list()
    if next_directory_metadata is not None:
        save_as_workflow_input(
            form_startjob=form_startjob,
            directory_metadata=next_directory_metadata,
        )
    form_rc = gh_start_job(form_startjob=form_startjob)
    return _index_start(
        request=request,
        form_startjob=form_startjob,
        form_rc=form_rc,
        file_html="jobs_pr.html",
    )


@app.get("/jobs/start_pr")
def jobs_start_pr_GET(request: Request):
    form_startjob = FormStartJob()
    form_startjob.pr_number = "17782"
    return _index_start(
        request=request,
        form_startjob=form_startjob,
        form_rc=ReturncodeStartJob(),
        file_html="jobs_pr.html",
    )


@app.get("/jobs/start")
def jobs_start_GET(request: Request):
    return _index_start(
        request=request,
        form_startjob=FormStartJob(),
        form_rc=ReturncodeStartJob(),
        file_html="jobs.html",
    )


@app.post("/jobs/start")
def jobs_start_POST(
    request: Request, form_startjob: typing.Annotated[FormStartJob, Form()]
):
    # form_data = await request.form()
    # action = form_data.get("action", "start")
    # Need to examine which will be the next job number
    assert isinstance(form_startjob, FormStartJob)
    if form_startjob.action == "validate":
        form_rc = util_validate.validate_repos(form_startjob=form_startjob)
        return _index_start(
            request=request,
            form_startjob=form_startjob,
            form_rc=form_rc,
            file_html="jobs.html",
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
    return _index_start(
        request=request,
        form_startjob=form_startjob,
        form_rc=form_rc,
        file_html="jobs.html",
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


@app.get("/purge")
def purge_expired_reports(request: Request):
    return JINJA2_TEMPLATES.TemplateResponse(
        "purge_expired_reports.html",
        {
            "request": request,
            "list_reports": list_reports,
        },
    )


# Mount the 'uploads' directory for browsing
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def reports(request: Request, read_github: bool = False):
    """
    This top route '/' overrides the following '/{path:path}'!
    """
    workflow_unique_id = request.query_params.get("workflow_unique_id", None)
    if workflow_unique_id is not None:
        # Expiry dialog. Write back values
        tag = request.query_params["tag"]
        expiry = request.query_params["expiry"]
        workflow_expiry = WorkflowExpiry(tag=tag, expiry=expiry)
        workflow_expiry.write(workflow_unique_id=workflow_unique_id)

    # if read_github:
    try:
        gh_list()
    except Exception as e:
        print(f"ERROR: {e}")

    return JINJA2_TEMPLATES.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "list_reports": list_reports,
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
