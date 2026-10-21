"""Composition root of the forecast lab's two report editions (stories FL1-1 and FL1-1d): G13b's reader and closes
(synced verified from Drive into O9's cache first, its back-fill too for the page's history), FL1's adapter, the
message's content (`page_wiring.py`), O9's data store for each edition's records, the Slack file poster pointed at
#fno-forecast, the alert sender for #fno-desk, the A7 calendar and the IST clock. Each edition is live from its own
`forecast_lab.live_from` date in config.yaml."""

from __future__ import annotations

import os
from datetime import date

from ..composition import build_alert_sender, build_session_calendar
from ..config import load_app_config
from ..constants import ENV_FNO_SLACK_BOT_TOKEN, FNO_FORECAST_CHANNEL_ID
from ..models import now_ist
from ..storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER, build_data_store, build_drive_cache, receipt_folder
from .composers import EveningComposer, MorningComposer
from .confirm import Confirmation
from .constants import EVENING, MORNING, MORNING_BY, REPORT_AREAS
from .delivery import NoReportPoster, ReportPoster, SlackFilesPoster
from .edition_run import Edition, EditionRun
from .g13b_adapter import G13bCloses, G13bRanges
from .match import MatchSection
from .official_closes import ArchivedCloses
from .page_wiring import build_report_maker
from .records import DriveReportRecords
from .report import CloseReport
from .sessions import RegularSessions

WRITER = "forecast-lab"
UNSYNCED = "G13b's records could not be read verified from Drive: {problems}"


def receipt_pathspecs(edition: str) -> tuple[str, ...]:
    """The receipts of one edition's own Drive files only (its routine commits these), never a shared folder."""
    return (f"{RECEIPTS_FOLDER}/{DATA_AREA}/{REPORT_AREAS[edition]}/",)


def build_forecast_poster(env=os.environ) -> ReportPoster:
    """#fno-forecast with `FNO_SLACK_BOT_TOKEN` only; without it nothing is sent and the outcome says so."""
    token = env.get(ENV_FNO_SLACK_BOT_TOKEN)
    return SlackFilesPoster(token, FNO_FORECAST_CHANNEL_ID) if token else NoReportPoster()


def live_from(cfg: dict) -> dict[str, date | None]:
    """`forecast_lab.live_from`: each edition's first live day; an edition without one is not live."""
    raw = (cfg.get("forecast_lab") or {}).get("live_from") or {}
    return {e: date.fromisoformat(str(raw[e])) if raw.get(e) else None for e in (MORNING, EVENING)}


def g13b_issues_from(cfg: dict) -> date | None:
    """G13b's first live day: no forecast is expected from an issue day before it."""
    from ..daily.wiring import live_dates

    return live_dates(cfg)["price_ranges"]


def records(edition: str, env=os.environ) -> DriveReportRecords:
    return DriveReportRecords(build_data_store(WRITER, env=env), receipt_folder(), REPORT_AREAS[edition])


def build_edition(edition: str, env=os.environ) -> EditionRun:
    from ..price_ranges import wiring as g13b
    from ..price_ranges.closes import IndexFileCloses, Outcomes
    from ..price_ranges.folders import BACKFILL, LIVE, SCORES, drive
    from ..price_ranges.reader import RangeForecasts, RangeScores
    from ..storage.wiring import build_index_close_files

    cache = build_drive_cache(env)
    problems = [p for prefix in (drive(LIVE), drive(SCORES), drive(BACKFILL)) for p in cache.sync(prefix).problems]
    if problems:
        raise RuntimeError(UNSYNCED.format(problems="; ".join(problems)))
    store = g13b.build_store(env)
    forecasts, scores = RangeForecasts(g13b.CACHE_ROOT, g13b.build_seals(store)), RangeScores(g13b.CACHE_ROOT)
    ranges = G13bRanges(forecasts, scores)
    calendar, cfg = build_session_calendar(), load_app_config()
    closes = ArchivedCloses(G13bCloses(Outcomes(g13b.build_closes(g13b.build_tables(store)))),
                            IndexFileCloses(build_index_close_files(), calendar))  # fmt: skip
    sessions, live = RegularSessions(calendar), live_from(cfg)
    maker = build_report_maker(ranges, forecasts, scores, calendar, closes)
    evenings, own = records(EVENING, env), records(edition, env)
    if edition == MORNING:
        composer = MorningComposer(maker, Confirmation(evenings.report, own.report, closes, sessions))
    else:
        report = CloseReport(ranges, MatchSection(ranges, closes, sessions, g13b_issues_from(cfg)), live[EVENING])
        composer = EveningComposer(report, maker, own.report)
    cutoff = MORNING_BY if edition == MORNING else None
    return EditionRun(Edition(edition, live[edition], cutoff), composer, own, build_forecast_poster(env),
                      build_alert_sender(), sessions.is_regular, now_ist)  # fmt: skip
