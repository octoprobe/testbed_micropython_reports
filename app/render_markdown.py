import pathlib

from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from testbed_micropython.testreport.util_markdown2 import markdown2html


def render_markdown(markdown_file: pathlib.Path) -> HTMLResponse:
    try:
        # Read the Markdown file
        markdown_content = markdown_file.read_text(encoding="utf-8")

        # Convert Markdown to HTML
        html_content = markdown2html(markdown_content)

        # Return the HTML content
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to convert Markdown: {str(e)}"
        ) from e
