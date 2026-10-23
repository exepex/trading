"""A model-priced put spread with its entry decision, for the evidence tests (story MS-INS, part c)."""

from dataclasses import replace
from datetime import date

from fno.constants import SIDE_BUY, SIDE_SELL
from fno.school.constants import SLOT_1500, ExitReason, Outcome, RoadCode
from fno.school.contracts.decisions import Decision, LegSpec, Proposal
from fno.school.contracts.records import DecisionRecord
from fno.school.instructor.contracts import HeldPath
from tests.school.instructor.attribution.fixtures import LONG, SHORT, model_snapshot, path
from tests.school.instructor.builders import ROAD

ENTRY_DAY, EXIT_DAY = date(2026, 11, 2), date(2026, 11, 4)
MAX_LOSS = 3000.0
SPREAD = Proposal("PCS", (LegSpec(SHORT, SIDE_SELL, 1), LegSpec(LONG, SIDE_BUY, 1)), 30, 500.0, MAX_LOSS, 80.0, 1.0)


def entry_record(day: date = ENTRY_DAY) -> DecisionRecord:
    shot = model_snapshot(day, 1000.0, 0.20)
    decision = Decision("CS1@1", ROAD, day, Outcome.TRADE, "", SPREAD)
    return DecisionRecord(day, SLOT_1500, ROAD, "aa" * 32, shot.snapshot_id, shot.sha256, None, decision)


def spread_path(exit_forward: float = 980.0, exit_sigma: float = 0.22, settlement: float | None = None,
                reason: ExitReason = ExitReason.PROFIT_TARGET) -> HeldPath:  # fmt: skip
    shots = (model_snapshot(ENTRY_DAY, 1000.0, 0.20),)
    if settlement is None:
        shots += (model_snapshot(EXIT_DAY, exit_forward, exit_sigma),)
    held = path(shots, settlement=settlement)
    outcome = held.outcome if settlement is not None else replace(held.outcome, exit_reason=reason)
    return replace(held, outcome=outcome, entry=entry_record())


def market_snapshots(moves: dict[RoadCode, float]) -> dict:
    """Each monthly road at F = 1000 on entry and F = 1000 x (1 + move) on exit, sigma 0.20."""
    shots = {}
    for road, move in moves.items():
        for day, forward in ((ENTRY_DAY, 1000.0), (EXIT_DAY, 1000.0 * (1 + move))):
            shots[(road, day)] = replace(model_snapshot(day, forward, 0.20), road=road)
    return shots
