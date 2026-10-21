"""A report edition's message content (stories FL1-1c and FL1-1d): the text lines, the picture and the details file,
from one page model, so all three tell the same numbers. A picture that cannot be made never stops the report: the
message goes with the details file only, and one alert says why (never silently). The evening edition's verdicts
(today's close against the forecast for today) come from the same page, so the record keeps what the message said."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .delivery import Attachment
from .page.builder import PageBuilder
from .page.camera import PageCamera, PictureFailed
from .page.model import PageView
from .page.plain import slack_lines
from .page.render import PageRenderer
from .written import Verdict

PICTURE_FAILED = "the {edition} picture was not made ({reason}); the text and the details file were posted without it"
PICTURE_TITLE, DETAILS_TITLE = "Today's forecast", "Details (open in a browser)"


@dataclass(frozen=True)
class Made:
    text: str
    files: tuple[Attachment, ...]
    alerts: tuple[str, ...]  # the maker's own (a picture not made)
    verdicts: tuple[Verdict, ...]


def verdicts(view: PageView) -> tuple[Verdict, ...]:
    """Each index's check of today's forecast on the evening's own close, as the page shows it."""
    out = []
    for index in view.indices:
        points = index.horizons[0].timeline.points if index.horizons else ()
        last = points[-1] if points else None
        if last is not None and last.day == view.day and last.provisional:
            b = last.band
            out.append(Verdict(index.underlying, view.day, index.method, last.close, last.inside_50, last.inside_90,
                               (b.q05, b.q25, b.q75, b.q95)))  # fmt: skip
    return tuple(out)


class ReportMaker:
    def __init__(self, pages: PageBuilder, renderer: PageRenderer, camera: PageCamera):
        self.pages, self.renderer, self.camera = pages, renderer, camera

    def make(self, day: date, now: datetime, edition: str, alerts: tuple[str, ...] = (), checks: str = "",
             confirmation: tuple[str, ...] = ()) -> Made:  # fmt: skip
        """`checks`: FL1-1's seal-check and match lines, for the details; `confirmation`: the morning's lines."""
        lines = tuple(line for line in checks.splitlines() if line.strip())
        view = self.pages.build(day, now, edition, alerts, lines, confirmation)
        name = f"forecast-{edition}-{day.isoformat()}"
        details = Attachment(f"{name}.html", self.renderer.details(view).encode("utf-8"), DETAILS_TITLE)
        text = "\n".join(slack_lines(view))
        try:
            picture = self._picture(self.renderer.picture(view))
        except PictureFailed as failed:
            return Made(text, (details,), (PICTURE_FAILED.format(edition=edition, reason=failed),), verdicts(view))
        return Made(text, (Attachment(f"{name}.png", picture, PICTURE_TITLE), details), (), verdicts(view))

    def _picture(self, html: str) -> bytes:
        with tempfile.TemporaryDirectory() as folder:
            return self.camera.picture(html, Path(folder) / "picture.png").read_bytes()
