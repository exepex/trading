"""Story O1-desk-freeze (owner's cut-list, 22 Oct 2026): `config.yaml` `desk.frozen: true` freezes the paper desk's
daily steps until the edge study shows a trade with an edge after costs. While any book holds an open position, what
it needs still runs (`OPEN_POSITION_STEPS`; judge 469, the default until the owner answers): a freeze never leaves a
trade unclosed, unmarked or outside its loss rules."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date
from pathlib import Path

from ..books.account import PaperAccount
from ..books.equity import trade_positions
from ..constants import DESK_FROZEN_STEPS, OPEN_POSITION_STEPS

NOT_A_SWITCH = "config.yaml desk.frozen must be true or false, not {value!r}"


def desk_frozen(cfg: dict) -> bool:
    """The owner's one switch; absent means the desk runs."""
    value = (cfg.get("desk") or {}).get("frozen", False)
    if not isinstance(value, bool):
        raise ValueError(NOT_A_SWITCH.format(value=value))
    return value


def open_trades(root: Path, accounts: Iterable[str]) -> int:
    """Open trades across the accounts, read from their downloaded files (read-only: no lock, no Drive write)."""
    return sum(t.is_open for a in accounts for t in trade_positions(PaperAccount(root, a).fills()).values())


class DeskFreeze:
    """The desk steps frozen today: none when the switch is off; every desk step when it is on, but those an open
    position needs while one is open."""

    def __init__(self, frozen: bool, open_positions: Callable[[], int]):
        self.on, self.open_positions = frozen, open_positions

    def __call__(self, day: date) -> frozenset[str]:
        if not self.on:
            return frozenset()
        held = set(OPEN_POSITION_STEPS) if self.open_positions() else set()
        return frozenset(DESK_FROZEN_STEPS) - held
