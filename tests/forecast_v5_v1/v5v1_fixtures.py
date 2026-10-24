"""Real A16 and A16b rows (committed under research/data/intraday) for G14's tests. `candle_rows` stands in for G7b's
candle reader (amendment 1's interface: method rv-candle-15m-v1, value None when void) until it is on main; the
package itself never reads candle files (criterion 11)."""

from __future__ import annotations

from datetime import date, datetime

from fno.forecast_v4_rules.series import SessionRv, live_intraday_rv
from fno.intraday.candle_rv_table import CandleRvTable
from fno.intraday.rv_table import RvTable
from fno.intraday.wiring import INTRADAY_FOLDER

CANDLE_METHOD = "rv-candle-15m-v1"


def candle_rows() -> list[SessionRv]:
    rows = [r for r in CandleRvTable(INTRADAY_FOLDER).rows() if r["method"] == CANDLE_METHOD]
    out = [SessionRv(date.fromisoformat(r["session"]), float(r["rv_session"]) if r["status"] == "ok" else None,
                     datetime.fromisoformat(r["first_seen_at"])) for r in rows]  # fmt: skip
    return sorted(out, key=lambda s: s.day)


def live_rows() -> list[SessionRv]:
    return live_intraday_rv(RvTable(INTRADAY_FOLDER).rows())


def oct(day: int) -> date:
    return date(2026, 10, day)
