import os
import logging
import tarfile

from .util_context import DIRECTORY_NAME_TESTRESULTS
from .render_directory import render_directory_or_file
from .render_log import SEVERITY_DEFAULT

from fastapi import UploadFile, File, FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse

from .constants import DIRECTORY_REPORTS

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

    curl -X POST -F "label=ch_hans_1-2025-04-22_12-33-22" -F "file=@/home/maerki/work_octoprobe_testbed_micropython/results_yoga_2025-04-21b.tgz" -k http://localhost:8000/upload

    curl -X POST -F "label=ch_hans_1-2025-04-22_12-33-22" -F "file=@/home/maerki/work_octoprobe_testbed_micropython/results_yoga_2025-04-21b.tgz" -k https://reports.octoprobe.org/upload

    -k: Skips SSL verification
    """
    MAX_FILE_SIZE_BYTES = 10_1024_1024  # 10 MB in bytes

    unpack_dir = DIRECTORY_REPORTS / label  # Unpack into a folder named after the label
    unpack_dir.mkdir(parents=True, exist_ok=True)
    filename = unpack_dir / f"{label}.tgz"
    try:
        # Download and save file
        with filename.open("wb") as f:
            f.write(await file.read())

        # Check file size
        file_size_bytes = filename.stat().st_size
        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            filename.unlink()  # Delete the file if it exceeds the size limit
            raise HTTPException(
                status_code=413,  # Payload Too Large
                detail=f"File size {file_size_bytes / (1024 * 1024):0.1f} MB exceeds the {MAX_FILE_SIZE_BYTES / (1024 * 1024):0.1f} MB limit!",
            )

        # Untar
        with tarfile.open(filename, "r:gz") as tar:
            tar.extractall(path=unpack_dir)

        # Make sure the subdirectory is called 'testresults'
        directories = [
            directory for directory in unpack_dir.iterdir() if directory.is_dir()
        ]
        if len(directories) == 1:
            directory_report = directories[0]
            directory_report.rename(
                directory_report.with_name(DIRECTORY_NAME_TESTRESULTS)
            )
        else:
            logger.warning(
                f"Expected one directory but got: {[str(d) for d in directories]}!"
            )

        return JSONResponse(
            content={"message": f"File '{filename}' uploaded successfully."},
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


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
