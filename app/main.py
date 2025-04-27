import io
import logging
import os
import shutil
import tarfile

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .constants import DIRECTORY_REPORTS
from .render_directory import render_directory_or_file
from .render_log import SEVERITY_DEFAULT

logger = logging.Logger(__file__)

app = FastAPI()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)


@app.get("/index")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_tar_file(
    file: UploadFile = File(...),
    label: str = Form(...),
):
    """
    Endpoint to upload a tar file via HTTPS POST.

    curl -X POST -F "label=github_testbed_micropython_107" -F "file=@/home/maerki/Downloads/testresults/github_testbed_micropython_107.tgz" -k http://localhost:8000/upload

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
    return render_directory_or_file(path=path, url=url, severity=severity)
