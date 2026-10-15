"""The whole measurement (PROTOCOL.md sections 8 and 11-14): every entry observed at each R, then the cells. The main
width (200; LC and LP at 0) gives every figure; widths 100 and 300 only the 15:00, R = 60 cells (sensitivity)."""

from __future__ import annotations

from collections.abc import Sequence

from .cells import CellKey, flip_shares, main_cell, paired
from .entries import SENSITIVITY_WIDTHS, Entry, main_width, widths
from .observe import Observation, Observer
from .times import DECISION_14, DECISION_15, DECISIONS, REACTIONS

LATE_REACTION = 60  # the flip share, the paired difference and the width sensitivity are read at R = 60


def registered_keys(families: Sequence[str]) -> list[CellKey]:
    keys = []
    for family in families:
        keys += [CellKey(family, main_width(family), at, r) for at in DECISIONS for r in REACTIONS]
        keys += [CellKey(family, w, DECISION_15, LATE_REACTION) for w in SENSITIVITY_WIDTHS if w in widths(family)]
    return keys


def observe_all(entries: Sequence[Entry], observer: Observer, keys: Sequence[CellKey]) -> list[Observation]:
    wanted = set(keys)
    return [observer.observe(e, r) for e in entries for r in REACTIONS
            if CellKey(e.family, e.width, e.decision.at, r) in wanted]  # fmt: skip


def analyse(observations: Sequence[Observation], families: Sequence[str], eligible: dict, lot: int) -> dict:
    """`eligible`: decision time -> days eligible for it (section 4, after the index-missing days)."""
    keys = registered_keys(families)
    rows = {k: [] for k in keys}
    for o in observations:
        rows[CellKey(o.family, o.width, o.decision, o.reaction)].append(o)
    cells = {k: main_cell(k, rows[k], eligible[k.decision], lot) for k in keys}
    out = {"cells": [cells[k] for k in keys], "paired": [], "flips": []}
    for family in families:
        late, early = (CellKey(family, main_width(family), at, LATE_REACTION) for at in (DECISION_15, DECISION_14))
        out["paired"].append(paired(cells[late], cells[early], rows[late], rows[early], family))
        out["flips"] += [flip_shares(cells[k], rows[k]) for k in (late, early)]
    return out
