import logging
import pathlib
import re

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from starlette.datastructures import URL

from app.render_directory_style import STYLESHEET, get_listing_style

from .constants import DIRECTORY_REPORTS
from .render_ansii_color import render_ansi_color
from .render_log import DEFAULT_LOGFILE, is_logfile, render_log
from .render_markdown import render_markdown

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

    def f(match: re.Match) -> str:
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
            # ".spec": "text/plain",
            ".json": "text/json",
        }.get(directory.suffix, None)
        if media_type is None:
            content_bytes = directory.read_bytes()
            try:
                # Try if it is an ascii file
                content_bytes.decode("ascii")
                media_type = "text/plain"
            except UnicodeDecodeError:
                # No ascii: It is a binary file to be downloaded
                return HTMLResponse(
                    content=content_bytes,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename={directory.name}"
                    },
                )
        content_text = directory.read_text()
        return HTMLResponse(content=content_text, media_type=media_type)

    # List files and directories
    files = sorted(directory.glob("*"), key=key_number_sort, reverse=True)
    # prune_logfiles(files=files)
    html_files: list[str] = []

    def add_html_file(filename: pathlib.Path, name_override: str | None = None) -> None:
        try:
            path_ = str(filename.relative_to(DIRECTORY_REPORTS))
        except ValueError:
            assert name_override == ".."
            return
        name = filename.name
        if name_override is not None:
            name = name_override
        is_dir = filename.is_dir()
        styles = " ".join(
            [
                get_listing_style(path=path_).css_style,
                "directory" if is_dir else "file",
            ]
        )
        image = "bootstrap_folder.svg" if is_dir else "bootstrap_file-text.svg"
        html_files.append(
            f"""<li>
<a class="{styles}" href="/{path_}">
<img class="{styles}" src="/static/{image}" alt="{styles}"/>
{name}
</a>
</li>"""
        )

    # Add the top directory
    add_html_file(filename=directory.parent, name_override="..")

    for filename in files:
        add_html_file(filename=filename)

    # Generate HTML response
    html_content = f"""
    <html>
        <head>
        <title>Directory Browser</title>
        <style>
        {STYLESHEET}
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
