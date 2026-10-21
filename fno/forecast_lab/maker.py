"""The 15:45 message's content (story FL1-1c): the 3 text lines, the picture and the details file, from one page
model, so all three tell the same numbers. A picture that cannot be made never stops the report: the message goes
with the details file only, and one alert says why (never silently)."""

from __future__ import annotations

import tempfile
from datetime import date, datetime
from pathlib import Path

from .delivery import Attachment
from .page.builder import PageBuilder
from .page.camera import PageCamera, PictureFailed
from .page.plain import slack_lines
from .page.render import PageRenderer

PICTURE_FAILED = "the 15:45 picture was not made ({reason}); the text and the details file were posted without it"
PICTURE_TITLE, DETAILS_TITLE = "Today's forecast", "Details (open in a browser)"


class ReportMaker:
    def __init__(self, pages: PageBuilder, renderer: PageRenderer, camera: PageCamera):
        self.pages, self.renderer, self.camera = pages, renderer, camera

    def make(self, day: date, now: datetime, alerts: tuple[str, ...], checks: str) -> tuple[str, tuple, tuple]:
        """(the text, the files, the extra alerts). `checks`: FL1-1's seal-check and match lines, for the details."""
        view = self.pages.build(day, now, alerts, tuple(line for line in checks.splitlines() if line.strip()))
        details = Attachment(f"forecast-{day.isoformat()}.html", self.renderer.details(view).encode("utf-8"),
                             DETAILS_TITLE)  # fmt: skip
        text = "\n".join(slack_lines(view))
        try:
            picture = self._picture(self.renderer.picture(view))
        except PictureFailed as failed:
            return text, (details,), (PICTURE_FAILED.format(reason=failed),)
        return text, (Attachment(f"forecast-{day.isoformat()}.png", picture, PICTURE_TITLE), details), ()

    def _picture(self, html: str) -> bytes:
        with tempfile.TemporaryDirectory() as folder:
            return self.camera.picture(html, Path(folder) / "picture.png").read_bytes()
