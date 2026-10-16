"""The live daily record (section 7), run by O1's `price_distribution` step after the card. One file per underlying
per day; the command never alerts itself: O1's `Alerted` sends the one alert for a failed or refused step.

- not live (no `daily.live_from.price_distribution`, before it, or not today): `nothing written: ...`, exit 0;
- a closed day: `not a trading day`, exit 0;
- a day already in Drive: never rebuilt (its `made_at` would change the bytes); the same bytes are put again, which
  restores a missing receipt, and the line says `already recorded`;
- no chain for any underlying: `nothing written: ...`, exit 0 (O1 records `refused`, one alert);
- any other problem: every file still written (a missing chain as a `missing` record), last line `written with
  problems: ...`, exit 1 (O1 records `failed`, one alert, and commits the receipts)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date, datetime

from ..constants import SESSION_REGULAR, SESSION_SPECIAL
from ..research_data.calendar import SessionCalendar
from .build import DayBuilder, missing_record
from .chain import ChainSource
from .constants import LIVE
from .folders import live_path
from .records import Stamp, encode
from .sources import ChainUnavailable
from .store import DistributionStore

NOT_LIVE = "nothing written: not live on {day} (config.yaml daily.live_from.price_distribution: {live_from})"
NOT_TODAY = "nothing written: {day} is not today ({today}); past days go through `pricedist backfill`"
NOT_TRADING = "not a trading day"
NO_CHAIN = "no canonical 3 pm chain"
NOTHING = "nothing written: no 3 pm chain for any underlying ({reasons})"
ALREADY = "{underlying}: already recorded"
RECORDED = "{underlying}: recorded ({problems} problems)"
WITH_PROBLEMS = "written with problems: {problems}"
DONE = "recorded"
RECORDED_KINDS = (SESSION_REGULAR, SESSION_SPECIAL)


class LiveRecorder:
    def __init__(self, source: ChainSource, builder: DayBuilder, store: DistributionStore, calendar: SessionCalendar,
                 underlyings: Sequence[str], live_from: date | None, now: Callable[[], datetime]):  # fmt: skip
        self.source, self.builder, self.store, self.calendar = source, builder, store, calendar
        self.underlyings, self.live_from, self.now = tuple(underlyings), live_from, now

    def record(self, day: date) -> tuple[int, list[str]]:
        now = self.now()
        if self.live_from is None or day < self.live_from:
            return 0, [NOT_LIVE.format(day=day, live_from=self.live_from)]
        if day != now.date():
            return 0, [NOT_TODAY.format(day=day, today=now.date())]
        if self.calendar.session_kind(day) not in RECORDED_KINDS:
            return 0, [NOT_TRADING]
        lines, built, gaps, problems = [], {}, {}, []
        for underlying in self.underlyings:
            path = live_path(underlying, day)
            existing = self.store.get(path)
            if existing is not None:
                self.store.put(path, existing)
                lines.append(ALREADY.format(underlying=underlying))
                built[underlying] = None
                continue
            try:
                chain = self.source.chain(underlying, day)
            except ChainUnavailable as error:
                chain, gaps[underlying] = None, str(error)
            if chain is None:
                gaps.setdefault(underlying, NO_CHAIN)
                continue
            built[underlying] = self.builder.build(chain, LIVE, now.isoformat())
        if not built:
            return 0, [NOTHING.format(reasons="; ".join(f"{u}: {r}" for u, r in gaps.items()))]
        for underlying, record in built.items():
            if record is not None:
                self.store.put(live_path(underlying, day), encode(record))
                lines.append(RECORDED.format(underlying=underlying, problems=len(record["problems"])))
                problems += [f"{underlying} {p}" for p in record["problems"]]
        stamp = Stamp(LIVE, self.builder.method, "", now.isoformat())
        for underlying, reason in gaps.items():
            self.store.put(live_path(underlying, day), encode(missing_record(underlying, day, reason, stamp)))
            problems.append(f"{underlying} {reason}")
        return (1, [*lines, WITH_PROBLEMS.format(problems="; ".join(problems))]) if problems else (0, [*lines, DONE])
