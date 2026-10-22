"""What the harness needs of a fleet and its stores (story MS-P1i). `fake_rig` builds it from a's fakes; story j writes
`real_rig(scenario)` over the real wiring and runs the same checks (`tests/school/acceptance/harness.py`)."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from fno.school.acceptance.scenario import Scenario
from fno.school.constants import SLOT_1500, RecordKind, RoadCode
from fno.school.contracts.accounts import LedgerEntry
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.dashcam import DashcamStore
from fno.school.contracts.fleet import FleetRunner
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.snapshot import SlotSnapshot
from fno.school.fake_fleet import FakeFleet
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeDriver,
    FakeFills,
    FakeMaxLossLaw,
    FakeRoadCatalogue,
    FakeSnapshotSource,
)

Key = tuple[RoadCode, str]  # (road, driver id): one scheduled road decision


@dataclass(frozen=True)
class Rig:
    """A fleet with the views the checks read. A real rig supplies the same five readers over its stores."""

    scenario: Scenario
    fleet: FleetRunner
    dashcam: DashcamStore
    ledger: Callable[[], tuple[LedgerEntry, ...]]  # every entry of every driver account
    snapshot_for: Callable[[RoadCode], SlotSnapshot]  # the snapshot the fleet decided on, per road
    count_file: Callable[[date], bytes]  # the session's public counts file
    section_inputs: Callable[
        [date, str], tuple[DecisionRecord, ...]
    ]  # records a section renders from; "today"/"evening"
    denominator: Callable[[date], frozenset[Key]]  # every (road, driver) the counts are over

    def sealed_decisions(self, session: date) -> tuple[DecisionRecord, ...]:
        return sealed_decisions(self.dashcam, session)


def sealed_decisions(dashcam: DashcamStore, session: date) -> tuple[DecisionRecord, ...]:
    seal = dashcam.find(session, SLOT_1500, RecordKind.DECISIONS)
    return () if seal is None else tuple(r for r in dashcam.read(seal) if isinstance(r, DecisionRecord))


def fake_count_file(records: tuple[DecisionRecord, ...], entries: tuple[LedgerEntry, ...]) -> bytes:
    """Per (road, driver): the sealed outcome and reason, and whether an account entry opened. Canonical JSON."""
    opened = {(e.position.road, e.position.driver_id) for e in entries if not e.closes}
    rows = [
        {"road": r.road, "driver": r.decision.driver_id, "outcome": r.decision.outcome, "reason": r.decision.reason,
         "executed": int((r.road, r.decision.driver_id) in opened)}
        for r in records
    ]  # fmt: skip
    rows.sort(key=lambda row: (row["road"], row["driver"]))
    return json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()


def fake_rig(scenario: Scenario) -> Rig:
    accounts, dashcam = FakeAccounts(2_000_000), FakeDashcam(pushed_at=scenario.seal_pushed_at)
    fleet = FakeFleet(
        True,
        FakeRoadCatalogue({scenario.session: scenario.road_days}),
        FakeSnapshotSource({(code, scenario.session): snap for code, snap in scenario.snapshots.items()}),
        tuple(FakeDriver(plan.card, plan.proposal) for plan in scenario.drivers),
        (FakeMaxLossLaw(scenario.cap_rs),),
        accounts,
        FakeFills(),
        dashcam,
        FixedClock(scenario.fill_at),
    )  # fmt: skip

    def ledger() -> tuple[LedgerEntry, ...]:
        return tuple(entry for entries in accounts.ledgers.values() for entry in entries)

    def sealed(session: date) -> tuple[DecisionRecord, ...]:
        return sealed_decisions(dashcam, session)

    # The fakes' readers: both sections and the counts read the one sealed decisions file.
    return Rig(
        scenario, fleet, dashcam, ledger, lambda code: scenario.snapshots[code],
        lambda session: fake_count_file(sealed(session), ledger()),
        lambda session, which: sealed(session),
        lambda session: frozenset((r.road, r.decision.driver_id) for r in sealed(session)),
    )  # fmt: skip
