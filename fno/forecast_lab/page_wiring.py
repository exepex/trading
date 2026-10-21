"""Composition root of the report editions' content (stories FL1-1c and FL1-1d): the page builder over FL1's G13b
adapter, G13b's history and official closes, the evening's own close (none until A4h's reader), the reasons' facts
(the repository's tables and P8's FII/DII flows archive), the renderer (the interim drawing until the designer's is
signed off) and headless Chromium for the picture."""

from __future__ import annotations

import functools
from datetime import date

from ..config import ROOT
from ..research_data.calendar import SessionCalendar
from .g13b_history import G13bHistory
from .maker import ReportMaker
from .page.builder import PageBuilder
from .page.camera import ChromiumCamera
from .page.cues import Section
from .page.facts import RepositoryFacts
from .page.render import InterimRenderer
from .ranges import NoTodayCloses, Outcomes, RangeSource
from .sections.global_cues import SPECS, GlobalCueSection
from .sections.india import FlagsSection, PendingSection, VixSection
from .sections.levels import Levels
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


PARTICIPANT_OI = "participant-oi"
GIFT, GIFT_PENDING = "GIFT Nifty", "A22b's early GIFT file is not merged yet"


def build_sections(facts: RepositoryFacts, sessions: RegularSessions) -> tuple[Section, ...]:
    """The cues' Sections, one source each: A17's overnight cues (read only), India VIX from NSE's archived file, the
    day's flags, and GIFT Nifty (pending A22b). A new source is one class and one line here."""
    from ..global_cues.as_of import OPEN
    from ..global_cues.wiring import build_reader
    from ..storage.wiring import build_index_close_files

    reader, known = functools.cache(build_reader), functools.cache(facts.facts)
    return (
        *(GlobalCueSection(reader, spec, OPEN) for spec in SPECS),
        VixSection(build_index_close_files(), sessions.previous, lambda day: known(day).vix),
        FlagsSection(known),
        PendingSection(GIFT, GIFT_PENDING),
    )


def build_levels(calendar: SessionCalendar, sessions: RegularSessions) -> Levels:
    """The evening's levels and flows: NSE's F&O files and A8's participant OI through the raw-file libraries (stores
    first, then NSE), P8's flows archive; all read-only here (the evening routine archives them first)."""
    from ..storage.raw_source import ParticipantOiSource
    from ..storage.wiring import build_nifty_panel_files, build_participant_oi_library, daily_files

    fo_files, _ = build_nifty_panel_files()
    participant = daily_files(PARTICIPANT_OI, ParticipantOiSource, build_participant_oi_library())
    return Levels(fo_files, participant, flows_reader(calendar), sessions.previous)


def build_report_maker(ranges: RangeSource, forecasts, scores, calendar: SessionCalendar,
                       official: Outcomes) -> ReportMaker:  # fmt: skip
    """`forecasts`, `scores`: G13b's `RangeForecasts` and `RangeScores` over the synced Drive cache."""
    facts, sessions = RepositoryFacts(ROOT, flows_reader(calendar)), RegularSessions(calendar)
    pages = PageBuilder(ranges, G13bHistory(forecasts, scores), facts, sessions, official=official,
                        today_closes=NoTodayCloses(), sections=build_sections(facts, sessions),
                        levels=build_levels(calendar, sessions))  # fmt: skip
    return ReportMaker(pages, InterimRenderer(), ChromiumCamera(width=PICTURE_WIDTH))
