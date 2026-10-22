"""The driver brake's state (story 3.3 law 7; owner, 22 Oct 2026, "Pause till monthly review"), from the account's
equity rows (one per session, at that slot's marks before its fills) and the monthly review rows that lift it.

- The high is the highest fully marked equity since the account opened, or since the brake was last lifted.
- The brake engages on the first fully marked session whose equity is `brake_rs` or more below that high, and holds
  across sessions whatever equity does next.
- A review row dated on or after the engagement and before a session lifts it from that session; the high restarts
  at the next fully marked equity (until then, the latest row's). A review row with no brake engaged changes nothing.
- A session with an unmarked position (counted at its worst case) neither sets the high nor engages the brake: one
  missing quote never pauses a driver for a month. Its own decision is still checked against its own equity."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EquityRow:
    session: date
    equity: float
    fully_marked: bool


@dataclass(frozen=True)
class BrakeState:
    high: float
    engaged_on: date | None
    lifted_on: date | None


def brake_state(rows: Sequence[EquityRow], lifts: Sequence[date], brake_rs: float) -> BrakeState:
    high: float | None = None
    engaged: date | None = None
    lifted: date | None = None
    rows = sorted(rows, key=lambda r: r.session)
    for row in rows:
        lifting = [day for day in lifts if engaged is not None and engaged <= day < row.session]
        if lifting:
            engaged, lifted, high = None, max(lifting), None  # the high restarts at the next fully marked row
        if not row.fully_marked:
            continue
        high = row.equity if high is None else max(high, row.equity)
        if engaged is None and high - row.equity >= brake_rs:
            engaged = row.session
    if not rows:
        raise ValueError("the brake needs at least the account's opening row")
    return BrakeState(rows[-1].equity if high is None else high, engaged, lifted)
