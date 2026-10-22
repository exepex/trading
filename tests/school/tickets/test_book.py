"""Criterion 1 (story MS-P1f): tickets fill at the same quotes through the same fill port, live only in the ticket
ledger, and their rupees never reach an owner total."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.constants import SIDE_BUY
from fno.school.constants import ExitReason, ExitState, Outcome, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.accounts import SealedDecision, SettlementPrice
from fno.school.contracts.safety import LawResult
from fno.school.fakes import FakeAccounts, FakeFills, FakeSettlementSource
from fno.school.tickets.book import TicketBook, TicketLedger
from fno.school.tickets.rules import as_ticket
from fno.school.tickets.rupees import account_net
from fno.school.tickets.shared_size import OwnedFill, allocate
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import outcome_record

AT = b.SLOT_AT + timedelta(minutes=4)
MARKS = {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}
PASS = (LawResult("max_loss", True, None),)


def ticket(file_sha256: str = "cd" * 32) -> SealedDecision:
    return SealedDecision(as_ticket(b.decision(), TicketReason.TRADE_LIMIT), file_sha256)


def book() -> tuple[TicketBook, FakeAccounts, FakeAccounts]:
    accounts, ledger = FakeAccounts(2_000_000), FakeAccounts(0)
    source = FakeSettlementSource({("BANKNIFTY", b.EXPIRY): SettlementPrice(950.0, "ee" * 32)})
    return TicketBook(FakeFills(source), TicketLedger(ledger)), accounts, ledger


def test_a_ticket_fills_every_leg_at_the_snapshot_s_touch():
    tickets, _, _ = book()
    fill = tickets.enter(ticket(), PASS, b.snapshot(), b.seal(), AT)
    snapshot, proposal = b.snapshot(), ticket().decision.proposal
    expected = [snapshot.quote(leg.key).ask if leg.side == SIDE_BUY else snapshot.quote(leg.key).bid
                for leg in proposal.legs]  # fmt: skip
    assert [leg.price for leg in fill.legs] == expected and fill.rests_on == "cd" * 32


BINDING = (RefusalReason.MAX_LOSS, RefusalReason.UNPROTECTED, RefusalReason.SIZE_ABOVE_DISPLAYED,
           RefusalReason.PROTECTION_UNSELLABLE, RefusalReason.DAILY_STOP, RefusalReason.BRAKE)  # fmt: skip


@pytest.mark.parametrize("reason", BINDING)
def test_a_ticket_that_breaks_a_binding_law_is_refused_and_records_nothing(reason):
    tickets, _, ledger = book()
    fill = tickets.enter(ticket(), (*PASS, LawResult(str(reason), False, reason)), b.snapshot(), b.seal(), AT)
    assert fill.refused == (reason,) and ledger.ledgers == {}


def test_an_account_limit_does_not_stop_a_ticket():
    tickets, _, _ = book()
    cap = (LawResult("open_risk", False, RefusalReason.OPEN_RISK),)
    assert tickets.enter(ticket(), cap, b.snapshot(), b.seal(), AT).filled


def test_a_ticket_lives_in_the_ticket_ledger_never_in_an_account():
    tickets, accounts, ledger = book()
    tickets.enter(ticket(), PASS, b.snapshot(), b.seal(), AT)
    opened = ledger.view("CS1@1", MARKS, b.SESSION).open_positions
    assert [p.position_id for p in opened] == ["ticket:CS1@1:BANKNIFTY-M:2026-11-02"]
    assert opened[0].entry_net == tickets.fills.enter(ticket(), b.snapshot(), b.seal(), AT).cash
    assert accounts.view("CS1@1", MARKS, b.SESSION).open_positions == () and accounts.ledgers == {}


def test_a_ticket_with_a_stale_seal_or_a_missing_quote_records_nothing():
    tickets, _, ledger = book()
    stale = tickets.enter(ticket("00" * 32), PASS, b.snapshot(), b.seal(), AT)
    missing = tickets.enter(ticket(), PASS, b.snapshot(quotes={}), b.seal(), AT)
    assert RefusalReason.STALE_SEAL in stale.refused and RefusalReason.MISSING_QUOTE in missing.refused
    assert ledger.ledgers == {}


def test_a_trade_is_not_entered_as_a_ticket():
    tickets, _, _ = book()
    with pytest.raises(ValueError):
        tickets.enter(b.sealed(), PASS, b.snapshot(), b.seal(), AT)


def test_a_ticket_closes_at_the_touch_or_waits_and_settles_at_expiry():
    tickets, _, ledger = book()
    tickets.enter(ticket(), PASS, b.snapshot(), b.seal(), AT)
    position = ledger.view("CS1@1", MARKS, b.SESSION).open_positions[0]
    waiting = tickets.exit(position, ExitReason.PROFIT_TARGET, b.snapshot(quotes={}), "cd" * 32, b.seal(), AT)
    assert waiting.state == ExitState.EXIT_WAITING_QUOTE
    assert ledger.view("CS1@1", MARKS, b.SESSION).open_positions == (position,)
    settled = tickets.settle(position, b.EXPIRY)
    assert settled.filled and ledger.view("CS1@1", MARKS, b.SESSION).open_positions == ()
    assert ledger.ledgers["CS1@1"][-1].exit_reason == ExitReason.EXPIRY


def test_a_ticket_exit_fills_and_closes():
    tickets, _, ledger = book()
    tickets.enter(ticket(), PASS, b.snapshot(), b.seal(), AT)
    position = ledger.view("CS1@1", MARKS, b.SESSION).open_positions[0]
    closed = tickets.exit(position, ExitReason.SESSIONS_HELD, b.snapshot(), "cd" * 32, b.seal(), AT)
    assert closed.filled and ledger.view("CS1@1", MARKS, b.SESSION).open_positions == ()


def test_ticket_rupees_never_reach_the_owner_total():
    trade, ticket_outcome = outcome_record(), replace(outcome_record(), is_ticket=True, net=99_999.0)
    assert account_net([trade, ticket_outcome]).net == trade.net
    assert account_net([ticket_outcome]).net == 0 and account_net([]).net == 0


def test_two_accounts_on_one_displayed_size_sum_only_the_servable_one():
    quotes = {b.key(1000.0): b.quote(size=30), b.key(900.0): b.quote(4.0, 5.0, size=30)}
    snapshot = b.snapshot(quotes=quotes)
    first = FakeFills().enter(b.sealed(), snapshot, b.seal(), AT)
    second = FakeFills().enter(b.sealed(), snapshot, b.seal(), AT)  # REF's own fill: equal to CS1's, another owner
    allocation = allocate([OwnedFill("CS1@1", first), OwnedFill("REF@1", second)], snapshot, "15:00")
    lost = allocation.unservable[0]
    outcomes = [replace(outcome_record(), position_id=owner, driver_id=owner, entry=fill, net=100.0)
                for owner, fill in (("CS1@1", first), ("REF@1", second))]  # fmt: skip
    total = account_net(outcomes, allocation.unservable_fills)
    assert first == second and total.net == 100.0 and total.left_out == (lost.owner,)


def test_the_ticket_outcome_keeps_its_ticket_outcome_code():
    assert ticket().decision.outcome == Outcome.TICKET
