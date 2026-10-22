"""Criteria 1, 2 and 4 (story MS-P1a): frozen types, the counts' order, two banner colours, consistent decisions."""

import dataclasses
import inspect
from datetime import datetime, timedelta

import pytest

from fno.school import constants as k
from fno.school.contracts import (
    accounts,
    clock,
    decisions,
    fleet,
    records,
    reports,
    roads,
    safety,
    seal,
    snapshot,
    tickets,
)
from fno.school.contracts.accounts import FillResult
from fno.school.contracts.decisions import Decision, LegSpec, Proposal
from fno.school.contracts.reports import Banner
from fno.school.contracts.roads import RoadStatus
from fno.school.contracts.safety import LawResult
from fno.school.contracts.seal import Seal
from fno.school.contracts.tickets import OpportunityCounts
from tests.school.contracts import builders as b

MODULES = (accounts, clock, decisions, fleet, records, reports, roads, safety, seal, snapshot, tickets)
DATACLASSES = [obj for m in MODULES for _, obj in inspect.getmembers(m, inspect.isclass)
               if dataclasses.is_dataclass(obj) and obj.__module__ == m.__name__]  # fmt: skip


@pytest.mark.parametrize("cls", DATACLASSES, ids=lambda c: c.__name__)
def test_every_contract_type_is_frozen(cls):
    assert cls.__dataclass_params__.frozen


def test_a_contract_value_cannot_be_changed():
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.put_spread().max_loss = 1.0


@pytest.mark.parametrize("counts", [(3, 2, 1), (1, 1, 1), (0, 0, 0)])
def test_counts_in_order_are_accepted(counts):
    OpportunityCounts(b.SESSION, k.RoadCode.NIFTY_WEEKLY, "WS1@1", *counts)


@pytest.mark.parametrize("counts", [(1, 2, 0), (2, 1, 2), (0, 0, -1)])
def test_counts_out_of_order_are_refused(counts):
    with pytest.raises(ValueError):
        OpportunityCounts(b.SESSION, k.RoadCode.NIFTY_WEEKLY, "WS1@1", *counts)


def test_the_banner_has_red_and_amber_only():
    assert {banner.value for banner in Banner} == {"red", "amber"}


def test_no_valid_quotes_is_its_own_no_trade_reason():
    assert k.NoTradeReason.NO_VALID_QUOTES == "no_valid_quotes"
    assert k.NoTradeReason.NO_VALID_QUOTES != k.NoTradeReason.NO_STRUCTURE_UNDER_CAP
    Decision("X@1", k.RoadCode.NIFTY_MONTHLY, b.SESSION, k.Outcome.NO_TRADE, k.NoTradeReason.NO_VALID_QUOTES)


def test_every_outcome_has_its_reason_codes_and_codes_are_unique_across_families():
    assert set(k.REASONS_BY_OUTCOME) == set(k.Outcome)
    families = (k.TicketReason, k.NoTradeReason, k.ClosureReason, k.RefusalReason, k.UnavailableReason)
    assert k.TicketReason.ACCOUNT_LIMIT not in k.REASONS_BY_OUTCOME[k.Outcome.REFUSED]
    values = [member.value for family in families for member in family]
    assert len(values) == len(set(values))


@pytest.mark.parametrize("outcome, reason, proposal", [
    (k.Outcome.TRADE, "", b.put_spread()), (k.Outcome.TICKET, k.TicketReason.TRADE_LIMIT, b.put_spread()),
    (k.Outcome.REFUSED, k.RefusalReason.DAILY_STOP, b.put_spread()), (k.Outcome.NO_TRADE, k.NoTradeReason.N0, None),
    (k.Outcome.ROAD_CLOSED, k.ClosureReason.CAPTURE_MISSING, None),
    (k.Outcome.UNAVAILABLE, k.UnavailableReason.DRIVER_ERROR, None)])  # fmt: skip
def test_consistent_decisions_are_accepted(outcome, reason, proposal):
    Decision("X@1", k.RoadCode.NIFTY_MONTHLY, b.SESSION, outcome, reason, proposal)


@pytest.mark.parametrize("outcome, reason, proposal", [
    (k.Outcome.TRADE, "", None), (k.Outcome.TRADE, k.NoTradeReason.N0, b.put_spread()),
    (k.Outcome.NO_TRADE, "", None), (k.Outcome.NO_TRADE, k.NoTradeReason.N0, b.put_spread()),
    (k.Outcome.REFUSED, k.ClosureReason.LOT_MISMATCH, None), (k.Outcome.REFUSED, k.RefusalReason.BRAKE, None),
    (k.Outcome.TICKET, k.TicketReason.TRADE_LIMIT, None)])  # fmt: skip
def test_inconsistent_decisions_are_refused(outcome, reason, proposal):
    with pytest.raises(ValueError):
        Decision("X@1", k.RoadCode.NIFTY_MONTHLY, b.SESSION, outcome, reason, proposal)


def test_an_open_road_needs_its_lot_step_and_expiries():
    with pytest.raises(ValueError):
        dataclasses.replace(b.road_day(), lot=None)
    closed = b.road_day(status=RoadStatus(k.ClosureReason.LOT_MISMATCH))
    assert not closed.status.open and closed.lot is None


def test_legs_and_proposals_refuse_empty_or_wrong_values():
    with pytest.raises(ValueError):
        LegSpec(b.key(1000.0), "hold", 1)
    with pytest.raises(ValueError):
        LegSpec(b.key(1000.0), "buy", 0)
    with pytest.raises(ValueError):
        Proposal("PCS", (), 30, 0.0, 100.0, 10.0, 0.0)
    with pytest.raises(ValueError):
        dataclasses.replace(b.put_spread(), costs=b.put_spread().max_loss + 1)
    with pytest.raises(ValueError):
        dataclasses.replace(b.put_spread(), max_loss=0.0)


def test_a_law_result_names_a_reason_exactly_when_refused():
    LawResult("x", True, None)
    LawResult("x", False, k.RefusalReason.BRAKE)
    for passed, reason in ((True, k.RefusalReason.BRAKE), (False, None)):
        with pytest.raises(ValueError):
            LawResult("x", passed, reason)


def test_a_fill_result_is_filled_or_refused_never_both_or_neither():
    with pytest.raises(ValueError):
        FillResult()
    leg = accounts.FilledLeg(b.key(1000.0), "sell", 30, 10.0, 1.0)
    with pytest.raises(ValueError):
        FillResult((leg,), refused=(k.RefusalReason.MISSING_QUOTE,), filled_at=b.SLOT_AT, rests_on="x")
    with pytest.raises(ValueError):
        FillResult((leg,))  # no time and no file
    with pytest.raises(ValueError):
        FillResult((leg,), filled_at=b.SLOT_AT)  # no file it rests on
    with pytest.raises(ValueError):
        FillResult((leg,), filled_at=datetime(2026, 11, 2, 15, 4), rests_on="x")  # naive time
    with pytest.raises(ValueError):
        FillResult(refused=(k.RefusalReason.MISSING_QUOTE,), state=k.ExitState.EXIT_WAITING_QUOTE)
    assert FillResult(state=k.ExitState.EXIT_WAITING_QUOTE).filled is False


def test_a_fill_s_cash_is_premium_received_less_paid_and_charges():
    sell = accounts.FilledLeg(b.key(1000.0), "sell", 30, 10.0, 21.0)
    buy = accounts.FilledLeg(b.key(900.0), "buy", 30, 4.0, 20.0)
    assert FillResult((sell, buy), filled_at=b.SLOT_AT, rests_on="x").cash == 300.0 - 120.0 - 41.0
    assert FillResult(refused=(k.RefusalReason.MISSING_QUOTE,)).cash == 0


def test_a_seal_covers_only_its_file_and_fills_after_its_push():
    seal = b.seal()
    assert seal.covers(seal.sha256, seal.pushed_at)
    assert not seal.covers(seal.sha256, seal.pushed_at - timedelta(seconds=1))
    assert not seal.covers("00" * 32, seal.pushed_at)
    with pytest.raises(ValueError):
        Seal("p", "x", datetime(2026, 11, 2, 15, 3), "c")  # naive time


def test_a_quote_is_two_sided_only_when_valid_with_both_prices_and_sizes():
    assert b.quote().two_sided and b.quote().mid == 10.5
    assert not dataclasses.replace(b.quote(), valid=False).two_sided
    assert not dataclasses.replace(b.quote(), bid_qty=0).two_sided
    assert dataclasses.replace(b.quote(), ask=None).mid is None


def test_snapshot_expiries_are_nearest_first():
    with pytest.raises(ValueError):
        dataclasses.replace(b.snapshot(), expiries=(b.EXPIRY, b.SESSION))


def test_a_ledger_entry_records_fills_only_and_a_close_names_its_reason():
    with pytest.raises(ValueError):
        accounts.LedgerEntry(b.position(), FillResult(refused=(k.RefusalReason.MISSING_QUOTE,)), closes=False)
    with pytest.raises(ValueError):
        accounts.LedgerEntry(b.position(), b.filled(), closes=True)
    accounts.LedgerEntry(b.position(), b.filled(), closes=True, exit_reason=k.ExitReason.EXPIRY)


def test_snapshot_and_clock_times_must_be_aware():
    with pytest.raises(ValueError):
        dataclasses.replace(b.snapshot(), started_at=datetime(2026, 11, 2, 15, 0))
    with pytest.raises(ValueError):
        clock.FixedClock(datetime(2026, 11, 2, 15, 0))
    assert clock.FixedClock(b.SLOT_AT).now() == b.SLOT_AT
