from __future__ import annotations

import re
import pathlib
from markupsafe import Markup
from .util_html import Segments

from starlette.datastructures import URL
from fastapi.responses import HTMLResponse
from . import util_context


CSS = pathlib.Path(__file__).with_suffix(".css").read_text()
"""
Cash the stylesheet
"""
RE_SEVERITY_TEXT = re.compile(
    r"^(?P<severity>DEBUG|INFO|WARNING|ERROR) +- (\[(?P<color_schema>COLOR_[A-Z]+)\])?(?P<payload>.*)$"
)
"""
Example: 'DEBUG    - not matched'
Example: 'INFO     - [COLOR_INFO]ESP8266_GENERIC: Firmware build start.'
"""


DICT_SEVERITY_TEXT = {
    "DEBUG": 1,
    "INFO": 2,
    "WARNING": 3,
    "ERROR": 4,
}
DICT_SEVERITY = {s: s_text for s_text, s in DICT_SEVERITY_TEXT.items()}
SEVERITY_MIN = min(DICT_SEVERITY_TEXT.values())
SEVERITY_MAX = max(DICT_SEVERITY_TEXT.values())
SEVERITY_DEFAULT = "INFO"

DEFAULT_LOGFILE = "logger_10_debug.log"
TASK_REPORT_FILES_TO_PRUNE = {"task_report.md", "task_report.txt"}

LOGFILE_TRIGGER = "logger_"
LOGFILE_DEFAULT = "logger_10_debug.log"


def is_logfile(filename: pathlib.Path) -> bool:
    return filename.name.startswith(LOGFILE_TRIGGER)


def prune_logfiles(files: list[pathlib.Path]):
    files_to_prune: list[pathlib.Path] = []
    found = False
    for filename in files:
        if not is_logfile(filename=filename):
            if filename.name not in TASK_REPORT_FILES_TO_PRUNE:
                continue
        if filename.name == DEFAULT_LOGFILE:
            found = True
        else:
            files_to_prune.append(filename)
    if not found:
        return
    for filename in files_to_prune:
        files.remove(filename)


def get_severity_text(severity: int) -> str:
    return DICT_SEVERITY.get(severity, "ERROR")


HTML_BEGIN = f"""<html>
<head>
    <style>
{CSS}
    </style>
</head>
<body>
"""

HTML_END = """</body>
</html>
"""

LINE_STYLES_NORMAL = """
<style>
span.text.DEBUG {
    color: gray;
    font-size: smaller;
}

span.text.INFO {
    color: black;
}

span.text.WARNING {
    color: orange;
    font-size: "bigger";
}

span.text.ERROR {
    color: red;
    font-size: "bigger";
}
</style>
"""

LINE_STYLES_COLOR_SCHEMA = """
<style>

span.text.DEBUG {
    font-weight: lighter;
        font-size: smaller;
}

span.text.INFO {
}

span.text.WARNING {
    font-weight: bold;
    font-size: bigger;
}

span.text.ERROR {
    font-weight: bold;
    font-size: bigger;
}

span.text.COLOR_INFO {
    color: blue;
}

span.text.COLOR_FAILED {
    color: orange;
    font-size: bigger;
}

span.text.COLOR_SUCCESS {
    color: green;
}

span.text.COLOR_ERROR {
    color: red;
    font-size: bigger;
}

</style>
"""


def severity_link(line_number: int, severity: int, label: str) -> str:
    if SEVERITY_MIN <= severity <= SEVERITY_MAX - 1:
        sev_text = DICT_SEVERITY[severity]
        return f'<a class="severity" title="{sev_text}" href="?severity={sev_text}#line{line_number}">{label}</a>'
    return ""


def severity_links(severity: int, line_number: int) -> str:
    return severity_link(
        line_number=line_number, severity=severity + 1, label="-"
    ) + severity_link(line_number, severity - 1, "+")


class Render:
    def __init__(self, logfile: pathlib.Path, url: URL, severity_text: str) -> None:
        assert isinstance(logfile, pathlib.Path)
        assert logfile.is_file()
        assert isinstance(url, URL)
        assert isinstance(severity_text, str)

        self.severity_text = severity_text
        self.last_severity = ""
        self.severity = DICT_SEVERITY_TEXT[severity_text]
        self.line_severity_text = SEVERITY_DEFAULT
        self.color_schema = "COLOR_INFO"
        self.logfile = logfile
        self.url = url

        directory_testresults = util_context.get_directory_testresults(logfile=logfile)
        self.replace = util_context.get_path_replace(
            directory_testresults=directory_testresults
        )

    def _render_line(self, line_payload: str, line_number: int) -> Segments:
        segments = Segments()

        with segments.tag("div", params='class="line"'):
            match_severity_text = RE_SEVERITY_TEXT.match(line_payload)
            if match_severity_text:
                self.line_severity_text = match_severity_text.group("severity")
                self.color_schema = match_severity_text.group("color_schema")
                line_payload = match_severity_text.group("payload")
                if self.line_severity_text != self.last_severity:
                    self.last_severity = self.line_severity_text
                    with segments.tag(
                        "a",
                        params=f'id="line{line_number}" name="line{line_number}"',
                    ):
                        html_number = severity_links(
                            line_number=line_number,
                            severity=self.severity,
                        )
                        segments.append(Markup(html_number))
            with segments.tag(
                "span", params=f'class="text {self.last_severity} {self.color_schema}"'
            ):
                segments.extend(self.replace.expand_href_line(line=line_payload))

        if DICT_SEVERITY_TEXT[self.line_severity_text] >= self.severity:
            return segments
        return Segments()

    def render(self) -> str:
        """
        severity:
          text: DEBUG, INFO
          int: 1, 2, 3
        severity: The requested severity

        """
        logfile_text = self.logfile.read_text()

        schema_color_active = logfile_text.find("[COLOR_INFO]") >= 0
        path_directory, _, path_filename = self.url.path.rpartition("/")

        segments = Segments()

        segments.append(Markup(HTML_BEGIN))
        if schema_color_active:
            segments.append(Markup(LINE_STYLES_COLOR_SCHEMA))
        else:
            segments.append(Markup(LINE_STYLES_NORMAL))
        segments.append(
            Markup(f"""
<p class="filename">
    <a id="line{0}" name="line{0}"/>
    <a href="{path_directory}">back to directory</a><br/>
    path: {self.url.path}</br>
    severity: {severity_links(self.severity, line_number=0)} {self.severity_text}<br>
    schema_color_active: {schema_color_active}
</p>
""")
        )

        for line_number0, line in enumerate(logfile_text.splitlines()):
            line_payload = line.rstrip()
            segments.extend(
                self._render_line(
                    line_payload=line_payload,
                    line_number=line_number0 + 1,
                )
            )
        return segments.as_string()


def render_log(
    logfile: pathlib.Path,
    url: URL,
    severity: str,
) -> HTMLResponse:
    r = Render(logfile=logfile, url=url, severity_text=severity)
    html_content = r.render()
    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
