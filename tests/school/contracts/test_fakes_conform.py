"""Criterion 8 (story MS-P1a): every fake passes the conformance check its real class must pass."""

from datetime import timedelta

from fno.school.constants import ClosureReason, Outcome
from fno.school.contracts.decisions import Decision
from fno.school.contracts.roads import RoadStatus
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeDriver,
    FakeFills,
    FakeMaxLossLaw,
    FakeRoadCatalogue,
    FakeSection,  # fmt: skip
    FakeSnapshotSource,
)
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

CLOSED = RoadStatus(ClosureReason.HASH_MISMATCH)


def test_road_catalogue():
    c.check_road_catalogue(FakeRoadCatalogue({b.SESSION: (b.road_day(),)}), b.SESSION, b.SESSION + timedelta(days=5))


def test_snapshot_source():
    source = FakeSnapshotSource({(b.road_day().road.code, b.SESSION): b.snapshot()})
    c.check_snapshot_source(source, b.road_day(), b.road_day(status=CLOSED))


def test_driver_with_and_without_a_proposal():
    c.check_driver(FakeDriver(b.card(), b.put_spread()), b.road_day(), b.snapshot())
    c.check_driver(FakeDriver(b.card()), b.road_day(), b.snapshot())


def test_safety_law():
    c.check_safety_law(FakeMaxLossLaw(10_000), b.put_spread(10_000), b.put_spread(10_001), b.account(), b.snapshot())


def test_account_port():
    c.check_account_port(FakeAccounts(2_000_000), "CS1@1", b.snapshot())


def test_fill_port():
    decision = Decision("CS1@1", b.road_day().road.code, b.SESSION, Outcome.TRADE, "", b.put_spread())
    fill_time = b.SLOT_AT + timedelta(minutes=4)
    late = b.seal(pushed_at=fill_time + timedelta(seconds=1))
    c.check_fill_port(FakeFills(fill_time), decision, b.snapshot(), b.seal(), late)


def test_dashcam():
    c.check_dashcam(FakeDashcam(), b.SESSION, "15:00")


def test_report_section():
    c.check_report_section(FakeSection(), b.SESSION)
