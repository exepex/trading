"""Law 3's margin room (story 3.3; orchestrator, 22 Oct 2026, story section 6 item 7, revised): C2's `MarginRoom`,
failing closed, wherever every position of the check (the proposal and each held one: C2 sums them all) has a sourced
row in C2's margins file; otherwise the law refuses (`margin_room`) with the note `MARGIN_NOT_CHECKED` and no number,
and never invents a margin (design 6.1a: no usable margin, no new entry; the fix is margin data, a separate piece).
The margins file has no index column: its rows are NIFTY's, so a position on another index never uses them. A stale
row is a row, and a missing or malformed file is no usable data either: C2 runs and refuses both."""

import csv
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from ...risk.margins import MARGIN_COLUMNS
from ..constants import RefusalReason, RoadCode
from ..contracts.decisions import LegSpec, Proposal
from ..contracts.roads import ROADS_BY_CODE
from ..contracts.safety import AccountView, LawResult
from ..contracts.snapshot import SlotSnapshot
from .c2_inputs import structure_width
from .c2_laws import C2Law

MARGIN_NOT_CHECKED = "margin not checked: no data"
MARGIN_ROWS_INDEX = "NIFTY"  # the only index C2's margins file holds rows for


def margin_not_checked(result: LawResult) -> bool:
    """True for a margin-room refusal for want of a margin row (reports show its note)."""
    return result.law == MarginRoomLaw.name and result.note == MARGIN_NOT_CHECKED


class MarginRows:
    """The (structure, width) pairs C2's margins file holds a sourced row for, at any date."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def held(self) -> set[tuple[str, float]] | None:
        """None when the file is missing or not C2's layout: then C2 itself runs and refuses (fail closed)."""
        if not self.path.exists():
            return None
        with open(self.path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) != MARGIN_COLUMNS:
                return None
            return {(r["structure"], float(r["width"])) for r in reader if r["source"].strip()}


class MarginRoomLaw:
    name = "margin_room"

    def __init__(self, checked: C2Law, rows: MarginRows):
        self.checked, self.rows = checked, rows

    def check(self, proposal: Proposal, account: AccountView, snapshot: SlotSnapshot, session: date) -> LawResult:
        held = self.rows.held()
        positions = [(snapshot.road, proposal.structure, proposal.legs)]
        positions += [(p.road, p.structure, p.legs) for p in account.open_positions]
        if held is not None and not all(_has_row(held, road, structure, legs) for road, structure, legs in positions):
            return LawResult(self.name, False, RefusalReason.MARGIN_ROOM, note=MARGIN_NOT_CHECKED)
        return self.checked.check(proposal, account, snapshot, session)


def _has_row(held: set[tuple[str, float]], road: RoadCode, structure: str, legs: Iterable[LegSpec]) -> bool:
    return ROADS_BY_CODE[road].underlying == MARGIN_ROWS_INDEX and (structure, structure_width(legs)) in held
