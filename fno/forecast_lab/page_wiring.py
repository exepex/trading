"""Composition root of story FL1-1c, the 15:45 message's content: the page builder over FL1's G13b adapter and
G13b's history, the reasons' facts (the repository's tables and P8's FII/DII flows archive), the renderer (the
interim drawing until the designer's is signed off) and headless Chromium for the picture."""

from __future__ import annotations

from datetime import date

from ..config import ROOT
from ..research_data.calendar import SessionCalendar
from .g13b_history import G13bHistory
from .maker import ReportMaker
from .page.builder import PageBuilder
from .page.camera import ChromiumCamera
from .page.facts import RepositoryFacts
from .page.render import InterimRenderer
from .ranges import RangeSource
from .sessions import RegularSessions

PICTURE_WIDTH = 600  # CSS pixels: the picture page's own width, so a phone does not shrink it to unreadable


def flows_reader(calendar: SessionCalendar):
    """Session -> (FII net, DII net) in Rs crore, up to a day, from P8's archive (read-only)."""
    from ..market_read_models.frame_inputs import FlowsReader
    from ..market_read_models.wiring import build_versioned_reader

    reader = FlowsReader(build_versioned_reader(), calendar)

    def flows(day: date) -> dict[date, tuple[float, float]]:
        return {c.day: (c.fii.net, c.dii.net) for c in reader.on(day).cash}

    return flows


def build_report_maker(ranges: RangeSource, forecasts, scores, calendar: SessionCalendar) -> ReportMaker:
    """`forecasts`, `scores`: G13b's `RangeForecasts` and `RangeScores` over the synced Drive cache."""
    pages = PageBuilder(ranges, G13bHistory(forecasts, scores), RepositoryFacts(ROOT, flows_reader(calendar)),
                        RegularSessions(calendar))  # fmt: skip
    return ReportMaker(pages, InterimRenderer(), ChromiumCamera(width=PICTURE_WIDTH))
