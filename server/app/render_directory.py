import logging
import pathlib
import re

from .render_markdown import render_markdown

from .render_log import DEFAULT_LOGFILE, is_logfile, prune_logfiles, render_log
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

from .constants import DIRECTORY_REPORTS
from .render_ansii_color import render_ansi_color
from starlette.datastructures import URL

logger = logging.Logger(__file__)

RE_NUMBER = re.compile(r"((?P<number>\d+)|(?P<text>^\d+))")
"""
"testresults_100" -> "testresults_", "100"
"""


def key_number_sort(filename: pathlib.Path | str) -> str:
    """
    Example:
        testresults_100
        testresults_92
        testresults_97
    Returns:
        testresults_00100
        testresults_00092
        testresults_00097

    This then will allow sorting by numbers.
    """
    if isinstance(filename, pathlib.Path):
        filename = str(filename)
    assert isinstance(filename, str)

    def f(match: re.Match) -> str | int:
        number = match.group("number")
        if number is not None:
            return format(int(number), "010d")
        text = match.group("text")
        assert text is not None
        return text

    return RE_NUMBER.sub(f, filename)


def render_directory_or_file(path: str, url: URL, severity: str) -> HTMLResponse:
    directory = DIRECTORY_REPORTS / path

    # Ensure the directory exists
    if not directory.exists():
        raise HTTPException(status_code=404, detail="Uploads directory not found.")

    if directory.is_file():
        filename = directory
        if filename.suffix == ".md":
            return render_markdown(markdown_file=filename)
        if filename.suffix == ".color":
            return render_ansi_color(color_file=filename, url=url)
        if filename.suffix == ".log":
            if is_logfile(filename):
                # Whenever we select logger_20_info.log, we fall back to logger_10_debug.log!
                return render_log(
                    logfile=filename.with_name(DEFAULT_LOGFILE),
                    url=url,
                    severity=severity,
                )

        media_type = {
            ".html": "text/html",
            ".txt": "text/plain",
            ".json": "text/json",
        }.get(directory.suffix, None)
        if media_type is None:
            return HTMLResponse(
                content=directory.read_bytes(),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={directory.name}"
                },
            )
        content = directory.read_text()
        return HTMLResponse(content=content, media_type=media_type)

    # List files and directories
    files = sorted(directory.glob("*"), key=key_number_sort, reverse=True)
    prune_logfiles(files=files)
    html_files: list[str] = []

    def add_html_file(is_dir: bool, path_: str, name: str) -> None:
        class_name = "directory" if is_dir else "file"
        image = "bootstrap_folder.svg" if is_dir else "bootstrap_file-text.svg"
        html_files.append(
            f"""<li>
<a class="{class_name}" href="/{path_}">
<img class="{class_name}" src="/static/{image}" alt="{class_name}"/>
{name}
</a>
</li>"""
        )

    if path != "":
        path_ = str(directory.parent.relative_to(DIRECTORY_REPORTS))
        add_html_file(is_dir=True, path_=path_, name="..")

    for item in files:
        path_ = str(item.relative_to(DIRECTORY_REPORTS))
        is_dir = item.is_dir()
        add_html_file(is_dir=is_dir, path_=path_, name=item.name)

    # Generate HTML response
    stylesheet = """
ul {
    list-style-type: none;
}

a.file {
    color: black;
}

a.directory {
    color: blue;
}

a > img {
    width: 16px;
    height: 16px;
    margin-top: 6px;
    margin-right: 12px;
    margin-bottom: 0px;
}

a > img.file {
    color: black;
}

a > img.directory {
    color: blue;
}

# image {
# width:16px;
# height:16px;
# margin-right:5px;
# }
"""

    html_content = f"""
    <html>
        <head>
        <title>Directory Browser</title>
        <style>
        {stylesheet}
        </style>
        </head>
        <body>
            <h1>Browsing: {str(directory.relative_to(DIRECTORY_REPORTS))}</h1>
            <ul>
                {"".join(html_files)}
            </ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
