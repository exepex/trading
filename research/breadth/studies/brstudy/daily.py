"""From the panel to scored (u, t) pairs and the daily cross-sectional mean losses (story BR1a, items `universe`,
`target_t1`, `outcome_exclusion`, `baselines`).

- Outcome of (u, t): Y = 1 when |ln(S(t+1) / S(t))| is at least t's implied daily move. S(t+1) is the next session's
  spot (UDiFF rows), or the same near-month future's next close (legacy rows, `next_spot`). A missing next value gives
  no outcome.
- Outcome-side screen: a (u, t) whose strikes NSE replaced by t+1 (`sizing.adjusted`) is not scored, for every
  baseline alike. The flag reads t+1's file, so it never reaches a forecast.
- Universe: on day t, a name is scored when it had a traded ATM straddle on at least 48 of the last 60 sessions and has
  60 resolved outcomes (`sizing.forecasts`).
- Daily losses: for each baseline, the mean Brier over the day's scored names."""

import math
from collections import defaultdict

from .panel import LEGACY
from .sizing_tools import sizing

WINDOW, MIN_TRADED = 60, 48
BASELINES = ("market", "trail60", "cal60", "tilt")  # tilt: the planning case only, never a baseline


def next_value(a: dict, b: dict | None) -> float | None:
    if a["source"] == LEGACY:
        return float(a["next_spot"]) if a["next_spot"] else None
    return float(b["spot"]) if b else None


def outcomes(rows: dict, sessions: list[str]) -> dict:
    """day -> (y, |r| / m), or None on a contract-adjustment day."""
    out = {}
    for t, nxt in zip(sessions, sessions[1:], strict=False):
        a, b = rows.get(t), rows.get(nxt)
        if not (a and a["implied"]):
            continue
        if b and sizing.adjusted(a, b):
            out[t] = None
            continue
        later = next_value(a, b)
        if later:
            r = abs(math.log(later / float(a["spot"])))
            out[t] = (int(r >= float(a["implied"])), r / float(a["implied"]))
    return out


def traded_enough(rows: dict, sessions: list[str]) -> set[str]:
    """The days on which the name had a traded ATM straddle on at least 48 of the 60 sessions up to the day."""
    have = [bool(rows.get(d, {}).get("implied")) for d in sessions]
    ok, running = set(), 0
    for i, day in enumerate(sessions):
        running += have[i] - (have[i - WINDOW] if i >= WINDOW else 0)
        if i >= WINDOW - 1 and running >= MIN_TRADED:
            ok.add(day)
    return ok


def scored_pairs(table: dict) -> tuple[dict, dict]:
    """underlying -> day -> (y, {baseline: p}); and the excluded count per year."""
    sessions = sorted({d for rows in table.values() for d in rows})
    scored, excluded = {}, defaultdict(int)
    for u, rows in table.items():
        series = outcomes(rows, sessions)
        for day, value in series.items():
            excluded[day[:4]] += value is None
        eligible = traded_enough(rows, sessions)
        scored[u] = {d: v for d, v in sizing.forecasts(series).items() if d in eligible}
    return scored, dict(excluded)


def daily_losses(scored: dict) -> list[dict]:
    """One row per day: the number of names and each baseline's mean Brier."""
    sums = defaultdict(lambda: defaultdict(float))
    counts = defaultdict(int)
    for days in scored.values():
        for day, (y, p) in days.items():
            counts[day] += 1
            for b in BASELINES:
                sums[day][b] += (p[b] - y) ** 2
    return [{"day": d, "names": counts[d], **{b: sums[d][b] / counts[d] for b in BASELINES}} for d in sorted(counts)]
