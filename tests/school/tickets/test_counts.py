"""Criteria 2 and 4 (story MS-P1f): the three counts over a fixture day keep eligible >= fillable >= executed, and
refusals, closed roads and refused tickets stay in the denominator."""

from dataclasses import replace

import pytest

from fno.school.constants import ClosureReason, NoTradeReason, Outcome, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.accounts import FillResult
from fno.school.contracts.decisions import Decision
from fno.school.contracts.safety import LawResult
from fno.school.tickets.counts import CountTotals, counts_for, totals
from fno.school.tickets.rules import as_ticket
from tests.school.contracts import builders as b

PASS = (LawResult("max_loss", True, None),)
CAP = (LawResult("open_risk", False, RefusalReason.OPEN_RISK),)
QUOTE = (LawResult("quote_gate", False, RefusalReason.MISSING_QUOTE),)
MISSING = FillResult(refused=(RefusalReason.MISSING_QUOTE,))


def plain(outcome: Outcome, reason: str) -> Decision:
    return Decision("CS1@1", RoadCode.NIFTY_MONTHLY, b.SESSION, outcome, reason)


TRADE = b.decision()
TICKET = as_ticket(b.decision(), TicketReason.TRADE_LIMIT)
REFUSED = Decision("CS1@1", RoadCode.BANKNIFTY_MONTHLY, b.SESSION, Outcome.REFUSED, RefusalReason.MAX_LOSS,
                   b.put_spread())  # fmt: skip

CASES = [  # decision, law results, fill, expected (eligible, fillable, executed)
    (TRADE, PASS, b.filled(), (1, 1, 1)),
    (TRADE, PASS, MISSING, (1, 0, 0)),  # passed the laws, then no quote at the fill
    (TRADE, PASS, None, (1, 0, 0)),
    (TRADE, CAP, b.filled(), (1, 0, 0)),  # a trade's laws are not relaxed (judge 481 minor a)
    (TICKET, CAP, b.filled(), (1, 1, 0)),  # an account limit does not bind a ticket
    (TICKET, QUOTE, b.filled(), (1, 0, 0)),
    (TICKET, PASS, MISSING, (1, 0, 0)),  # a refused ticket: still counted
    (REFUSED, (LawResult("max_loss", False, RefusalReason.MAX_LOSS),), None, (1, 0, 0)),
    (plain(Outcome.NO_TRADE, NoTradeReason.RULE_NOT_FIRED), (), None, (0, 0, 0)),
    (plain(Outcome.ROAD_CLOSED, ClosureReason.CAPTURE_MISSING), (), None, (0, 0, 0)),
]


@pytest.mark.parametrize("decision, results, fill, expected", CASES)
def test_each_case_counts_as_expected(decision, results, fill, expected):
    counts = counts_for(decision, results, fill)
    assert (counts.eligible, counts.fillable, counts.executed) == expected
    assert (counts.session, counts.road, counts.driver_id) == (decision.session, decision.road, decision.driver_id)


def test_a_fixture_day_keeps_the_order_and_every_decision_in_the_denominator():
    day = totals(replace(counts_for(*case[:3]), driver_id=f"D{i}@1") for i, case in enumerate(CASES))
    assert day == CountTotals(scheduled=10, eligible=8, fillable=2, executed=1)
    assert day.scheduled >= day.eligible >= day.fillable >= day.executed


def test_a_day_with_no_decision_counts_nothing():
    assert totals([]) == CountTotals(0, 0, 0, 0)


def test_a_second_row_for_one_decision_is_refused():
    row = counts_for(TRADE, PASS, b.filled())
    with pytest.raises(ValueError):
        totals([row, row])


def test_an_entry_the_shared_size_could_not_serve_is_fillable_not_executed():
    counts = counts_for(TRADE, PASS, b.filled(), size_shared=True)
    assert (counts.eligible, counts.fillable, counts.executed) == (1, 1, 0)
