"""Criterion 8 (story MS-P1a): every fake passes the conformance check its real class must pass."""

from datetime import date, timedelta

import pytest

from fno.school.constants import ClosureReason, ExitReason, ExitState, RoadCode
from fno.school.contracts.accounts import LedgerEntry, SettlementPrice
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.roads import ROADS, RoadStatus
from fno.school.fakes import (
    FakeAccounts,
    FakeDashcam,
    FakeDriver,
    FakeFills,
    FakeMaxLossLaw,
    FakeRoadCatalogue,
    FakeSection,
    FakeSettlementSource,
    FakeSnapshotSource,
)
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.contracts.test_records import outcome_record, trade_record

CLOSED = RoadStatus(ClosureReason.HASH_MISMATCH)
AT = b.SLOT_AT + timedelta(minutes=4)
MARKS = {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}
CLOSING = LedgerEntry(b.position(), b.filled(), closes=True, exit_reason=ExitReason.PROFIT_TARGET)


def test_road_catalogue():
    days = tuple(b.road_day(road.code) for road in ROADS)
    c.check_road_catalogue(FakeRoadCatalogue({b.SESSION: days}), b.SESSION, b.SESSION + timedelta(days=5))


def test_snapshot_source():
    source = FakeSnapshotSource({(RoadCode.BANKNIFTY_MONTHLY, b.SESSION): b.snapshot()})
    c.check_snapshot_source(source, b.road_day(), b.road_day(status=CLOSED))


def test_driver_with_and_without_a_proposal():
    c.check_driver(FakeDriver(b.card(), b.put_spread(), ExitReason.PROFIT_TARGET), b.road_day(), b.snapshot(),
                   b.position())  # fmt: skip
    c.check_driver(FakeDriver(b.card()), b.road_day(), b.snapshot(), b.position())


def test_safety_law():
    account = b.account()
    c.check_safety_law(FakeMaxLossLaw(10_000), (b.put_spread(10_000), account), (b.put_spread(10_001), account),
                       b.snapshot())  # fmt: skip


def test_account_port():
    c.check_account_port(FakeAccounts(2_000_000), b.opening(), {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}, b.SESSION)


def test_fill_port():
    c.check_fill_port(FakeFills(), b.sealed(), b.snapshot(), b.seal(), AT)
    c.check_fill_port_missing_quote(FakeFills(), b.sealed(), b.snapshot(quotes={}), b.seal(), AT, b.position())


def test_settlement_at_intrinsic_or_needed():
    source = FakeSettlementSource({("BANKNIFTY", b.EXPIRY): SettlementPrice(950.0, "ee" * 32)})
    settled = FakeFills(source).settle(b.position(), b.EXPIRY)
    assert [leg.price for leg in settled.legs] == [50.0, 0.0] and settled.rests_on == "ee" * 32
    assert FakeFills().settle(b.position(), b.EXPIRY).state == ExitState.SETTLEMENT_NEEDED
    assert FakeFills(source).settle(b.position(), date(2026, 12, 29)).state == ExitState.SETTLEMENT_NEEDED


def test_dashcam():
    c.check_dashcam(FakeDashcam(), b.SESSION, "15:00", (trade_record(),), (outcome_record(),))


def test_report_section():
    c.check_report_section(FakeSection(), b.SESSION)


def test_clock():
    c.check_clock(FixedClock(b.SLOT_AT))


def test_settlement_source():
    source = FakeSettlementSource({("BANKNIFTY", b.EXPIRY): SettlementPrice(950.0, "ee" * 32)})
    c.check_settlement_source(source, ("BANKNIFTY", b.EXPIRY), ("NIFTY", b.EXPIRY))


def test_ledger_reader():
    accounts = FakeAccounts(2_000_000)
    c.check_ledger_reader(accounts, accounts, b.opening(), CLOSING, MARKS, b.SESSION)


class EveryEntry:
    """A bad reader: everything ever recorded, whatever has been recorded yet (it reads ahead of the ledger)."""

    def entries(self, driver_id):
        return (b.opening(), CLOSING)


class NeverAny(FakeAccounts):
    def entries(self, driver_id):
        return ()


class PhantomWhenEmpty(FakeAccounts):
    """Wrong only before anything is recorded: it shows an entry for an account never opened."""

    def entries(self, driver_id):
        return super().entries(driver_id) or (b.opening(),)


class LateByOne(FakeAccounts):
    """Wrong only after the opening: it shows nothing until the position is also closed."""

    def entries(self, driver_id):
        found = super().entries(driver_id)
        return found if len(found) != 1 else ()


class Reversed(FakeAccounts):
    def entries(self, driver_id):
        return tuple(reversed(super().entries(driver_id)))


BAD = {"never": NeverAny, "reversed": Reversed, "phantom": PhantomWhenEmpty, "late": LateByOne}


@pytest.mark.parametrize("bad", ["ahead", *BAD])
def test_the_ledger_reader_check_refuses_a_wrong_reader(bad):
    port = FakeAccounts(2_000_000) if bad == "ahead" else BAD[bad](2_000_000)
    reader = EveryEntry() if bad == "ahead" else port
    with pytest.raises(AssertionError):
        c.check_ledger_reader(reader, port, b.opening(), CLOSING, MARKS, b.SESSION)
