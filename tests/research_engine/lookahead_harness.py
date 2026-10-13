"""Reusable look-ahead harness (story B1 criteria 1 and 4; story B7 reuses it for the live 15:00 features).

`assert_no_lookahead(feature, data, decision_day, context)` computes the feature, then changes every input available
after the cutoff and proves the value does not
move. The cutoff is the feature's `known_at(decision_day)` (or an explicit `cutoff`), but never later than the
decision day's close: a feature that declares a later availability is still tested at the close, so it cannot hide a
leak behind its own declaration (judge 26). Each input carries an availability time:
- panel rows (closes, options, futures): `available_at(day, session)`, the session's close (15:30 IST; the evening
  muhurat session at the end of its day). So a 15:00 cutoff also changes the decision day's own closing data;
- events: a scheduled event's date is known from `announced_on`, an unscheduled one only when it happens (its date);
  story A6's dates are days, so an announcement counts from the start of its day.
Changes are scaled values, removed values, untraded legs, extra strikes, moved and added events. The harness fails if
there was nothing after the cutoff to change (the test would prove nothing). Extra inputs (B7's 15:00 snapshots) plug
in as further perturbers.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Sequence
from datetime import date, datetime, time, timedelta
from random import Random

from fno.constants import SESSION_CLOSE_TIME
from fno.research_data.events import Event
from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose
from fno.research_engine.features import DecisionContext, Feature, ResearchData, available_at

Perturber = Callable[[ResearchData, datetime, Random], tuple[ResearchData, int]]


def _scaled(value: float | None, rng: Random) -> float | None:
    """Another value, never the same one: removed one time in five, else scaled by 0.5 to 1.5 (never 1)."""
    if value is None or rng.random() < 0.2:
        return None if value is not None else rng.uniform(10, 30000)
    return value * rng.choice([rng.uniform(0.5, 0.95), rng.uniform(1.05, 1.5)])


def _price(value: float, rng: Random) -> float:
    return _scaled(value, rng) or value * 2


def _shake_session(s: SessionClose, rng: Random) -> SessionClose:
    return s._replace(underlying=_scaled(s.underlying, rng), vix=_scaled(s.vix, rng))


def _shake_options(quotes: tuple[OptionQuote, ...], rng: Random) -> tuple[OptionQuote, ...]:
    changed = [
        q._replace(close=_price(q.close, rng), settle=_price(q.settle + 1, rng), volume=rng.choice([0, q.volume + 7]))
        for q in quotes
        if rng.random() > 0.1  # one leg in ten removed
    ]
    extra = [q._replace(strike=q.strike + 25, volume=rng.randint(1, 500)) for q in quotes if rng.random() < 0.2]
    return tuple(changed + extra)


def _shake_futures(quotes: tuple[FutureQuote, ...], rng: Random) -> tuple[FutureQuote, ...]:
    return tuple(q._replace(close=_price(q.close, rng), volume=rng.choice([0, q.volume + 3])) for q in quotes)


def perturb_panel(data: ResearchData, cutoff: datetime, rng: Random) -> tuple[ResearchData, int]:
    """Changes every panel value available after the cutoff; returns the new data and how many sessions changed."""
    panel = data.panel
    later = {s.day for s in panel.sessions if available_at(s.day, s.session) > cutoff}
    trial = rng.getrandbits(64)  # exactly one draw per call, so the perturbers after this one never depend on the panel

    def day_rng(day: date, table: str) -> Random:
        """Each day's changes come from its own stream: appending days (story A13) never changes another day's draws."""
        return Random(f"{trial}-{table}-{day}")

    sessions = tuple(_shake_session(s, day_rng(s.day, "close")) if s.day in later else s for s in panel.sessions)
    options = {d: _shake_options(q, day_rng(d, "options")) if d in later else q for d, q in panel.options.items()}
    futures = {d: _shake_futures(q, day_rng(d, "futures")) if d in later else q for d, q in panel.futures.items()}
    return dataclasses.replace(data, panel=NiftyPanel(sessions, options, futures)), len(later)


def known_from(event: Event) -> datetime:
    """When the event's own date became knowable: its announcement if scheduled, else the day it happened."""
    day = event.announced_on if event.scheduled and event.announced_on is not None else event.day
    return datetime.combine(day, time.min)


def _moved(event: Event, after: date, rng: Random) -> Event:
    floor = max(after, event.announced_on or after)
    return dataclasses.replace(event, day=floor + timedelta(days=rng.randint(1, 60)), description="moved by harness")


def _added(after: date, rng: Random) -> list[Event]:
    announced = after + timedelta(days=1)
    scheduled = [
        Event(announced + timedelta(days=rng.randint(1, 60)), "rbi_policy", True, announced, "added by harness")
        for _ in range(3)
    ]
    return scheduled + [Event(announced + timedelta(days=rng.randint(0, 60)), "budget", False, None, "added")]


def perturb_events(data: ResearchData, cutoff: datetime, rng: Random) -> tuple[ResearchData, int]:
    """Moves every event whose date was not knowable by the cutoff and adds events announced after it. The first
    announcement of a moved meeting (`revised_from`, `first_announced_on`) is not touched when it was known."""
    after = cutoff.date()
    events = [_moved(e, after, rng) if known_from(e) > cutoff else e for e in data.events]
    added = _added(after, rng)
    return dataclasses.replace(data, events=tuple(events + added)), len(added)


DEFAULT_PERTURBERS: tuple[Perturber, ...] = (perturb_panel, perturb_events)


def remove_panel_after(data: ResearchData, cutoff: datetime) -> tuple[ResearchData, int]:
    """The deterministic trial: every panel value available after the cutoff removed (no closes, no option or future
    rows), so a feature that reads any of them moves on every run, not only on a lucky random draw (judge 64 addendum
    3: a threshold feature wrongly declared live is caught every time)."""
    panel = data.panel
    later = {s.day for s in panel.sessions if available_at(s.day, s.session) > cutoff}
    sessions = tuple(s._replace(underlying=None, vix=None) if s.day in later else s for s in panel.sessions)
    options = {d: () if d in later else q for d, q in panel.options.items()}
    futures = {d: () if d in later else q for d, q in panel.futures.items()}
    return dataclasses.replace(data, panel=NiftyPanel(sessions, options, futures)), len(later)


def assert_no_lookahead(
    feature: Feature,
    data: ResearchData,
    decision_day: date,
    context: DecisionContext,
    *,
    cutoff: datetime | None = None,
    trials: int = 3,
    seed: int = 20261013,
    perturbers: Sequence[Perturber] = DEFAULT_PERTURBERS,
):
    """The feature's value, after proving that `trials` random changes of the data after the cutoff, and one removal of
    every panel value after it, leave it equal."""
    cutoff = min(cutoff or feature.known_at(decision_day), datetime.combine(decision_day, SESSION_CLOSE_TIME))
    expected = feature.value(data, decision_day, context)
    rng = Random(f"{seed}-{feature.name}-{decision_day}")
    for trial in range(trials):
        changed = data
        for perturb in perturbers:
            changed, count = perturb(changed, cutoff, rng)
            assert count > 0, f"{perturb.__name__}: nothing after {cutoff} to change, the test would prove nothing"
        _assert_unmoved(feature, changed, decision_day, context, expected, cutoff, f"trial {trial}")
    removed, count = remove_panel_after(data, cutoff)
    assert count > 0, f"remove_panel_after: nothing after {cutoff} to remove, the test would prove nothing"
    _assert_unmoved(feature, removed, decision_day, context, expected, cutoff, "every panel value after it removed")
    return expected


def _assert_unmoved(feature, changed, decision_day, context, expected, cutoff, how: str) -> None:
    got = feature.value(changed, decision_day, context)
    assert got == expected, (
        f"look-ahead: {feature.name} on {decision_day} moved from {expected!r} to {got!r} when data after "
        f"{cutoff} changed ({how})"
    )


def _shake_quote(q, rng: Random):
    return q.__class__(q.expiry, q.strike, q.kind, _scaled(q.bid, rng), _scaled(q.ask, rng), rng.random() < 0.5)


def perturb_snapshots(data: ResearchData, cutoff: datetime, rng: Random) -> tuple[ResearchData, int]:
    """Story B7: changes every 3 pm snapshot whose capture finished after the cutoff (a later day's, or the same day's
    when it finished late): quotes repriced or made invalid, spot and VIX changed."""
    later = {day for day, s in data.snapshots.items() if s.finished_at > cutoff}
    snapshots = {
        day: dataclasses.replace(
            s, spot=_scaled(s.spot, rng), vix=_scaled(s.vix, rng), quotes=tuple(_shake_quote(q, rng) for q in s.quotes)
        )
        if day in later
        else s
        for day, s in data.snapshots.items()
    }
    return dataclasses.replace(data, snapshots=snapshots), len(later)


LIVE_PERTURBERS: tuple[Perturber, ...] = (perturb_panel, perturb_events, perturb_snapshots)
