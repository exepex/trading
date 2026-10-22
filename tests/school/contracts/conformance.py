"""Conformance checks every real school class must pass, as the fakes do (story MS-P1a, criterion 8). Each later
part's tests call the check for its port with its own real object and inputs; a check only uses the contract."""

from datetime import date, datetime, timedelta

import pytest

from fno.constants import SIDE_BUY
from fno.school.constants import SCHOOL_OFF_LINE, ExitState, Outcome, RecordKind, RefusalReason
from fno.school.contracts.accounts import (
    AccountPort,
    FillPort,
    IndexSettlementSource,
    LedgerEntry,
    LedgerReader,
    SealedDecision,
    SettlementPrice,  # fmt: skip
    SettlementUnavailable,
)
from fno.school.contracts.clock import Clock
from fno.school.contracts.dashcam import DashcamStore, ReplayConflict
from fno.school.contracts.decisions import Decision, Driver, OpenPosition, Proposal
from fno.school.contracts.fleet import FleetRunner, RunMode
from fno.school.contracts.reports import Banner, ReportSection, SectionText
from fno.school.contracts.roads import ROADS, RoadCatalogue, RoadDay
from fno.school.contracts.safety import AccountView, LawResult, SafetyLaw
from fno.school.contracts.seal import Seal
from fno.school.contracts.slot_file import SlotRecord
from fno.school.contracts.snapshot import SlotSnapshot, SnapshotSource, SnapshotUnavailable


def check_road_catalogue(catalogue, trading_day: date, closed_day: date) -> None:
    """All five roads on a trading day (each open, or closed with its one reason); none on a closed day."""
    assert isinstance(catalogue, RoadCatalogue)
    days = catalogue.day(trading_day)
    assert sorted(d.road.code for d in days) == sorted(r.code for r in ROADS)
    assert all(isinstance(d, RoadDay) and d.session == trading_day for d in days)
    for day in (d for d in days if d.status.open):  # MS-P1a2: every recorded expiry has its own step
        assert set(day.strike_steps) == set(day.expiries) and all(day.step_for(e) > 0 for e in day.expiries)
    assert catalogue.day(closed_day) == ()


def check_snapshot_source(source, open_day: RoadDay, closed_day: RoadDay) -> None:
    assert isinstance(source, SnapshotSource)
    found = source.for_road(open_day)
    assert isinstance(found, SlotSnapshot) and (found.road, found.session) == (open_day.road.code, open_day.session)
    with pytest.raises(SnapshotUnavailable) as raised:
        source.for_road(closed_day)
    assert raised.value.reason == closed_day.status.closed_by


def check_driver(driver, road_day: RoadDay, snapshot: SlotSnapshot, position: OpenPosition) -> None:
    assert isinstance(driver, Driver)
    decision = driver.decide(road_day, snapshot, (), ())
    assert isinstance(decision, Decision)
    assert (decision.driver_id, decision.road, decision.session) == (
        driver.card.driver_id, road_day.road.code, road_day.session)  # fmt: skip
    driver.review_exit(position, snapshot, ())  # an ExitReason or None; the type is checked by the caller's test


def check_safety_law(law, passing: tuple[Proposal, AccountView], refusing: tuple[Proposal, AccountView],
                     snapshot: SlotSnapshot) -> None:  # fmt: skip
    """`passing` and `refusing` are (proposal, account) pairs, so laws on the account (daily stop, brake) fit too."""
    assert isinstance(law, SafetyLaw)
    for (proposal, account), expected in ((passing, True), (refusing, False)):
        result = law.check(proposal, account, snapshot, snapshot.session)
        assert isinstance(result, LawResult) and result.law == law.name and result.passed is expected
    assert law.check(*refusing, snapshot, snapshot.session) == law.check(*refusing, snapshot, snapshot.session)


def check_account_port(port, entry: LedgerEntry, marks: dict, session: date) -> None:
    """`entry` opens a position: recording it shows it open; recording it again changes nothing."""
    assert isinstance(port, AccountPort)
    driver_id = entry.position.driver_id
    before = port.view(driver_id, marks, session)
    assert isinstance(before, AccountView) and before.driver_id == driver_id and not before.open_positions
    port.record(driver_id, entry)
    after = port.view(driver_id, marks, session)
    assert [p.position_id for p in after.open_positions] == [entry.position.position_id]
    port.record(driver_id, entry)
    assert port.view(driver_id, marks, session) == after, "the same entry again is a no-op"


def check_fill_port(port, sealed: SealedDecision, snapshot: SlotSnapshot, seal: Seal, at: datetime) -> None:
    """`seal` covers `sealed` at `at`, and every leg of the proposal has a two-sided quote in `snapshot`."""
    assert isinstance(port, FillPort)
    late = Seal(seal.path, seal.sha256, at + timedelta(seconds=1), seal.commit)
    other = Seal(seal.path, "00" * 32, seal.pushed_at, seal.commit)
    for bad in (late, other):
        refused = port.enter(sealed, snapshot, bad, at)
        assert not refused.filled and RefusalReason.STALE_SEAL in refused.refused
    filled = port.enter(sealed, snapshot, seal, at)
    proposal = sealed.decision.proposal
    assert filled.filled and filled.rests_on == sealed.file_sha256 and filled.filled_at == at
    assert len(filled.legs) == len(proposal.legs), "every leg fills, or none"
    for leg, fill in zip(proposal.legs, filled.legs, strict=True):
        quote = snapshot.quote(leg.key)
        assert fill.price == (quote.ask if leg.side == SIDE_BUY else quote.bid), "fills at the touch"
        assert fill.units == leg.lots * proposal.lot


def check_fill_port_missing_quote(port, sealed: SealedDecision, empty: SlotSnapshot, seal: Seal, at: datetime,
                                  position: OpenPosition) -> None:  # fmt: skip
    """With no quote for any leg: the entry is refused and the exit waits; neither invents a price."""
    entry = port.enter(sealed, empty, seal, at)
    assert not entry.filled and RefusalReason.MISSING_QUOTE in entry.refused
    exit_ = port.exit(position, empty, sealed.file_sha256, seal, at)
    assert not exit_.filled and exit_.state == ExitState.EXIT_WAITING_QUOTE


def check_dashcam(store, session: date, slot: str, records: tuple[SlotRecord, ...],
                  other: tuple[SlotRecord, ...]) -> None:  # fmt: skip
    assert isinstance(store, DashcamStore)
    assert store.find(session, slot, RecordKind.DECISIONS) is None, "nothing sealed yet"
    first = store.seal(session, slot, RecordKind.DECISIONS, records)
    assert store.find(session, slot, RecordKind.DECISIONS) == first
    assert store.find(session, slot, RecordKind.OUTCOMES) is None
    assert store.seal(session, slot, RecordKind.DECISIONS, records) == first, "the same records again change nothing"
    with pytest.raises(ReplayConflict):
        store.seal(session, slot, RecordKind.DECISIONS, other)
    assert store.read(first) == records
    outcomes = store.seal(session, slot, RecordKind.OUTCOMES, other)
    assert outcomes.sha256 != first.sha256 and store.read(outcomes) == other, "each kind is its own file"


def check_report_section(section, session: date) -> None:
    assert isinstance(section, ReportSection)
    text = section.render(session)
    assert isinstance(text, SectionText) and text.banner in set(Banner)


def check_clock(clock) -> None:
    assert isinstance(clock, Clock)
    assert clock.now().tzinfo is not None


def check_settlement_source(source, known: tuple[str, date], unknown: tuple[str, date]) -> None:
    assert isinstance(source, IndexSettlementSource)
    price = source.price(*known)
    assert isinstance(price, SettlementPrice) and price.price > 0 and price.file_sha256
    with pytest.raises(SettlementUnavailable):
        source.price(*unknown)


def check_fleet(runner, session: date, scheduled: set[tuple], mode: RunMode = RunMode.REPLAY) -> None:
    """`scheduled`: every (road code, driver id) of the session. One sealed decision each, sealed before any fill,
    every entry resting on that seal; a second run seals nothing new."""
    assert isinstance(runner, FleetRunner)
    run = runner.run(session, mode)
    keys = [(r.road, r.decision.driver_id) for r in run.decisions]
    assert run.status == "" and len(keys) == len(set(keys)) and set(keys) == scheduled
    assert run.decisions_seal is not None and all(r.session == session for r in run.decisions)
    trades = sum(r.decision.outcome == Outcome.TRADE for r in run.decisions)
    assert len(run.fills) == trades
    seal = run.decisions_seal
    for fill in (f for f in run.fills if f.filled):
        assert fill.rests_on == seal.sha256 and fill.filled_at >= seal.pushed_at, "sealed before any fill"
    again = runner.run(session, mode)
    assert again.decisions == run.decisions and again.decisions_seal == run.decisions_seal and again.fills == ()


def check_fleet_off(runner, session: date) -> None:
    run = runner.run(session, RunMode.RECORD)
    assert run.status == SCHOOL_OFF_LINE and run.decisions == () and run.fills == ()


def check_ledger_reader(reader, port, opening: LedgerEntry, closing: LedgerEntry, marks: dict, session: date) -> None:
    """MS-P1a3: `reader` reads `port`'s accounts. Never-opened gives (); then the opening, then both in order; reading
    changes nothing and writes no equity row (a view before and after a read is equal)."""
    assert isinstance(reader, LedgerReader)
    driver_id = opening.position.driver_id
    assert reader.entries(driver_id) == ()
    port.view(driver_id, marks, session)
    port.record(driver_id, opening)
    assert reader.entries(driver_id) == (opening,)
    port.record(driver_id, closing)
    before = port.view(driver_id, marks, session)
    assert reader.entries(driver_id) == (opening, closing) == reader.entries(driver_id)
    assert port.view(driver_id, marks, session) == before, "a read writes nothing"
