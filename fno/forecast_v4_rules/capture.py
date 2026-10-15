"""One session's v4 phase-1 forecasts (story G7): every baseline and rule forecaster for V6a, V6b and V1, from inputs
first seen before the day's 15:00 IST cutoff. Used live (`LiveCapture`) and by the back-fill."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, time

from ..constants import (
    V1_RV_1S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_EWMA,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_HAR_INTRADAY,
    V4_BASELINE_TRAILING,
    V4_RULE_V1_CLOSE_BLEND,
    V4_RULE_V6_EWMA_T4,
    V6_BIG_MOVE_1S,
    V6_BIG_MOVE_5S,
)
from ..models import IST
from .baselines import NOT_ELIGIBLE, NOT_STARTED, BaseRate, Ewma, Har, Value, before, trailing_previous_session
from .records import BASELINE, LIVE, RULE, SLOT_REPORTED, SLOT_RULES, Record, record
from .rules import v1_close_blend, v6_ewma_t4
from .series import DayValue, SessionRv, big_move_outcomes, close_proxy_rv

CUTOFF = time(15, 0)
V1_START_SESSIONS, HAR_INTRADAY_SESSIONS = 20, 250  # live non-void A16 sessions (protocol 1.3 and 3.1)
FORECASTERS = {  # (forecaster, question) -> (kind, slot); decision 70: V6's rules slot is M1's
    (V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S): (BASELINE, SLOT_REPORTED),
    (V4_BASELINE_BASE_RATE, V6_BIG_MOVE_5S): (BASELINE, SLOT_REPORTED),
    (V4_RULE_V6_EWMA_T4, V6_BIG_MOVE_1S): (RULE, SLOT_REPORTED),
    (V4_RULE_V6_EWMA_T4, V6_BIG_MOVE_5S): (RULE, SLOT_REPORTED),
    (V4_BASELINE_TRAILING, V1_RV_1S): (BASELINE, SLOT_REPORTED),
    (V4_BASELINE_EWMA, V1_RV_1S): (BASELINE, SLOT_REPORTED),
    (V4_BASELINE_HAR_DAILY, V1_RV_1S): (BASELINE, SLOT_REPORTED),
    (V4_BASELINE_HAR_INTRADAY, V1_RV_1S): (BASELINE, SLOT_REPORTED),
    (V4_RULE_V1_CLOSE_BLEND, V1_RV_1S): (RULE, SLOT_RULES),
}


def cutoff(d: date) -> datetime:
    return datetime.combine(d, CUTOFF, IST)


@dataclass(frozen=True)
class Inputs:
    closes: list[DayValue]  # regular-session NIFTY closes
    closes_lines: list[str]  # the closes file's regular rows as text, same order (for the inputs hash)
    intraday: list[SessionRv]  # A16's live rows
    sessions: list[date]  # scored sessions (A7 regular), including any day to forecast
    method_sha256: str


class DayForecasts:
    def __init__(self, inputs: Inputs):
        self.inputs = inputs
        self.days = [c.day for c in inputs.closes]
        rv = close_proxy_rv(inputs.closes)
        self.ewma = Ewma(rv)
        self.har_daily = Har(rv, 1, inputs.sessions)
        self.base_rates = {q: BaseRate(big_move_outcomes(inputs.closes, h)) for q, h in
                           ((V6_BIG_MOVE_1S, 1), (V6_BIG_MOVE_5S, 5))}  # fmt: skip
        self._prefix = _prefix_hashes(inputs.closes_lines)

    def values(self, d: date) -> dict[tuple[str, str], Value]:
        ewma = self.ewma.forecast(d, 1)
        p1, p5 = v6_ewma_t4(ewma)
        out = {
            (V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S): self.base_rates[V6_BIG_MOVE_1S].forecast(d),
            (V4_BASELINE_BASE_RATE, V6_BIG_MOVE_5S): self.base_rates[V6_BIG_MOVE_5S].forecast(d),
            (V4_RULE_V6_EWMA_T4, V6_BIG_MOVE_1S): p1,
            (V4_RULE_V6_EWMA_T4, V6_BIG_MOVE_5S): p5,
        }
        return out | self._v1(d, ewma)

    def _v1(self, d: date, ewma: Value) -> dict[tuple[str, str], Value]:
        seen = [r for r in self.inputs.intraday if r.day < d and r.first_seen_at < cutoff(d)]
        usable = [DayValue(r.day, r.value) for r in seen if r.value is not None]
        if len(usable) < V1_START_SESSIONS:
            return {(f, q): Value(NOT_STARTED) for f, q in FORECASTERS if q == V1_RV_1S}
        har_daily = self.har_daily.forecast(d)
        intraday = Value(NOT_ELIGIBLE)
        if len(usable) >= HAR_INTRADAY_SESSIONS:
            intraday = Har(usable, 1, self.inputs.sessions, minimum=1).forecast(d)
        previous = self.inputs.sessions[before(self.inputs.sessions, d) - 1]
        return {
            (V4_BASELINE_TRAILING, V1_RV_1S): trailing_previous_session(seen, previous),
            (V4_BASELINE_EWMA, V1_RV_1S): ewma,
            (V4_BASELINE_HAR_DAILY, V1_RV_1S): har_daily,
            (V4_BASELINE_HAR_INTRADAY, V1_RV_1S): intraday,
            (V4_RULE_V1_CLOSE_BLEND, V1_RV_1S): v1_close_blend(har_daily, ewma),
        }

    def records(self, d: date, label: str, made_at: str) -> dict[tuple[str, str], Record]:
        inputs_sha = self._inputs_sha(d)
        audit = dict(label=label, method_sha256=self.inputs.method_sha256, inputs_sha256=inputs_sha, made_at=made_at)
        out = {}
        for key, value in self.values(d).items():
            kind, slot = FORECASTERS[key]
            out[key] = record(d, key[1], value.status, value.value, kind=kind, slot=slot, **audit)
        return out

    def _inputs_sha(self, d: date) -> str:
        """SHA-256 of the closes rows before `d` and A16's rows seen before `d`'s cutoff."""
        digest = hashlib.sha256(self._prefix[before(self.days, d)].encode())
        for r in self.inputs.intraday:
            if r.day < d and r.first_seen_at < cutoff(d):
                digest.update(f"{r.day},{r.value},{r.first_seen_at.isoformat()}\n".encode())
        return digest.hexdigest()


def _prefix_hashes(lines: list[str]) -> list[str]:
    """prefix[i] = SHA-256 of the first i lines."""
    digest, out = hashlib.sha256(), [hashlib.sha256().hexdigest()]
    for line in lines:
        digest.update((line + "\n").encode())
        out.append(digest.hexdigest())
    return out


class CaptureRefused(RuntimeError):
    """Not before the day's cutoff, or not a scored session: nothing written."""


def capture_day(forecasts: DayForecasts, d: date, now: datetime, write) -> int:
    """Today's live rows, only before 15:00 IST (as G3); `write(forecaster, question, rows)` stores them."""
    if d not in forecasts.inputs.sessions:
        raise CaptureRefused(f"{d} is not a scored session")
    if now >= cutoff(d):
        raise CaptureRefused(f"{now:%Y-%m-%d %H:%M} IST is at or after {d}'s 15:00 cutoff")
    rows = forecasts.records(d, LIVE, now.isoformat())
    return sum(write(f, q, [row]) for (f, q), row in rows.items())
