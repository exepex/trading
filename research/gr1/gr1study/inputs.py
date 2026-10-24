"""GR1's real inputs (protocol section 3), all read-only: G13b's back-fill records and closes through the verified
Drive cache, India VIX, the event calendar, each index's option expiries from the archived F&O files, the global
cues by A17's rule, NIFTY's intraday realised variance and 09:15 price from A16b. Expiries are cached in the
untracked work folder (reading about 1,900 files takes about an hour), keyed by the files' SHA-256, never committed."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import date
from pathlib import Path

from .candidates import CUES, Context
from .cues import DECISION_CUTOFF, cue_move, cutoff_for, usdinr_rows
from .rows import Row

METHOD, LABEL = "8d7d730170d1f67311b8112f6f811a079eae981b44b99c7224d8557c79664ce3", "backfill_eod"
EVENT_TYPES = ("rbi_policy", "budget", "election_result")
Z95 = 1.6448536269514722
ROOT = Path(__file__).resolve().parents[3]
EXPIRY_CACHE = ROOT / "work" / "gr1" / "expiries.json"


def back_fill_records() -> list[dict]:
    from fno.price_ranges.cli import CACHE_PREFIX
    from fno.price_ranges.reader import RangeForecasts
    from fno.price_ranges.wiring import CACHE_ROOT, build_store, build_tables

    report = build_tables(build_store()).cache.sync(CACHE_PREFIX)
    if not report.complete:
        raise RuntimeError(f"the Drive cache could not verify every file: {report.problems}")
    found = RangeForecasts(CACHE_ROOT, None).backfill()
    return [r for r in found if r["method_sha256"] == METHOD and r["label"] == LABEL]


def closes():
    from fno.price_ranges.closes import Outcomes
    from fno.price_ranges.wiring import build_closes, build_store, build_tables

    outcomes = Outcomes(build_closes(build_tables(build_store())))
    return outcomes.close


def vix(path=ROOT / "research/data/vix/india_vix_daily.csv") -> dict[date, float]:
    return {date.fromisoformat(r["date"]): float(r["close"]) for r in csv.DictReader(path.open())}


def events(path=ROOT / "research/data/events/events.csv") -> dict[date, date]:
    return {date.fromisoformat(r["date"]): date.fromisoformat(r["announced_on"])
            for r in csv.DictReader(path.open()) if r["type"] in EVENT_TYPES and r["announced_on"]}  # fmt: skip


def rv_session(folder=ROOT / "research/data/intraday/rv-candle") -> dict[date, float]:
    found = {}
    for path in sorted(folder.glob("*/nifty_rv_candle_*.csv")):
        for r in csv.DictReader(path.open()):
            if r["status"] == "ok" and r["rv_session"]:
                found[date.fromisoformat(r["session"])] = float(r["rv_session"])
    return found


def opens(first: date, last: date) -> dict[date, float]:
    """NIFTY's 09:15 price: the 09:15 candle's open (A16b's rule, `session_candles(...).levels[0]`)."""
    from fno.intraday.backfill_wiring import build_candle_archive
    from fno.intraday.candle_levels import parse_candles, session_candles

    candles = []
    for copy in build_candle_archive().copies("15m", first, last):
        candles += parse_candles(copy.rows)
    days = sorted({c.start.date() for c in candles})
    found = {}
    for day in days:
        level = session_candles(day, candles).levels[0]
        if level is not None:
            found[day] = level
    return found


def expiries(days: list[date]) -> dict[str, dict[date, frozenset[date]]]:
    """Each index's expiries as listed in each day's own F&O file (judge 442 SF2: never a union across files)."""
    from fno.fo_bhavcopy import BadFile, read_fo_file
    from fno.storage.wiring import build_nifty_panel_files

    cached = json.loads(EXPIRY_CACHE.read_text()) if EXPIRY_CACHE.is_file() else {"files": {}}
    fo_files, _ = build_nifty_panel_files()
    for day in days:
        if day.isoformat() in cached["files"]:
            continue
        for files in fo_files:
            if not files.covers(day):
                continue
            name, data = files.get(day)
            if data is None:
                continue
            try:
                rows = read_fo_file(name, data)
            except BadFile:
                continue
            listed = {u: sorted({r["XpryDt"][:10] for r in rows if r["TckrSymb"] == u and r["FinInstrmTp"] == "IDO"})
                      for u in ("NIFTY", "BANKNIFTY")}  # fmt: skip
            cached["files"][day.isoformat()] = {"sha256": hashlib.sha256(data).hexdigest(), "expiries": listed}
            break
    EXPIRY_CACHE.parent.mkdir(parents=True, exist_ok=True)
    EXPIRY_CACHE.write_text(json.dumps(cached, sort_keys=True))
    wanted = {d.isoformat() for d in days}
    return {u: {date.fromisoformat(d): frozenset(date.fromisoformat(e) for e in f["expiries"][u])
                for d, f in cached["files"].items() if d in wanted} for u in ("NIFTY", "BANKNIFTY")}  # fmt: skip


def cue_reader():
    """Each cue's rows and source (A17's tables; S&P 500 is private, in Drive)."""
    from fno.global_cues.wiring import SOURCES, build_tables

    tables = build_tables(include_private=True)
    sources = {s.cue: s for s in SOURCES}
    rows = {cue: tables[cue].rows() for cue in CUES}
    rows["usdinr_rbi"] = usdinr_rows(rows["usdinr_rbi"], tables["usdinr_fbil"].rows())

    def move(cue: str, day: date, cutoff=DECISION_CUTOFF) -> float | None:
        return cue_move(rows[cue], sources[cue], day, cutoff_for(cue, cutoff))

    return move


def implied_variance(rows: list[Row]) -> dict[tuple[str, date], float]:
    """Implied's one-session variance at the day: its N1 90% band read as a normal one (C8's denominator)."""
    n1 = [r for r in rows if r.horizon == "N1"]
    return {(r.underlying, r.day): ((r.quantiles[4] - r.quantiles[0]) / (2 * Z95)) ** 2 for r in n1}


def train_stats(vix_by_day: dict[date, float], train_days: list[date]) -> tuple[float, tuple[float, float]]:
    values = sorted(vix_by_day[d] for d in train_days if d in vix_by_day)
    logs = sorted(math.log(v) for v in values)
    n = len(values)
    mid = logs[n // 2] if n % 2 else (logs[n // 2 - 1] + logs[n // 2]) / 2
    return mid, (values[n // 3], values[(2 * n) // 3])


def up_to(values: dict[date, float], last: date) -> dict[date, float]:
    """Run 1 holds no value of a day after its last sealed day (section 12 (a): nothing of 2025-26 is loaded)."""
    return {d: v for d, v in values.items() if d <= last}


def context(rows: list[Row], calendar, stats: tuple[float, tuple[float, float]] | None = None) -> Context:
    """Run 1 computes the train statistics from its train days; run 2 passes run 1's (`selection.json`)."""
    last = max(r.day for r in rows)
    vix_by_day = up_to(vix(), last)
    if stats is None:
        stats = train_stats(vix_by_day, sorted({r.day for r in rows if r.period == "train"}))
    days = sorted({r.day for r in rows})
    return Context(vix_by_day, calendar.previous_session, events(), expiries(days), cue_reader(),
                   up_to(rv_session(), last), implied_variance(rows), stats[0], tuple(stats[1]))  # fmt: skip
