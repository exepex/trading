"""Fakes for the candle back-fill (story A16b). Every level here is made up (fake), never a real NIFTY value."""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import date, datetime, timedelta

from fno.global_cues.cue_calendars import NseSessionCalendar
from fno.intraday.backfill import CandleBackfill
from fno.intraday.backfill_daily import DEFERRALS
from fno.intraday.backfill_verify import CandleRowVerifier
from fno.intraday.candle_archive import CandleArchive
from fno.intraday.candle_rv_table import CandleRvTable
from fno.intraday.candle_source import FIFTEEN_MINUTES, ONE_MINUTE, CandleAnswer, CandleCallFailed, IntradayCandleSource
from fno.intraday.deferral_log import DeferralLog
from fno.intraday.nse_days import NseDays, NseReadFailed, NseReading
from fno.intraday.nse_range import NseDay
from fno.intraday.realised_vol import CandleCloseRv15m
from fno.intraday.session_deriver import SessionDeriver
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.raw_store import AreaStore, LocalFolderStore

SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2026-10-02,holiday,example holiday,{SOURCE}\n"
    f"2026-10-10,special,example Saturday session,{SOURCE}\n"
    f"2026-10-21,muhurat,example muhurat,{SOURCE}\n"
)
START = date(2026, 9, 28)  # a Monday: the test series' first session
FETCHED = datetime(2026, 10, 30, 18, 0, tzinfo=IST)  # after every test session: back-filled


def levels(day: date, base: float = 20000.0) -> list[float]:
    """26 fake levels that move a little each mark (0.25-point steps, so every value is exact in binary)."""
    seed = day.toordinal() % 7
    return [base + seed + 2.25 * k - (k % 3) * 1.5 for k in range(26)]


def t(day: date, hour: int, minute: int) -> str:
    return f"{day}T{hour:02d}:{minute:02d}:00"


def fifteen_minute_rows(day: date, values: list[float], drop: tuple[int, ...] = (), extra: bool = True) -> list:
    """The day's candles 09:15 ... 15:15 (open of the first = values[0], close of candle k = values[k + 1]); with the
    09:00 pre-open and 15:30 candles that are never levels."""
    rows = [[t(day, 9, 0), values[0], values[0] + 1, values[0] - 1, values[0], None, None]] if extra else []
    for k in range(25):
        if k in drop:
            continue
        start = datetime.combine(day, datetime.min.time()) + timedelta(hours=9, minutes=15 + 15 * k)
        o, c = values[k], values[k + 1]
        rows.append([t(day, start.hour, start.minute), o, max(o, c) + 0.5, min(o, c) - 0.5, c, None, None])
    if extra:
        rows.append([t(day, 15, 30), values[-1], values[-1], values[-1], values[-1], None, None])
    return rows


def minute_rows(day: date, values: list[float], pre_open: float, skip: tuple[str, ...] = ()) -> list:
    """1-minute candles 09:00-15:29 agreeing with `values` at every mark; the pre-open minutes close at `pre_open`."""
    rows, moment = [], datetime.combine(day, datetime.min.time()) + timedelta(hours=9)
    end = moment + timedelta(hours=6, minutes=30)
    while moment < end:
        hhmm = f"{moment:%H:%M}"
        minutes_after = (moment.hour * 60 + moment.minute) - (9 * 60 + 15)
        if minutes_after < 0:
            o = c = pre_open
        else:
            k = minutes_after // 15
            o = values[k] if minutes_after % 15 == 0 else values[k] + 0.25
            c = values[k + 1] if minutes_after % 15 == 14 else values[k] + 0.25
        if hhmm not in skip:
            rows.append([t(day, moment.hour, moment.minute), o, max(o, c), min(o, c), c, None, None])
        moment += timedelta(minutes=1)
    return rows


def nse_day(day: date, values: list[float]) -> NseDay:
    rows = fifteen_minute_rows(day, values, extra=False)
    return NseDay(values[0] - 3.0, max(r[2] for r in rows), min(r[3] for r in rows))


class FakeGroww(IntradayCandleSource):
    """Candles per day; a day mapped to an exception fails its calls."""

    def __init__(self, days: dict, minutes: dict | None = None, failing: set | None = None, fetched=FETCHED):
        self.days, self.minute_rows, self.failing, self.calls = days, minutes or {}, failing or set(), []
        self.fetched = fetched  # when every answer is received

    def candles(self, start: date, end: date) -> CandleAnswer:
        self.calls.append((FIFTEEN_MINUTES, start, end))
        if ("window", start) in self.failing:
            raise CandleCallFailed(f"Groww 15m {start}..{end}: ReadTimeout")
        rows = [r for d, rs in sorted(self.days.items()) if start <= d <= end for r in rs]
        return _answer(FIFTEEN_MINUTES, start, end, rows, self.fetched)

    def minute_candles(self, day: date) -> CandleAnswer:
        self.calls.append((ONE_MINUTE, day, day))
        if ("minutes", day) in self.failing:
            raise CandleCallFailed(f"Groww 1m {day}..{day}: GrowwAPIException")
        return _answer(ONE_MINUTE, day, day, self.minute_rows.get(day, []), self.fetched)


def _answer(kind: str, start: date, end: date, rows: list, fetched: datetime) -> CandleAnswer:
    raw = json.dumps({"candles": rows}, sort_keys=True, separators=(",", ":")).encode()
    return CandleAnswer(kind, start, end, raw, rows, fetched, fetched)


class FakeNse(NseDays):
    """NSE's days: a NseDay, None (definitively absent) or an exception (a failed read)."""

    def __init__(self, days: dict):
        self.days = days

    def read(self, day: date) -> NseReading:
        found = self.days.get(day)
        if isinstance(found, Exception):
            raise NseReadFailed(f"NSE index-close {day}: {type(found).__name__}")
        return NseReading(found, "" if found is None else hashlib.sha256(repr(found).encode()).hexdigest())


def session_data(days: list[date], overrides: dict | None = None):
    """Groww and NSE answers for normal sessions; overrides adjust one day's pieces."""
    fifteen, minutes, nse = {}, {}, {}
    for day in days:
        values = levels(day)
        fifteen[day] = fifteen_minute_rows(day, values)
        minutes[day] = minute_rows(day, values, values[0] - 3.0)
        nse[day] = nse_day(day, values)
    for key, value in (overrides or {}).items():
        kind, day = key
        {"15m": fifteen, "1m": minutes, "nse": nse}[kind][day] = value
    return fifteen, minutes, nse


def build(tmp_path, groww: FakeGroww, nse: FakeNse, store=None, start: date = START) -> CandleBackfill:
    archive = CandleArchive(store or AreaStore(LocalFolderStore(tmp_path / "drive"), "raw"), tmp_path / "manifests")
    deriver = SessionDeriver(CandleCloseRv15m(), _next_session)
    repo = tmp_path / "repo"
    return CandleBackfill(
        groww, archive, nse, CandleRvTable(repo), DeferralLog(repo / DEFERRALS), deriver, CALENDAR, lambda: FETCHED,
        start,
    )  # fmt: skip


_next_session = NseSessionCalendar(CALENDAR, CALENDAR.first).next_open


def verifier(backfill: CandleBackfill) -> CandleRowVerifier:
    """`backfill-verify` over the same files and fakes as `backfill`."""
    return CandleRowVerifier(backfill.archive, backfill.nse, backfill.table, backfill.deriver, CALENDAR,
                             backfill.series_start)  # fmt: skip


def gunzip_json(data: bytes):
    return json.loads(gzip.decompress(data))
