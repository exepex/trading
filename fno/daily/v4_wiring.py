"""Composition root of protocol v4's daily pieces in O1's run (story G10 completion; apart from `wiring.py`, at its
size): the `v4` quote part (A4e's 14:30-14:40 window) beside the 3 pm parts, `v4_release` once that part has ended (by
14:45, `V4_RELEASE_BY`; a part still running then is stopped) and `v4_deadline` from 15:12. The capture part is gated
by `daily.live_from.v4_pack` and the two steps by `daily.live_from.v4_release` (STAB1, owner 25 Oct 2026: forecasting
off, captures never stop; the release forecasts nothing but makes the pack's record, so it goes off with them while
the capture keeps running); in a rehearsal each key's note reaches its own part or steps."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date

from ..alerts.sender import AlertSender
from ..constants import V4_DEADLINE_STEP, V4_RELEASE_STEP
from ..desk.daily_ports import DayStep, Waiter
from ..quotes.window import V4_WINDOW, named_window
from ..storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER
from ..v4_pack.deadline import CHECK_FROM
from ..v4_pack.paths import DAYS_FOLDER, DEADLINES_FOLDER, PACKS_FOLDER
from ..v4_pack.release_run import V4_RELEASE_BY
from .quote_parts import QUOTE_PARTS, QuotePart, QuoteParts
from .quote_steps import AfterPart
from .steps import Alerted, LiveFrom, NotBefore
from .v4_part import V4_PART, v4_part

RELEASE, DEADLINE = ("v4-pack", "release"), ("v4-pack", "deadline")
V4_STEPS = (V4_RELEASE_STEP, V4_DEADLINE_STEP)


def receipts(*folders: str) -> tuple[str, ...]:
    return tuple(f"{RECEIPTS_FOLDER}/{DATA_AREA}/{folder}/" for folder in folders)


def day_parts(cfg: dict) -> tuple[QuotePart, ...]:
    """A4's 3 pm parts and protocol v4's `v4` part, its times from A4e's window in `config.yaml`."""
    return (*QUOTE_PARTS, v4_part(named_window(cfg, V4_WINDOW)))


def part_notes(parts: Sequence[QuotePart], notes: Mapping[str, str]) -> dict[tuple[str, ...], str]:
    """Each part's rehearsal note, by its command, from its live key's note (none outside a rehearsal)."""
    return {part.arguments: notes[part.live_key] for part in parts if part.live_key in notes}


def step_notes(notes: Mapping[str, str]) -> dict[str, str]:
    """The steps' notes with `v4_release`'s note given to both of its steps (they share that one live key)."""
    shared = {name: notes[V4_RELEASE_STEP] for name in V4_STEPS if V4_RELEASE_STEP in notes}
    return {**notes, **shared}


def v4_steps(
    command: Callable[[Callable[[date], tuple[str, ...]], tuple[str, ...]], DayStep],
    parts: QuoteParts,
    waiter: Waiter,
    live_from: date | None,
    alerts: AlertSender,
) -> dict[str, DayStep]:
    """`command(arguments, pathspecs)`: the run's command step committing only those receipts."""
    release = AfterPart(command(lambda day: RELEASE, receipts(DAYS_FOLDER, PACKS_FOLDER)), parts, V4_PART,
                        V4_RELEASE_BY, waiter)  # fmt: skip
    deadline = NotBefore(command(lambda day: DEADLINE, receipts(DEADLINES_FOLDER)), CHECK_FROM, waiter)
    return {
        V4_RELEASE_STEP: Alerted(V4_RELEASE_STEP, LiveFrom(release, live_from), alerts),
        V4_DEADLINE_STEP: Alerted(V4_DEADLINE_STEP, LiveFrom(deadline, live_from), alerts),
    }
