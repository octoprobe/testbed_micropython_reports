from __future__ import annotations

import html
import io
from contextlib import contextmanager

from markupsafe import Markup


class Segments(list[str | Markup]):
    def write(self, fout: io.StringIO) -> None:
        for segment in self:
            if isinstance(segment, Markup):
                fout.write(segment)
                continue
            if isinstance(segment, str):
                fout.write(html.escape(segment))
                continue
            raise ValueError(f"Expected str or Markup: {segment!r}")

    def as_string(self) -> str:
        fout = io.StringIO()
        self.write(fout=fout)
        return fout.getvalue()

    @contextmanager
    def tag(self, tag: str, params: str):
        self.append(Markup(f"<{tag} {params}>"))
        yield self
        self.append(Markup(f"</{tag}>"))
