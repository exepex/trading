"""F9's trades (protocol sections 3-6): for an event (or an ordinary control day) E, enter at the close of the
session before E, exit at E's close (E0) or the next session's close (E1), on the nearest monthly expiry with at
least 5 sessions after the exit, through EDGE1's frozen planned-exit path (every leg traded at entry, the
impossible-price rule, the cap at the dated lot, an untraded exit leg flagged `incomplete_exit`). Structures centre on
the expiry's future close at entry (passed as the position's "spot")."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from edge1study.lots import circular_lot
from edge1study.runner import WIDTHS_BY_INDEX
from edge1study.trade import T21, Trade, run_trade
from f1study.gate import implied

from fno.research_data.panel_reader import NiftyPanel, SessionClose
from fno.research_engine.cycle_costs import LOSS_CAP, CycleTerms
from fno.research_engine.cycles import Cycle
from fno.research_engine.structures import ShortCondor, ShortIronFly

from .rows import MonthlyDay

MIN_SESSIONS_LEFT, YEAR = 5, 252
EXITS = {"E0": 0, "E1": 1}  # sessions after the event day's session
STRUCTURES = ("FLY", "CONDOR")
NO_ROWS, NO_EXPIRY, NO_FORWARD, NO_IV = "no_rows", "no_expiry", "no_forward", "no_straddle"


@dataclass(frozen=True)
class Setup:
    index: str
    event: date
    entry: date
    exit: date
    expiry: date | None
    forward: float | None
    lot: int | None
    move_pct: float | None  # the expiry future's close-to-close move, entry to exit
    gap_pct: float | None  # entry close to the event session's open (the overnight gap)
    sigma_iv: float | None
    status: str  # "ok" or why no trade can be built


def _future(day: MonthlyDay | None, expiry: date):
    return next((f for f in day.futures if f.expiry == expiry), None) if day else None


def _expiry(entry: MonthlyDay, exit_day: date, sessions: Sequence[date]) -> date | None:
    for expiry in sorted({f.expiry for f in entry.futures if f.expiry > exit_day}):
        if sum(exit_day < d <= expiry for d in sessions) >= MIN_SESSIONS_LEFT:
            return expiry
    return None


def setup(index: str, event: date, exit_code: str, sessions: Sequence[date], rows: Mapping[date, MonthlyDay]) -> Setup:
    """`sessions`: regular and special sessions in order. E's session is the first on or after the event date."""
    first = next((i for i, d in enumerate(sessions) if d >= event), None)
    if first is None or first == 0 or first + EXITS[exit_code] >= len(sessions):
        return Setup(index, event, event, event, None, None, None, None, None, None, NO_ROWS)
    entry_day, event_session, exit_day = sessions[first - 1], sessions[first], sessions[first + EXITS[exit_code]]
    entry, at_event, out = rows.get(entry_day), rows.get(event_session), rows.get(exit_day)
    base = (index, event, entry_day, exit_day)
    if entry is None or out is None:
        return Setup(*base, None, None, None, None, None, None, NO_ROWS)
    expiry = _expiry(entry, exit_day, sessions)
    if expiry is None:
        return Setup(*base, None, None, None, None, None, None, NO_EXPIRY)
    start, end, opened = _future(entry, expiry), _future(out, expiry), _future(at_event, expiry)
    if start is None or start.close <= 0:
        return Setup(*base, expiry, None, None, None, None, None, NO_FORWARD)
    lot = entry.lots.get(expiry) if entry.source == "udiff" else circular_lot(index, expiry)
    move = None if end is None or end.close <= 0 else end.close / start.close - 1
    gap = None if opened is None or opened.open <= 0 else opened.open / start.close - 1
    n = sum(entry_day < d <= expiry for d in sessions)
    iv = implied([q for q in entry.options if q.expiry == expiry], expiry, start.close, n)
    status = "ok" if iv.status == "ok" else NO_IV
    return Setup(*base, expiry, start.close, lot, move, gap, iv.sigma_iv, status)


def run_setup(code: str, s: Setup, rows: Mapping[date, MonthlyDay], charges: Mapping[str, float], pad: float) -> Trade:
    entry, out = rows[s.entry], rows[s.exit]
    options = {s.entry: tuple(q for q in entry.options if q.expiry == s.expiry),
               s.exit: tuple(q for q in out.options if q.expiry == s.expiry)}  # fmt: skip
    panel = NiftyPanel((SessionClose(s.entry, "regular", s.forward, None),), options, {})
    structure = ShortIronFly() if code == "FLY" else ShortCondor(offset=s.sigma_iv * (1 / YEAR) ** 0.5)
    terms = CycleTerms(s.lot, dict(charges), pad, LOSS_CAP, WIDTHS_BY_INDEX[s.index])
    return run_trade(structure, panel, Cycle(s.expiry, s.entry, s.entry, s.exit), terms, T21, [s.entry, s.exit],
                     lambda _e: None, capped=True)  # fmt: skip


def trade_row(code: str, s: Setup, t: Trade | None, kind: str) -> dict:
    row = {"index": s.index, "event": s.event.isoformat(), "kind": kind, "entry": s.entry.isoformat(),
           "exit": s.exit.isoformat(), "move_pct": s.move_pct, "gap_pct": s.gap_pct, "structure": code}  # fmt: skip
    if t is None:
        return {**row, "status": s.status, "net": 0.0}
    return {**row, "status": t.status, "incomplete": t.incomplete_exit, "width": t.width, "lot": t.lot,
            "credit": t.credit, "gross": t.gross, "charges": t.charges, "pads": t.pads, "net": t.net}  # fmt: skip


def priced(code: str, setups: Sequence[Setup], rows_by_index, charges, pad: float, kinds: Mapping) -> list[dict]:
    out = []
    for s in setups:
        if s.status != "ok" or not s.lot:
            out.append(trade_row(code, s, None, kinds[s.event]))
            continue
        out.append(trade_row(code, s, run_setup(code, s, rows_by_index[s.index], charges, pad), kinds[s.event]))
    return out
