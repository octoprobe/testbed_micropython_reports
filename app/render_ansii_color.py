"""

https://github.com/pycontribs/ansi2html/blob/main/src/ansi2html/converter.py#L329-L333
https://github.com/pycontribs/ansi2html/blob/main/src/ansi2html/converter.py#L342

    def do_linkify(self, line: str) -> str:
        if not isinstance(line, str):
            return line  # If line is an object, e.g. OSC_Link, it
            # will be expanded to a string later
        if self.latex:
            return self.url_matcher.sub(r"\\url{\1}", line)
        return self.url_matcher.sub(r'<a href="\1">\1</a>', line)
"""

import pathlib
import re

from ansi2html import Ansi2HTMLConverter
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from starlette.datastructures import URL

from .constants import DIRECTORY_REPORTS

RE_LINKS = re.compile(r"\/(?:[^\/\s]+\/)*[^\/\s]+")
r"""
\/ matches the starting /

(?:[^\/\s]+\/)* matches any number of folders

[^\/\s]+ matches the final file or folder name

Avoids whitespace so you don't catch incomplete or invalid paths
"""


def replace_links(text: str, url: URL) -> str:
    def f(match: re.Match):
        link = match.group(0)
        link = link.replace("/home/octoprobe/testbed_micropython/results", "")
        return f"{url.scheme}://{link}"

    return RE_LINKS.sub(f, text)


def do_linkify(text: str, url: URL) -> str:
    def f(match: re.Match):
        link = match.group(0)
        link_small = link.replace("/home/octoprobe/testbed_micropython/results/", "")
        return f'<a href="{url.scheme}://{link}">{link_small}</a>'

    return RE_LINKS.sub(f, text)


def render_ansi_color(color_file: pathlib.Path, url: URL) -> HTMLResponse:
    """
    Convert a .color file (ASCII colors) into colorized HTML using ansi2html.
    """
    try:
        # Read the .color file
        color_content = color_file.read_text(encoding="utf-8")

        linkify = False

        if linkify:
            color_content = replace_links(color_content, url=url)

        # Convert ANSI color codes to HTML
        title = str(color_file.relative_to(DIRECTORY_REPORTS))
        # scheme = "ansi2html"
        scheme = "xterm"
        # scheme = "osx"
        # scheme = "osx-basic"
        # scheme = "osx-solid-colors"
        # scheme = "solarized"
        # scheme = "mint-terminal"
        # scheme = "dracula"
        conv = Ansi2HTMLConverter(
            title=title,
            dark_bg=False,
            linkify=linkify,
            scheme=scheme,
            markup_lines=True,
            font_size="120%",
        )
        full = False
        html_content = conv.convert(color_content, full=False)
        if not linkify:
            html_content = do_linkify(html_content, url=url)

        html_pre = ""
        if not full:
            html_pre = (
                """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>"""
                + title
                + """</title>
<style type="text/css">
.ansi2html-content { display: inline; white-space: pre-wrap; word-wrap: break-word; }
.body_foreground { color: #000000; }
.body_background { background-color: #DDDDDD; }
.inv_foreground { color: #AAAAAA; }
.inv_background { background-color: #000000; }
.ansi32 { color: #00cd00; }
.ansi34 { color: #0000ee; }
.ansi38-214 { color: #ffaf00; }
</style>
</head>
<body class="body_foreground body_background" style="font-size: 120%;" >
<pre class="ansi2html-content">
"""
            )
        html_post = """</pre>
</body>
</html>
"""
        html_content = html_pre + html_content + html_post

        # Wrap the content in a preformatted block for proper display
        # html_content = f"<pre>{html_content}</pre>"

        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to render .color file: {str(e)}"
        ) from e
