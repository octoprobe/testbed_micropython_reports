from __future__ import annotations

import pytest
from app.util_path_replace import PathMatch, PathReplace, Segments


@pytest.mark.parametrize(
    "path,pos_expected",
    (
        ("a ", 1),
        ("a", 1),
        ("a\nx", 1),
        ("a\\nx", 1),
        ("a')", 1),
        ("a'x", 1),
        ('a"x', 1),
        ("ax ", 2),
    ),
)
def test_end_of_path(path: str, pos_expected: int) -> None:
    pos = PathMatch.pos_end_of_path(path=path)
    assert pos == pos_expected, (pos, pos_expected)


@pytest.mark.parametrize(
    "line,line_expected",
    (
        (
            "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt B",
            'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a> B',
        ),
        (
            "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt",
            'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>',
        ),
        (
            "x=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt')",
            'x=<a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>&#x27;)',
        ),
        (
            "A /home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt B /home/worktree/micropython/.gitignore c",
            'A <a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a> B <a href="http:/t/.gitignore">.gitignore</a> c',
        ),
        (
            "/home/worktree/micropython/.gitignore /home/worktree/micropython/.gitignore",
            '<a href="http:/t/.gitignore">.gitignore</a> <a href="http:/t/.gitignore">.gitignore</a>',
        ),
        (
            "x",
            "x",
        ),
        (
            "",
            "",
        ),
        (
            "/home/worktree/micropython/.gitignore'",
            '<a href="http:/t/.gitignore">.gitignore</a>&#x27;',
        ),
        (
            "A/home/worktree/micropython/.gitignore\nB/home/worktree/micropython/.gitignore\n",
            'A<a href="http:/t/.gitignore">.gitignore</a>\nB<a href="http:/t/.gitignore">.gitignore</a>\n',
        ),
        (
            "--result-dir=/home/testresults/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt')",
            '--result-dir=<a href="https:/r/RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt">RUN-TESTS_EXTMOD_HARDWARE@5f2c-RPI_PICO_W/testresults.txt</a>&#x27;)',
        ),
    ),
)
def test_replace(line: str, line_expected: str) -> None:
    replace = PathReplace(
        directories={
            "R": "/home/testresults",
            "T": "/home/worktree/micropython",
        },
        git_ref={},
        urls={
            "R": "https://r/",
            "T": "http://t/",
        },
    )
    segments = replace.expand_href(segments=Segments([line]))
    line_result = Segments(segments).as_string()
    if line_result != line_expected:
        print("line:    " + line)
        print("result:  " + line_result)
        print("expected:" + line_expected)
        raise ValueError("Test failed")
