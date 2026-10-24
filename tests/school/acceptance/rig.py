"""What the harness needs of a fleet and its stores (story MS-P1i). `fake_rig` builds it from a's fakes; story j writes
`real_rig(scenario)` over the real wiring and runs the same checks (`tests/school/acceptance/harness.py`)."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from functools import partial

from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.quotes.snapshot_rows import COLUMNS, snapshot_csv
from fno.school.acceptance.scenario import Scenario
from fno.school.constants import SLOT_1500, ClosureReason, RecordKind, RoadCode
from fno.school.contracts.accounts import LedgerEntry
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.dashcam import DashcamStore
from fno.school.contracts.fleet import FleetRunner
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.roads import ROADS, ROADS_BY_CODE, DatedLot, Road
from fno.school.contracts.snapshot import ContractKey, SlotQuote, SlotSnapshot, SnapshotSource, SnapshotUnavailable
from fno.school.fake_fleet import FakeFleet
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeDriver,
    FakeFills,
    FakeMaxLossLaw,
)
from fno.school.quality.gate import RoadQualityGate
from fno.school.roads.capture import CaptureReader
from fno.school.roads.catalogue import RecordedRoadCatalogue
from fno.school.roads.ports import LotProblem
from fno.school.roads.snapshots import RecordedSnapshotSource
from fno.storage.raw_store import RawFileStore
from tests.school.roads.capture_builder import CALENDAR, DictStore, FixtureListing

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


class ScenarioExpiries:
    """ExpirySource: what the scenario's archived listing says each road records."""

    def __init__(self, listed: dict):
        self.listed = listed

    def expected(self, road: Road, session: date):
        return tuple(self.listed[road.code])


class ScenarioLots:
    """LotSource: the scenario's dated lot copy; one lot for every expiry of the capture, or the problem."""

    def __init__(self, lots: dict):
        self.lots = lots

    def lot(self, underlying: str, session: date, expiries: tuple[date, ...]):
        road = next(r for r in ROADS if r.underlying == underlying and r.code in self.lots)
        units = {self.lots[road.code].get(expiry) for expiry in expiries}
        if None in units:
            return LotProblem(ClosureReason.LOT_UNAVAILABLE)
        return DatedLot(units.pop(), "scenario lot copy") if len(units) == 1 else LotProblem(ClosureReason.LOT_MISMATCH)


class GatedSnapshots:
    """What the real fleet does between the catalogue and the drivers: the quality gate judges the snapshot, and a
    road it closes gives `SnapshotUnavailable` with the one reason."""

    def __init__(self, source: SnapshotSource, gate: RoadQualityGate):
        self.source, self.gate = source, gate

    def for_road(self, road_day):
        snapshot = self.source.for_road(road_day)
        status = self.gate.check(road_day, snapshot)
        if not status.open:
            raise SnapshotUnavailable(status.closed_by, "closed by the quality gate")
        return snapshot


def write_captures(store: RawFileStore, scenario: Scenario) -> None:
    """The scenario's snapshots as the recorder writes them (sidecar, quote file, canonical marker), so that b's reader
    takes the data from where the real one does."""
    for code, snapshot in scenario.snapshots.items():
        road = ROADS_BY_CODE[code]
        rows = [_row(snapshot, key, quote) for key, quote in sorted(snapshot.quotes.items())]
        data = snapshot_csv(rows)
        meta = {
            "snapshot_id": snapshot.snapshot_id, "underlying": road.underlying, "provider": "groww",
            "started_at": snapshot.started_at.isoformat(), "finished_at": snapshot.finished_at.isoformat(),
            "expiries": [e.isoformat() for e in snapshot.expiries], "spot": snapshot.spot,
            "expected_contracts": len(rows), "recorded_contracts": len(rows), "failures": [], "complete": True,
            "in_window": True, "csv_sha256": hashlib.sha256(data).hexdigest(),
        }  # fmt: skip

        place = partial(QuoteSnapshotRecorder.path, scenario.session, dataset=road.dataset)
        store.put(place(f"{snapshot.snapshot_id}.csv"), data)
        store.put(place(f"{snapshot.snapshot_id}.meta.json"), json.dumps(meta, sort_keys=True).encode())
        store.put(place(f"{road.stem}_{scenario.session:%Y%m%d}.canonical"), snapshot.snapshot_id.encode())


def _row(snapshot: SlotSnapshot, key: ContractKey, quote: SlotQuote) -> dict:
    def cell(value) -> str:
        return "" if value is None else f"{value:g}"

    row = dict.fromkeys(COLUMNS, "")
    row.update(snapshot_id=snapshot.snapshot_id, expiry=key.expiry.isoformat(), strike=f"{key.strike:g}",
               type=key.kind.value, bid=cell(quote.bid), ask=cell(quote.ask), last=cell(quote.last),
               bid_qty=cell(quote.bid_qty), ask_qty=cell(quote.ask_qty), spot=f"{snapshot.spot:.2f}",
               valid="true" if quote.valid else "false", provider="groww")  # fmt: skip
    return row


def fake_rig(scenario: Scenario) -> Rig:
    """The fleet over b's real classes: captures written to a store, read back by the real reader, the real catalogue
    (expiry and lot checks against the scenario's listing and lot copy) and the real quality gate, with a's fakes for
    the drivers, laws, accounts, fills and dashcam."""
    store = DictStore()
    write_captures(store, scenario)
    reader = CaptureReader({road.dataset: store for road in ROADS})
    catalogue = RecordedRoadCatalogue(
        CALENDAR, reader, ScenarioExpiries(scenario.listed_expiries), ScenarioLots(scenario.lots)
    )
    listing = FixtureListing(keys=frozenset(k for snap in scenario.snapshots.values() for k in snap.quotes))
    snapshots = GatedSnapshots(RecordedSnapshotSource(reader), RoadQualityGate(listing))
    accounts, dashcam = FakeAccounts(2_000_000), FakeDashcam(pushed_at=scenario.seal_pushed_at)
    fleet = FakeFleet(
        True, catalogue, snapshots,
        tuple(FakeDriver(plan.card, plan.proposal) for plan in scenario.drivers),
        (FakeMaxLossLaw(scenario.cap_rs),), accounts, FakeFills(), dashcam, FixedClock(scenario.fill_at),
    )  # fmt: skip

    def ledger() -> tuple[LedgerEntry, ...]:
        return tuple(entry for entries in accounts.ledgers.values() for entry in entries)

    def sealed(session: date) -> tuple[DecisionRecord, ...]:
        return sealed_decisions(dashcam, session)

    # The fakes' readers: both sections and the counts read the one sealed decisions file.
    return Rig(
        scenario, fleet, dashcam, ledger, lambda code: reader.read(ROADS_BY_CODE[code], scenario.session).snapshot(),
        lambda session: fake_count_file(sealed(session), ledger()),
        lambda session, which: sealed(session),
        lambda session: frozenset((r.road, r.decision.driver_id) for r in sealed(session)),
    )  # fmt: skip
