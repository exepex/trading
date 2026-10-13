"""Corporate actions from NSE's own list (story P6; judge 42): past prices and volumes are put on today's share basis
before any figure that compares the day with an earlier one (1W to 1Y changes, 52-week high and low, volume average,
RSI). Raw NSE closes jump at a split or bonus (KOTAKBANK's 5:1 split on 14 Jan 2026: 2,132.60 to 421.00).

- A split or consolidation ("Face Value Split ... From Rs 5/- Per Share To Re 1/- Per Share") divides earlier prices
  by old face value / new face value; a bonus a:b (a new shares for b held) by (a + b) / b. Earlier volumes are
  multiplied by the same factor.
- A demerger, scheme of arrangement, amalgamation or capital reduction has no ratio in NSE's list, so no adjustment can
  be computed from NSE's files: only the sessions from its ex-date on are used (figures needing older closes are null).
- Dividends, buy-backs, interest, distributions and rights issues change no price here (price returns, not total
  returns; rights adjustments are small and NSE's list gives no adjustment factor).
Only actions with an ex-date on or before the session are applied (never one announced for later)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import date, datetime

from ..fo_bhavcopy import BadFile
from .nse_files import EquityBar

FACE_VALUE = re.compile(r"From\s+R[es]+\.?\s*([\d.]+)\s*/-.*?To\s+R[es]+\.?\s*([\d.]+)\s*/-", re.IGNORECASE)
BONUS = re.compile(r"Bonus\s+(\d+)\s*:\s*(\d+)", re.IGNORECASE)
HISTORY_BREAKS = ("demerger", "arrangement", "amalgamation", "capital reduction")
EX_DATE_FORMAT = "%d-%b-%Y"
PRICE_DECIMALS = 2


@dataclass(frozen=True)
class CorporateAction:
    symbol: str
    ex_date: date
    subject: str
    factor: float | None  # earlier prices are divided by it (None: no price change)
    breaks_history: bool  # no ratio can be computed: earlier sessions are not used


def classify(subject: str) -> tuple[float | None, bool]:
    """(price factor, breaks history) of an action's description in NSE's list."""
    text = subject.lower()
    if any(word in text for word in HISTORY_BREAKS):
        return None, True
    factor = 1.0
    for old, new in FACE_VALUE.findall(subject):
        factor *= float(old) / float(new)
    for new_shares, held in BONUS.findall(subject):
        factor *= (int(new_shares) + int(held)) / int(held)
    return (factor if factor != 1.0 else None), False


def read_corporate_actions(data: bytes, filename: str) -> list[CorporateAction]:
    """Every action in NSE's corporate-actions list (JSON from its website), classified."""
    try:
        records = json.loads(data.decode("utf-8"))
        return [_action(r) for r in records if r.get("exDate") not in (None, "-")]
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise BadFile(f"{filename}: not NSE's corporate-actions list ({exc})") from exc


def _action(record: dict) -> CorporateAction:
    ex_date = datetime.strptime(record["exDate"], EX_DATE_FORMAT).date()
    return CorporateAction(record["symbol"], ex_date, record["subject"], *classify(record["subject"]))


def adjusted(bars: list[EquityBar], actions: list[CorporateAction]) -> list[EquityBar]:
    """A symbol's bars on its latest share basis, using the actions with an ex-date up to its last bar."""
    last = bars[-1].day
    for action in sorted(actions, key=lambda a: a.ex_date):
        if action.ex_date > last or action.ex_date <= bars[0].day:
            continue
        if action.breaks_history:
            bars = [b for b in bars if b.day >= action.ex_date]
        elif action.factor:
            bars = [_rebased(b, action.factor) if b.day < action.ex_date else b for b in bars]
    return bars


def _rebased(bar: EquityBar, factor: float) -> EquityBar:
    return replace(
        bar,
        close=round(bar.close / factor, PRICE_DECIMALS),
        high=round(bar.high / factor, PRICE_DECIMALS),
        low=round(bar.low / factor, PRICE_DECIMALS),
        volume=round(bar.volume * factor),
    )
