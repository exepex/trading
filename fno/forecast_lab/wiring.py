"""Composition root of story FL1-1, the forecast lab's 15:45 report: G13b's reader and closes (synced verified from
Drive into O9's cache first), FL1's adapter, O9's data store for the report's records, T1's Slack poster pointed at
#fno-forecast, the alert sender for #fno-desk, the A7 calendar and the IST clock."""

from __future__ import annotations

import os

from ..cards.posting import CardPoster, NoCardPoster, SlackCardPoster
from ..composition import build_alert_sender, build_session_calendar
from ..constants import ENV_FNO_SLACK_BOT_TOKEN, FNO_FORECAST_CHANNEL_ID
from ..models import now_ist
from ..storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER, build_data_store, build_drive_cache, receipt_folder
from .constants import REPORT_AREA
from .g13b_adapter import G13bCloses, G13bRanges
from .lab_close import CloseReport, LabClose
from .match import MatchSection
from .records import DriveReportRecords

WRITER = "lab-close"
UNSYNCED = "G13b's records could not be read verified from Drive: {problems}"


def receipt_pathspecs() -> tuple[str, ...]:
    """The receipts of the lab's own Drive files only (O1's step commits these), never a shared folder."""
    return (f"{RECEIPTS_FOLDER}/{DATA_AREA}/{REPORT_AREA}/",)


def build_forecast_poster(env=os.environ) -> CardPoster:
    """#fno-forecast with `FNO_SLACK_BOT_TOKEN` only; without it nothing is sent and the outcome says so."""
    token = env.get(ENV_FNO_SLACK_BOT_TOKEN)
    return SlackCardPoster(token, FNO_FORECAST_CHANNEL_ID) if token else NoCardPoster()


def build_lab_close(env=os.environ) -> LabClose:
    from ..price_ranges import wiring as g13b
    from ..price_ranges.closes import Outcomes
    from ..price_ranges.folders import LIVE, SCORES, drive
    from ..price_ranges.reader import RangeForecasts, RangeScores

    cache = build_drive_cache(env)
    problems = [p for prefix in (drive(LIVE), drive(SCORES)) for p in cache.sync(prefix).problems]
    if problems:
        raise RuntimeError(UNSYNCED.format(problems="; ".join(problems)))
    store = g13b.build_store(env)
    ranges = G13bRanges(RangeForecasts(g13b.CACHE_ROOT, g13b.build_seals(store)), RangeScores(g13b.CACHE_ROOT))
    closes = G13bCloses(Outcomes(g13b.build_closes(g13b.build_tables(store))))
    calendar = build_session_calendar()
    report = CloseReport(ranges, MatchSection(ranges, closes, calendar.previous_session))
    records = DriveReportRecords(build_data_store(WRITER, env=env), receipt_folder())
    return LabClose(report, records, build_forecast_poster(env), build_alert_sender(), calendar.session_kind, now_ist)
