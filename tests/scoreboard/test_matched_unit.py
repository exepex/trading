"""Story S3 criteria 6 and 7: the standard unit (one lot, E4 touch fills, time exit, retry, E7 settlement) and each
record's take, skip or not-observed reading. Charges are Rs 20 an order, so each figure is checked by hand."""

from datetime import date

import pytest

from fno.constants import Decision
from fno.desk.pricing import DeskLeg
from fno.desk.settlement import SettlementError
from fno.research_engine.structures import Leg
from fno.risk.open_risk import HeldMaxLoss
from fno.scoreboard.matched_actions import NOT_OBSERVED, SKIP, TAKE, action_of
from fno.scoreboard.standard_unit import CLOSED, MAX_LOSS_UNKNOWN, NOT_FILLED, OPEN, StandardUnit
from tests.scoreboard.matched_builders import CHARGES, EXPIRY, LOT, Calendar, Settlements, Snapshots, quote, record

ENTRY, EXIT, NEXT = date(2026, 11, 2), date(2026, 11, 4), date(2026, 11, 5)
CALL = DeskLeg("NIFTY-C-25000", EXPIRY, Leg(25000.0, "CE", 1))
SHORT_CALL = DeskLeg("NIFTY-C-25100", EXPIRY, Leg(25100.0, "CE", -1))


def unit(quotes, settlements=None) -> StandardUnit:
    source = Snapshots(quotes)
    days = lambda day: source.snapshot(day, "s") if day in quotes else None  # noqa: E731
    return StandardUnit(days, Calendar().sessions, settlements or Settlements(), HeldMaxLoss(CHARGES), CHARGES, LOT)


def test_a_long_call_bought_at_the_ask_and_sold_at_the_bid_on_its_exit_day():
    quotes = {ENTRY: [quote(25000, "CE", 99, 100)], EXIT: [quote(25000, "CE", 130, 131)]}
    result = unit(quotes).value([CALL], ENTRY, EXIT, NEXT)
    # paid 100 x 75 + Rs 20, received 130 x 75 - Rs 20; maximum loss (B2) = 7,520 paid + Rs 1 exit pad x 75 units + the
    # exit order's Rs 20 brokerage, which B2 charges even at zero value
    assert (result.status, result.net, result.max_loss, result.exited_on) == (CLOSED, 2210.0, 7615.0, EXIT)


def test_an_entry_leg_without_enough_size_at_the_touch_is_not_filled():
    quotes = {ENTRY: [quote(25000, "CE", 99, 100, size=LOT - 1)]}
    result = unit(quotes).value([CALL], ENTRY, EXIT, NEXT)
    assert result.status == NOT_FILLED and result.net is None and "not enough size" in result.note


def test_a_leg_without_a_quote_on_the_exit_day_exits_at_the_next_snapshot_dated_that_day():
    quotes = {ENTRY: [quote(25000, "CE", 99, 100)], EXIT: [], NEXT: [quote(25000, "CE", 120, 121)]}
    result = unit(quotes).value([CALL], ENTRY, EXIT, NEXT)
    assert (result.status, result.net, result.exited_on) == (CLOSED, 120 * LOT - 20 - 7520, NEXT)
    assert not result.staggered  # one leg: one exit session


def test_legs_that_exit_on_different_sessions_are_marked_staggered():
    """Review 120 (response 200 disclosure 5): the short call exits on its exit day, the long call a session later."""
    quotes = {ENTRY: [quote(25000, "CE", 99, 100), quote(25100, "CE", 60, 61)], EXIT: [quote(25100, "CE", 70, 71)],
              NEXT: [quote(25000, "CE", 120, 121)]}  # fmt: skip
    result = unit(quotes).value([CALL, SHORT_CALL], ENTRY, EXIT, NEXT)
    assert (result.status, result.exited_on, result.staggered) == (CLOSED, NEXT, True)


def test_a_leg_still_open_after_expiry_is_settled_at_e7s_price_and_open_until_it_is_published():
    quotes = {ENTRY: [quote(25000, "CE", 99, 100)]}
    after = date(2026, 11, 25)
    waiting = unit(quotes).value([CALL], ENTRY, EXIT, after)
    assert (waiting.status, waiting.past_expiry) == (OPEN, True)  # no settlement file yet: incomplete
    settled = unit(quotes, Settlements({EXPIRY: 25150.0})).value([CALL], ENTRY, EXIT, after)
    # intrinsic 150 x 75 received, Rs 20 brokerage on the exercise
    assert (settled.status, settled.net, settled.exited_on) == (CLOSED, 150 * LOT - 20 - 7520, EXPIRY)


def test_an_action_before_its_exit_day_is_open_and_unscored():
    result = unit({ENTRY: [quote(25000, "CE", 99, 100)]}).value([CALL], ENTRY, EXIT, ENTRY)
    assert result.status == OPEN and result.net is None and result.max_loss == 7615.0 and not result.past_expiry


def test_a_position_with_more_calls_sold_than_bought_has_no_fixed_maximum_loss():
    quotes = {ENTRY: [quote(25100, "CE", 50, 51)]}
    assert unit(quotes).value([SHORT_CALL], ENTRY, EXIT, NEXT).status == MAX_LOSS_UNKNOWN


@pytest.mark.parametrize(
    ("body", "kind"),
    [
        (record("o", Decision.CHOSEN), TAKE),
        (record("o", Decision.NOT_CHOSEN, "risk: bucket", failed=(("bucket_cap", "over"),)), TAKE),
        (record("o", Decision.NOT_CHOSEN, "unproven: 3 completed paper trades"), TAKE),
        (record("o", Decision.NOT_CHOSEN, "risk: stress", failed=(("stress_loss", "above"),)), TAKE),
        (record("o", Decision.NOT_CHOSEN, "risk: exposure", failed=(("exposure_limit", "above"),)), TAKE),
        (record("o", Decision.NOT_CHOSEN, "risk: open", failed=(("inputs", "trade x is already open in b"),)), TAKE),
        (record("o", Decision.NOT_CHOSEN, "risk: in", failed=(("inputs", "proposal has no expiry"),)), SKIP),
        (record("o", Decision.NOT_CHOSEN, "risk: cap", failed=(("max_loss_per_trade", "above"),)), SKIP),
        (record("o", Decision.NOT_CHOSEN, "risk", failed=(("max_loss_per_trade", "a"), ("bucket_cap", "b"))), SKIP),
        (record("o", Decision.NOT_CHOSEN, "risk", failed=(("bucket_cap", "refused, input not usable: x"),)),
         NOT_OBSERVED),
        (record("o", Decision.NOT_CHOSEN, "risk", failed=(("paper_account", "opened with 1"),)), NOT_OBSERVED),
        (record("o", Decision.CHOSEN, "blocked by C4 hard validity: x", action="no trade"), SKIP),
        (record("o", Decision.NOT_CHOSEN, "blocked by C4 hard validity: x", failed=(("bucket_cap", "over"),)), SKIP),
        (record("o", Decision.NO_TRADE, "rule did not fire", legs=()), SKIP),
    ],
)  # fmt: skip
def test_each_record_reads_as_the_story_says(body, kind):
    assert action_of(body).kind == kind


def test_a_take_refused_by_account_limits_lists_each_original_refusal():
    """Review 120 (response 200 disclosure 4): the rule and its words, so the owner sees what the account stopped."""
    body = record("o", Decision.NOT_CHOSEN, "risk", failed=(("bucket_cap", "over by 2,000"), ("margin_room", "short")))
    assert action_of(body).reason == "account limit only (bucket_cap: over by 2,000; margin_room: short)"
    unproven = record("o", Decision.NOT_CHOSEN, "unproven: 3 completed paper trades")
    assert action_of(unproven).reason == "account limit only (unproven: 3 completed paper trades)"


class RefusedSettlement(Settlements):
    def final_settlement(self, underlying, expiry):
        raise SettlementError("two different prices in the expiry file")


def test_a_settlement_file_without_one_clear_price_leaves_the_unit_open_with_the_reason():
    result = unit({ENTRY: [quote(25000, "CE", 99, 100)]}, RefusedSettlement()).value(
        [CALL], ENTRY, EXIT, date(2026, 11, 25)
    )
    assert result.status == OPEN and "settlement refused: two different prices" in result.note
