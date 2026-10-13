"""India's market band and coming-up expiries (story P10, contract 2.5: publisher fno for India), each a pure function
of the session's rows: `session` (Session: the session being predicted, its hours and when the next market run brings
its close), `indices` (Indices: NIFTY 50 and India VIX at the close) and `fno_events` (Events: the NIFTY expiries NSE
lists, monthly and weekly; the route applies each screen's query)."""

from __future__ import annotations

import calendar as months
from datetime import UTC, date, datetime, time, timedelta

from ..models import IST
from .blocks import BlockBuilder, SessionRows, as_of
from .home_blocks import FiguresNotComputed

EXCHANGE, ZONE = "India (NSE)", "IST"
OPEN_IST, CLOSE_IST = time(9, 15), time(15, 30)  # NSE's regular hours; its special sessions keep them (calendar notes)
MARKET_RUN_IST = time(7, 10)  # the next morning's market run brings the close (market-publish.yml)
MUHURAT = "muhurat"
NO_MUHURAT_HOURS = (
    "{day} is a muhurat session: its hours are not in the session calendar's fields, so the session block is not "
    "published rather than guessed (add them when NSE's timings circular is issued)"
)
INDEX_LEVELS = (  # (name in NSE's index file, id, symbol, name, role)
    ("Nifty 50", "NIFTY50", "NIFTY 50", "Index · NSE", "benchmark"),
    ("India VIX", "INDIAVIX", "INDIA VIX", "Volatility index · NSE", "vol_index"),
)
NO_CLOSE = "{index} has no stored close for {day}: the indices block is never published with a made-up level"
MONTHLY_TITLE, MOVED_TITLE = "NSE monthly F&O expiry (last Tuesday)", "NSE monthly F&O expiry (moved for a holiday)"
WEEKLY_TITLE = "NIFTY weekly expiry"
TUESDAY = 1


def utc(day: date, at: time) -> str:
    return datetime.combine(day, at, IST).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class SessionIndiaBlock(BlockBuilder):
    page_key, served_schema = "session", "SessionIndiaResponse"

    def build(self, rows: SessionRows) -> dict:
        frame = rows.frame
        predicted = frame.next_session
        if frame.next_session_kind == MUHURAT:
            raise FiguresNotComputed(NO_MUHURAT_HOURS.format(day=predicted))
        majors = [e["title"] for e in fno_events(rows) if e["date"] == predicted.isoformat() and e["major"]]
        return {
            "exchange": EXCHANGE, "zone": ZONE, "session_date": predicted.isoformat(),
            "open_utc": utc(predicted, OPEN_IST), "close_utc": utc(predicted, CLOSE_IST),
            "next_open_utc": utc(predicted, OPEN_IST), "regime": None,  # no regime is recorded by the F&O tool yet
            "post_close_at": utc(predicted + timedelta(days=1), MARKET_RUN_IST), "major_event_names": majors,
        }  # fmt: skip


class IndicesIndiaBlock(BlockBuilder):
    page_key, served_schema = "indices", "IndicesIndiaResponse"

    def build(self, rows: SessionRows) -> dict:
        by_name = {r["name"]: r for r in rows.indices}
        levels = []
        for source_name, ref, sym, name, role in INDEX_LEVELS:
            row = by_name.get(source_name)
            if row is None or row["close"] is None or row["d1"] is None or row["w1"] is None:
                raise FiguresNotComputed(NO_CLOSE.format(index=sym, day=rows.day))
            levels.append({
                "id": ref, "sym": sym, "name": name, "role": role, "last": row["close"], "chg_pct": row["d1"],
                "chg_5d_pct": row["w1"], "as_of": as_of(date.fromisoformat(row["as_of"])), "source": "close",
            })  # fmt: skip
        return {"indices": levels}


class FnoEventsBlock(BlockBuilder):
    page_key, served_schema = "fno_events", "FnoEventsResponse"

    def build(self, rows: SessionRows) -> dict:
        return {"events": fno_events(rows)}


def fno_events(rows: SessionRows) -> list[dict]:
    """The NIFTY expiries NSE lists after the session (the chain's scope: the next three calendar months)."""
    return [_event(date.fromisoformat(e["expiry"]), e["monthly"]) for e in rows.chain.expiries]


def _event(expiry: date, monthly: bool) -> dict:
    title = WEEKLY_TITLE
    if monthly:
        title = MONTHLY_TITLE if expiry == _last_tuesday(expiry) else MOVED_TITLE
    kind = "fno_expiry" if monthly else "weekly_expiry"
    return {"date": expiry.isoformat(), "title": title, "kind": kind, "major": monthly, "inst": None}


def _last_tuesday(day: date) -> date:
    last = date(day.year, day.month, months.monthrange(day.year, day.month)[1])
    return last - timedelta(days=(last.weekday() - TUESDAY) % 7)
