"""The Asian index levels before NSE's 09:15 open (story A17e part B): one Yahoo 5-minute read per Asian index that is
open by about 08:50 IST, called from A22's pre-open routine between its GIFT Nifty and pre-open windows.

Each read archives the raw answer in Drive with its snapshot-log row (A17's write-once rule), then appends one row to
the private table in Drive: the index, when we saw it, the time and value of its newest 5-minute level, that index's
previous close (A17e's reading at the open, live view: what was known then), and a status:
- `live`: the newest level is at most `STALE_AFTER` old when seen;
- `stale`: older than that (Yahoo's feed paused or delayed);
- `market closed`: the newest level is not from today in the market's own time zone (a holiday there).
A block (HTTP 401, 403 or 429, a redirect, a page that is not chart data) stops that index with no retry, exactly as
A17e's daily Yahoo cues (owner rule 50a79a43, rule 2); the other indexes still run.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from ..models import IST
from ..storage.row_log import RowLog
from .markets import MarketClose
from .snapshot_log import SnapshotLog, SnapshotRow
from .source import CueRequest, positive
from .yahoo_source import YahooChartSource, chart_result

YAHOO_INTRADAY = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=5m"
STALE_AFTER = timedelta(minutes=20)
LIVE, STALE, CLOSED, LUNCH = "live", "stale", "market closed", "lunch break"
BAR = timedelta(minutes=5)
ROW_FIELDS = ("index", "seen_at", "level_time", "level", "status", "previous_close", "previous_close_cue", "sha256")
RAW_FOLDER = "yahoo/preopen"


@dataclass(frozen=True)
class PreopenLevel:
    index: str
    seen_at: datetime
    level_time: datetime
    level: float  # private: never printed
    status: str


def level_status(seen_at: datetime, level_time: datetime, market: MarketClose) -> str:
    """`market closed` (no level today), `lunch break` (the market's midday break: the morning's last level), else
    `live` or `stale` by the level's age."""
    zone = ZoneInfo(market.zone)
    if level_time.astimezone(zone).date() != seen_at.astimezone(zone).date():
        return CLOSED
    if market.at_lunch(seen_at):
        return LUNCH
    return STALE if seen_at - level_time > STALE_AFTER else LIVE


def newest_level(index: str, data: bytes, seen_at: datetime, market: MarketClose) -> PreopenLevel:
    """The newest 5-minute close in a Yahoo chart answer, timed at its bar's end (or now, for the bar still running);
    ValueError when there is none or the layout changed. Never shows a level in an error."""
    result = chart_result(data, index)
    stamps, closes = result.get("timestamp") or [], result["indicators"]["quote"][0]["close"]
    if len(stamps) != len(closes):
        raise ValueError(f"{index}: not one close per timestamp in Yahoo's answer")
    points = [(t, c) for t, c in zip(stamps, closes, strict=True) if c is not None]
    if not points:
        raise ValueError(f"{index}: no 5-minute level in Yahoo's answer")
    stamp, level = points[-1]
    try:
        bar_start = datetime.fromtimestamp(stamp, ZoneInfo(result["meta"]["exchangeTimezoneName"]))
    except (OverflowError, OSError):
        raise ValueError(f"{index}: an impossible timestamp in Yahoo's answer") from None
    level_time = min(bar_start + BAR, seen_at)
    value = positive(level, index, True)
    return PreopenLevel(index, seen_at, level_time, value, level_status(seen_at, level_time, market))


class PreopenReader:
    def __init__(
        self,
        session: requests.Session,
        archive,
        log: SnapshotLog,
        rows: RowLog,
        previous_close: Callable[[str, datetime], tuple[str, str]],
        clock: Callable[[], datetime],
    ):
        """`previous_close(index, seen_at)`: the index's value and cue known at the open ("" when none)."""
        self.session, self.archive, self.log, self.rows = session, archive, log, rows
        self.previous_close, self.clock = previous_close, clock

    def read(self, source: YahooChartSource, index: str) -> tuple[str, str]:
        """One index's line and status; raises requests.RequestException (a block included) or ValueError."""
        request = CueRequest(f"{index}_5m.json", YAHOO_INTRADAY.format(symbol=source.symbol.replace("^", "%5E")))
        data = source.download(self.session, request)  # A17e's block rule: no retry, no other way
        seen_at = self.clock().astimezone(IST)
        level = newest_level(index, data, seen_at, source.market)
        sha256 = self._archive(index, request, data, seen_at)
        close, close_cue = self.previous_close(index, seen_at)
        self.rows.append(ROW_FIELDS, [_row(level, close, close_cue, sha256)])
        age = round((seen_at - level.level_time).total_seconds() / 60)
        line = f"{index}: {level.status}, level of {level.level_time:%H:%M} {level.level_time.tzname()} ({age} min old)"
        return line, level.status

    def _archive(self, index: str, request: CueRequest, data: bytes, seen_at: datetime) -> str:
        path = f"{RAW_FOLDER}/{seen_at:%Y/%m/%d}/{seen_at:%H%M%S}_{request.name}"
        sha256 = hashlib.sha256(data).hexdigest()
        self.archive.put(path, data)
        self.log.append(f"{index}_preopen", SnapshotRow(seen_at, path, request.url, (), sha256, len(data)))
        return sha256


def _row(level: PreopenLevel, close: str, close_cue: str, sha256: str) -> tuple:
    return (
        level.index,
        level.seen_at.isoformat(timespec="seconds"),
        level.level_time.isoformat(),
        repr(level.level),
        level.status,
        close,
        close_cue,
        sha256,
    )
