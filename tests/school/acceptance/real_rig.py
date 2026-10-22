"""`real_rig(scenario)` (story MS-P1j for MS-P1i's harness): the real fleet over the real parts.
- b's catalogue, reader and quality gate, on captures written as the recorder writes them;
- the scenario's drivers, as plans: they are the scenario's input, not the code under test;
- d's whole law set, with a fixed stressed margin in place of MS-P1m's Drive read;
- d's accounts and fills, and f's ticket book on its own ledger;
- c's real dashcam on a local Drive folder and a local git remote;
- j's counts files.

The scenario's times hold on the real git: the run's commits are dated at the scenario's `seal_pushed_at` (git's own
`GIT_COMMITTER_DATE`, set only while the fleet runs), so the real seal carries that time and the fill clock is the
scenario's `fill_at`. The stale-seal fault is then a fill before the real receipt's commit, exactly what it means."""

import csv
import os
from dataclasses import replace
from datetime import date

from fno.config import ROOT, load_config
from fno.school.accounts.school_accounts import SchoolAccounts
from fno.school.constants import SLOT_1500, RoadCode
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.roads import ROADS, ROADS_BY_CODE
from fno.school.dashcam.names import counts_path
from fno.school.execution.school_fills import SchoolFills
from fno.school.fakes import FakeDriver, FakeSettlementSource
from fno.school.fleet.books import Books
from fno.school.fleet.counts_file import SessionCounts, opportunity_path
from fno.school.fleet.entry_mids import DashcamEntryMids
from fno.school.fleet.report_inputs import SealedDayInputs
from fno.school.fleet.runner import SchoolFleet
from fno.school.quality.gate import RoadQualityGate
from fno.school.roads.capture import CaptureReader
from fno.school.roads.catalogue import RecordedRoadCatalogue
from fno.school.roads.snapshots import RecordedSnapshotSource
from fno.school.safety.wiring import build_safety_laws
from fno.school.settings import school_settings
from fno.school.tickets.book import TicketBook, TicketLedger
from tests.school.acceptance.rig import Rig, ScenarioExpiries, ScenarioLots, write_captures
from tests.school.dashcam import harness as cam
from tests.school.roads.capture_builder import CALENDAR, DictStore, FixtureListing
from tests.school.safety.law_builders import FixedMargin

CFG = load_config(ROOT / "config.yaml")
ALL_ROADS = tuple(road.code for road in ROADS)


class DatedFleet:
    """The fleet, its git commits dated at the scenario's seal time while it runs."""

    def __init__(self, fleet, scenario):
        self.fleet, self.scenario = fleet, scenario

    def run(self, session, mode):
        when = self.scenario.seal_pushed_at.isoformat()
        saved = {name: os.environ.get(name) for name in GIT_DATES}
        os.environ.update(dict.fromkeys(GIT_DATES, when))
        try:
            return self.fleet.run(session, mode)
        finally:
            for name, value in saved.items():
                os.environ.pop(name) if value is None else os.environ.__setitem__(name, value)


GIT_DATES = ("GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE")


class NoReviews:
    def lifts(self, driver_id, before):
        return ()


def real_rig(scenario, tmp_path) -> Rig:
    store = DictStore()
    write_captures(store, scenario)
    reader = CaptureReader({road.dataset: store for road in ROADS})
    catalogue = RecordedRoadCatalogue(CALENDAR, reader, ScenarioExpiries(scenario.listed_expiries),
                                      ScenarioLots(scenario.lots))  # fmt: skip
    listing = FixtureListing(keys=frozenset(k for snap in scenario.snapshots.values() for k in snap.quotes))
    block = {**CFG["school"], "enabled": True, "max_loss_rs": int(scenario.cap_rs)}
    settings = school_settings({"school": block})
    accounts = SchoolAccounts(
        tmp_path / "accounts", settings.account_rs, settings.brake_rs, CFG["charges"], NoReviews()
    )
    tickets = SchoolAccounts(tmp_path / "tickets", settings.account_rs, settings.brake_rs, CFG["charges"], NoReviews())
    fills = SchoolFills(CFG["charges"], FakeSettlementSource())
    books = Books(accounts, accounts, TicketBook(fills, TicketLedger(tickets)), tickets, fills)
    (tmp_path / "dashcam").mkdir(parents=True)
    dashcam = cam.build(tmp_path / "dashcam").store
    counts_root = tmp_path / "counts"
    drivers = tuple(FakeDriver(replace(plan.card, roads=ALL_ROADS), plan.proposal) for plan in scenario.drivers)
    margin = FixedMargin()
    fleet = SchoolFleet(
        settings, catalogue, RecordedSnapshotSource(reader), RoadQualityGate(listing), NoHistory(), drivers,
        lambda marks: build_safety_laws(CFG, settings, marks, margin), books, dashcam,
        SessionCounts(counts_root, None), lambda session: None, DashcamEntryMids(dashcam),
        FixedClock(scenario.fill_at),
    )  # fmt: skip
    day = SealedDayInputs(dashcam, counts_root, {d.card.driver_id: d.card.role for d in drivers})

    def ledger():
        return tuple(e for d in drivers for e in accounts.entries(d.card.driver_id))

    def decisions(session: date) -> tuple[DecisionRecord, ...]:
        return tuple(r for r in day.records(session) if isinstance(r, DecisionRecord))

    def count_file(session: date) -> bytes:
        files = (counts_root / counts_path(session, SLOT_1500), counts_root / opportunity_path(session, SLOT_1500))
        return b"".join(f.read_bytes() for f in files if f.is_file())

    def denominator(session: date):
        file = counts_root / opportunity_path(session, SLOT_1500)
        rows = csv.DictReader(file.open()) if file.is_file() else []
        return frozenset((RoadCode(r["road"]), r["driver"]) for r in rows)

    def snapshot_for(code):
        return reader.read(ROADS_BY_CODE[code], scenario.session).snapshot()

    def section_inputs(session: date, which: str):
        return decisions(session)

    fleet = DatedFleet(fleet, scenario)
    return Rig(scenario, fleet, dashcam, ledger, snapshot_for, count_file, section_inputs, denominator)


class NoHistory:
    def spots(self, road, session):
        return ()


def real_rig_builder(tmp_path):
    """The harness's `build(scenario)`: each call a fresh world in its own folder (the comparator builds two)."""
    worlds = iter(range(1_000))

    def build(scenario) -> Rig:
        return real_rig(scenario, tmp_path / f"world{next(worlds)}")

    return build
