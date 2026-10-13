"""Story C2 criterion 3 (and 6): the drawdown brake on closed equity, the owner's restart and its re-arm level."""

from datetime import date

import pytest

from fno.risk.drawdown import DrawdownBrake, high_water_mark
from fno.risk.inputs import RiskInputError

from .builders import FLY, book, market, open_trade, proposal, short_fly

D = date
EXPIRY = date(2026, 10, 27)
SERIES = ((D(2026, 9, 1), 500_000.0), (D(2026, 9, 10), 520_000.0), (D(2026, 9, 20), 490_000.0))  # 30,000 below
BRAKE = DrawdownBrake(30000)


def _check(closed, restarts=(), open_trades=()):
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
    return BRAKE.check(new, book(open_trades, closed=closed, restarts=restarts), market(25000, {}, EXPIRY))


def test_30000_below_the_high_blocks_every_new_entry():
    verdict = _check(SERIES)
    assert not verdict.ok
    assert verdict.numbers["high_water_mark_rs"] == 520_000.0 and verdict.numbers["drawdown_rs"] == 30_000.0
    assert "Rs 30,000.00 below its high Rs 520,000.00" in verdict.reason


@pytest.mark.parametrize(("closed_now", "ok"), [(490_000.01, True), (490_000.0, False), (480_000.0, False)])
def test_brake_just_inside_and_just_outside(closed_now, ok):
    assert _check(SERIES[:2] + ((D(2026, 9, 20), closed_now),)).ok is ok


def test_the_brake_never_closes_open_trades():
    """The rule only answers for the proposal: the book's open trades are untouched, still there after the check."""
    held = open_trade("held", FLY, 200, short_fly(25000, 200), EXPIRY, 0.0)
    the_book = book([held], closed=SERIES)
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
    assert not BRAKE.check(new, the_book, market(25000, {}, EXPIRY)).ok
    assert the_book.open_trades == (held,)


def test_after_the_owners_restart_entries_are_allowed_and_the_brake_rearms_30000_below_that_day():
    restarted = _check(SERIES, restarts=(D(2026, 9, 20),))
    assert restarted.ok and restarted.numbers["brake_level_rs"] == 460_000.0
    assert restarted.numbers["restarted_on"] == "2026-09-20"
    later = SERIES + ((D(2026, 9, 25), 460_000.01),)
    assert _check(later, restarts=(D(2026, 9, 20),)).ok
    hit_again = SERIES + ((D(2026, 9, 25), 460_000.0),)
    assert not _check(hit_again, restarts=(D(2026, 9, 20),)).ok


def test_after_a_restart_the_high_rises_again_from_new_highs():
    series = SERIES + ((D(2026, 9, 25), 505_000.0), (D(2026, 9, 30), 475_000.0))
    assert high_water_mark(series, (D(2026, 9, 20),), 30000) == (505_000.0, D(2026, 9, 20))
    assert not _check(series, restarts=(D(2026, 9, 20),)).ok


def test_a_restart_when_the_brake_was_not_in_force_is_refused():
    with pytest.raises(RiskInputError, match="not in force"):
        high_water_mark(SERIES[:2], (D(2026, 9, 10),), 30000)


def test_the_restart_uses_the_closing_equity_of_its_day_when_no_trade_closed_that_day():
    assert high_water_mark(SERIES, (D(2026, 9, 22),), 30000) == (490_000.0, D(2026, 9, 22))
