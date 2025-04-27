import pathlib

import markdown2
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

# See: https://github.com/trentm/python-markdown2/wiki/Extras
_MARKDOWN = markdown2.Markdown(
    extras=[
        "tables",  # Tables using the same format as GFM and PHP-Markdown Extra.
        "footnotes",  # support footnotes as in use on daringfireball.net and implemented in other Markdown processors (tho not in Markdown.pl v1.0.1).
        "target-blank-links",  # Add target="_blank" to all <a> tags with an href. This causes the link to be opened in a new tab upon a click.
        # "html-classes",  # Takes a dict mapping html tag names (lowercase) to a string to use for a "class" tag attribute. Currently only supports "pre", "code", "table" and "img" tags. Add an issue if you require this for other tags.
    ]
)

_HTML_HEADER = """
<html>
<head>
<style>
body {
    font-family: 'Arial', Verdana, sans-serif;
    font-size: 14px;
    # white-space: nowrap;
}
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
  padding: 4px;
}
</style>
</head>
<body>
"""
_HTML_FOOTER = """
</body>
</html>
"""


def render_markdown(markdown_file: pathlib.Path) -> HTMLResponse:
    try:
        # Read the Markdown file
        markdown_content = markdown_file.read_text(encoding="utf-8")

        # Convert Markdown to HTML
        html_content = _MARKDOWN.convert(markdown_content)

        # Return the HTML content
        html_content = _HTML_HEADER + html_content + _HTML_FOOTER
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to convert Markdown: {str(e)}"
        ) from e
