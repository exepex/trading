"""Criterion 1 (story MS-P1f): tickets fill at the same quotes through the same fill port, live only in the ticket
ledger, and their rupees never reach an owner total."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.school.constants import ExitReason, ExitState, Outcome, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.accounts import SealedDecision, SettlementPrice
from fno.school.fakes import FakeAccounts, FakeFills, FakeSettlementSource
from fno.school.tickets.book import TicketBook, fill_cash
from fno.school.tickets.rules import as_ticket
from fno.school.tickets.rupees import account_net
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import outcome_record

AT = b.SLOT_AT + timedelta(minutes=4)
MARKS = {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()}


def ticket(file_sha256: str = "cd" * 32) -> SealedDecision:
    return SealedDecision(as_ticket(b.decision(), TicketReason.TRADE_LIMIT), file_sha256)


def book() -> tuple[TicketBook, FakeAccounts, FakeAccounts]:
    accounts, ledger = FakeAccounts(2_000_000), FakeAccounts(0)
    source = FakeSettlementSource({("BANKNIFTY", b.EXPIRY): SettlementPrice(950.0, "ee" * 32)})
    return TicketBook(FakeFills(source), ledger), accounts, ledger


def test_a_ticket_fills_at_the_same_touch_a_trade_would():
    tickets, _, _ = book()
    as_ticket_fill = tickets.enter(ticket(), b.snapshot(), b.seal(), AT)
    as_trade_fill = FakeFills().enter(b.sealed(), b.snapshot(), b.seal(), AT)
    assert as_ticket_fill == as_trade_fill and as_ticket_fill.filled


def test_a_ticket_lives_in_the_ticket_ledger_never_in_an_account():
    tickets, accounts, ledger = book()
    tickets.enter(ticket(), b.snapshot(), b.seal(), AT)
    opened = ledger.view("CS1@1", MARKS, b.SESSION).open_positions
    assert [p.position_id for p in opened] == ["ticket:CS1@1:BANKNIFTY-M:2026-11-02"]
    assert opened[0].entry_net == fill_cash(tickets.fills.enter(ticket(), b.snapshot(), b.seal(), AT))
    assert accounts.view("CS1@1", MARKS, b.SESSION).open_positions == () and accounts.ledgers == {}


def test_a_ticket_with_a_stale_seal_or_a_missing_quote_records_nothing():
    tickets, _, ledger = book()
    stale = tickets.enter(ticket("00" * 32), b.snapshot(), b.seal(), AT)
    missing = tickets.enter(ticket(), b.snapshot(quotes={}), b.seal(), AT)
    assert RefusalReason.STALE_SEAL in stale.refused and RefusalReason.MISSING_QUOTE in missing.refused
    assert ledger.ledgers == {}


def test_a_trade_is_not_entered_as_a_ticket():
    tickets, _, _ = book()
    with pytest.raises(ValueError):
        tickets.enter(b.sealed(), b.snapshot(), b.seal(), AT)


def test_a_ticket_closes_at_the_touch_or_waits_and_settles_at_expiry():
    tickets, _, ledger = book()
    tickets.enter(ticket(), b.snapshot(), b.seal(), AT)
    position = ledger.view("CS1@1", MARKS, b.SESSION).open_positions[0]
    waiting = tickets.exit(position, ExitReason.PROFIT_TARGET, b.snapshot(quotes={}), "cd" * 32, b.seal(), AT)
    assert waiting.state == ExitState.EXIT_WAITING_QUOTE
    assert ledger.view("CS1@1", MARKS, b.SESSION).open_positions == (position,)
    settled = tickets.settle(position, b.EXPIRY)
    assert settled.filled and ledger.view("CS1@1", MARKS, b.SESSION).open_positions == ()
    assert ledger.ledgers["CS1@1"][-1].exit_reason == ExitReason.EXPIRY


def test_a_ticket_exit_fills_and_closes():
    tickets, _, ledger = book()
    tickets.enter(ticket(), b.snapshot(), b.seal(), AT)
    position = ledger.view("CS1@1", MARKS, b.SESSION).open_positions[0]
    closed = tickets.exit(position, ExitReason.SESSIONS_HELD, b.snapshot(), "cd" * 32, b.seal(), AT)
    assert closed.filled and ledger.view("CS1@1", MARKS, b.SESSION).open_positions == ()


def test_ticket_rupees_never_reach_the_owner_total():
    trade, ticket_outcome = outcome_record(), replace(outcome_record(), is_ticket=True, net=99_999.0)
    assert account_net([trade, ticket_outcome]) == trade.net
    assert account_net([ticket_outcome]) == 0 and account_net([]) == 0


def test_the_ticket_outcome_keeps_its_ticket_outcome_code():
    assert ticket().decision.outcome == Outcome.TICKET
