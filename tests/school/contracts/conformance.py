"""Conformance checks every real school class must pass, as the fakes do (story MS-P1a, criterion 8). Each later
part's tests call the check for its port with its own real object and inputs; a check only uses the contract."""

from datetime import date

import pytest

from fno.school.constants import RefusalReason
from fno.school.contracts.accounts import AccountPort, FillPort, FillResult
from fno.school.contracts.dashcam import DashcamStore, ReplayConflict, Seal
from fno.school.contracts.decisions import Decision, Driver, Proposal
from fno.school.contracts.reports import Banner, ReportSection, SectionText
from fno.school.contracts.roads import ROADS, RoadCatalogue, RoadDay
from fno.school.contracts.safety import AccountView, LawResult, SafetyLaw
from fno.school.contracts.snapshot import SlotSnapshot, SnapshotSource, SnapshotUnavailable


def check_road_catalogue(catalogue, trading_day: date, closed_day: date) -> None:
    assert isinstance(catalogue, RoadCatalogue)
    days = catalogue.day(trading_day)
    codes = [d.road.code for d in days]
    assert days and len(codes) == len(set(codes)) and set(codes) <= {r.code for r in ROADS}
    assert all(isinstance(d, RoadDay) and d.session == trading_day for d in days)
    assert catalogue.day(closed_day) == ()


def check_snapshot_source(source, open_day: RoadDay, closed_day: RoadDay) -> None:
    assert isinstance(source, SnapshotSource)
    found = source.for_road(open_day)
    assert isinstance(found, SlotSnapshot) and (found.road, found.session) == (open_day.road.code, open_day.session)
    with pytest.raises(SnapshotUnavailable) as raised:
        source.for_road(closed_day)
    assert raised.value.reason == closed_day.status.closed_by


def check_driver(driver, road_day: RoadDay, snapshot: SlotSnapshot) -> None:
    assert isinstance(driver, Driver)
    decision = driver.decide(road_day, snapshot, (), ())
    assert isinstance(decision, Decision)
    assert (decision.driver_id, decision.road, decision.session) == (
        driver.card.driver_id, road_day.road.code, road_day.session)  # fmt: skip


def check_safety_law(law, passing: Proposal, failing: Proposal, account: AccountView, snapshot: SlotSnapshot) -> None:
    assert isinstance(law, SafetyLaw)
    ok = law.check(passing, account, snapshot, snapshot.session)
    refused = law.check(failing, account, snapshot, snapshot.session)
    assert isinstance(ok, LawResult) and ok.passed and ok.law == law.name
    assert isinstance(refused, LawResult) and not refused.passed and isinstance(refused.reason, RefusalReason)


def check_account_port(port, driver_id: str, snapshot: SlotSnapshot) -> None:
    assert isinstance(port, AccountPort)
    before = port.view(driver_id, snapshot)
    assert isinstance(before, AccountView) and before.driver_id == driver_id
    port.record(driver_id, FillResult(refused=(RefusalReason.MISSING_QUOTE,)))
    assert port.view(driver_id, snapshot) == before, "a refusal records nothing"


def check_fill_port(port, decision: Decision, snapshot: SlotSnapshot, good: Seal, stale: Seal) -> None:
    assert isinstance(port, FillPort)
    refused = port.enter(decision, snapshot, stale)
    assert not refused.filled and RefusalReason.STALE_SEAL in refused.refused
    filled = port.enter(decision, snapshot, good)
    assert filled.filled and filled.seal_sha256 == good.sha256
    assert len(filled.legs) == len(decision.proposal.legs), "every leg fills, or none"


def check_dashcam(store, session: date, slot: str) -> None:
    assert isinstance(store, DashcamStore)
    first = store.seal(session, slot, b'{"a":1}')
    assert store.seal(session, slot, b'{"a":1}').sha256 == first.sha256, "the same bytes again change nothing"
    with pytest.raises(ReplayConflict):
        store.seal(session, slot, b'{"a":2}')
    assert store.read(first) == b'{"a":1}'


def check_report_section(section, session: date) -> None:
    assert isinstance(section, ReportSection)
    text = section.render(session)
    assert isinstance(text, SectionText) and text.banner in set(Banner)
