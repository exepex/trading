"""Story MS-P1j (the SIM builder's finding, orchestrator's ruling, 23 Oct 2026): every account store the fleet records
into is opened by the session's view before any fill, the ticket ledger as the driver account, so a driver's
first-ever ticket on a fresh ledger records and the session completes, session after session. On d's real stores."""

from fno.config import ROOT, load_config
from fno.school.constants import SLOT_1500, Outcome, RecordKind
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode
from fno.school.execution.school_fills import SchoolFills
from fno.school.fakes import FakeDriver, FakeMaxLossLaw, FakeSettlementSource
from fno.school.fleet_wiring import FleetStores, books_on
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig, all_roads

CFG = load_config(ROOT / "config.yaml")


def real_rig(tmp_path) -> Rig:
    """The fleet rig over d's `SchoolAccounts` for the driver accounts and the ticket ledger (a fresh home), filled by
    d's `SchoolFills` at the repository's charges, which d's store checks every fill against."""
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), (FakeMaxLossLaw(10_000),), max_new=0)
    home = tmp_path / "home"
    rig.fleet.books = books_on(CFG, FleetStores(home, None, None, None, FixedClock(b.SLOT_AT)),
                               SchoolFills(CFG["charges"], FakeSettlementSource()))  # fmt: skip
    return rig


def ticket_entries(rig: Rig, driver_id: str = "CS1@1"):
    return rig.fleet.books.ticket_entries.entries(driver_id)


def test_a_drivers_first_ever_ticket_on_a_fresh_ledger_records_and_the_session_completes(tmp_path):
    rig = real_rig(tmp_path)
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert run.status == "", run.status
    [mine] = [r for r in run.decisions if r.road == OPEN_ROAD]
    assert mine.decision.outcome == Outcome.TICKET and len(ticket_entries(rig)) == 1
    assert rig.dashcam.find(b.SESSION, SLOT_1500, RecordKind.OUTCOMES) is not None, "the session completed"
    assert rig.fleet.books.account_entries.entries("CS1@1") == (), "never in the driver's account"


def test_session_after_session_the_ledgers_stay_open_and_record(tmp_path):
    rig = real_rig(tmp_path)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.settings = type(rig.fleet.settings)(**{**vars(rig.fleet.settings), "max_new_trades_per_slot": 5})
    run = rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    assert run.status == "", run.status
    [mine] = [r for r in run.decisions if r.road == OPEN_ROAD]
    assert mine.decision.outcome == Outcome.TRADE and len(rig.fleet.books.account_entries.entries("CS1@1")) == 1
    assert len(ticket_entries(rig)) == 1, "the first session's ticket stays in its own ledger"
