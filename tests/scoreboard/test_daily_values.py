"""Story S2: each trade's value on each session day by hand. Cash moved so far plus the legs at the day's mid; a
missing mid keeps the last valid mark (flagged stale); a leg never marked leaves the day unvalued; the daily changes
add up to the trade's net in C1's trade ledger."""

from datetime import date, datetime, time

from fno.accounting.ledgers import Order, trade_line
from fno.books.equity import trade_positions
from fno.books.fills import Fill
from fno.constants import SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.scoreboard.daily_values import daily_changes, key_of, trade_days
from tests.scorecard.history import CHARGES, LONG, SHORT, UNITS

D1, D2, D3, D4 = date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16), date(2026, 10, 19)


def fill(name, leg, side, price, day):
    order = Order(side, price, UNITS, 0.0)
    when = datetime.combine(day, time(15, 15), IST)
    return Fill.priced(name, "t1", when, leg.contract, order, CHARGES)


OPEN = [fill("o1", LONG, SIDE_BUY, 20.0, D1), fill("o2", SHORT, SIDE_SELL, 70.0, D1)]
CLOSE = [fill("c1", SHORT, SIDE_BUY, 40.0, D4), fill("c2", LONG, SIDE_SELL, 10.0, D4)]
LEGS = {LONG.contract: LONG, SHORT.contract: SHORT}


def marks(table):
    return lambda day: table.get(day, {})


def both(long_mid, short_mid):
    return {key_of(LONG): long_mid, key_of(SHORT): short_mid}


def test_a_trade_s_value_each_day_is_its_cash_plus_its_legs_at_mid():
    table = {D1: both(19.0, 69.0), D2: both(15.0, 55.0), D3: both(12.0, 45.0)}
    days = trade_days(OPEN + CLOSE, LEGS, [D1, D2, D3, D4], marks(table))
    cash_open = sum(f.amount for f in OPEN)
    assert days[0].value == cash_open + UNITS * 19.0 - UNITS * 69.0
    assert days[1].value == cash_open + UNITS * 15.0 - UNITS * 55.0
    assert days[3].value == sum(f.amount for f in OPEN + CLOSE)  # closed: its cash flow alone, no marks needed


def test_the_daily_changes_add_up_to_the_trade_ledger_net():
    table = {D1: both(19.0, 69.0), D2: both(15.0, 55.0), D3: both(12.0, 45.0)}
    changes = daily_changes(trade_days(OPEN + CLOSE, LEGS, [D1, D2, D3, D4], marks(table)))
    position = trade_positions(OPEN + CLOSE)["t1"]
    line = trade_line(position.as_ledger_trade(), CHARGES)
    assert abs(sum(changes.values()) - line.net) < 1e-9 and list(changes) == [D1, D2, D3, D4]


def test_a_missing_mid_keeps_the_last_valid_mark_flagged_stale():
    table = {D1: both(19.0, 69.0), D2: {key_of(LONG): 15.0}}
    days = trade_days(OPEN, LEGS, [D1, D2], marks(table))
    assert days[1].value == sum(f.amount for f in OPEN) + UNITS * 15.0 - UNITS * 69.0
    assert days[1].stale == (SHORT.contract,) and days[0].stale == ()


def test_a_leg_never_marked_leaves_the_day_unvalued_and_its_move_lands_on_the_next_valued_day():
    table = {D2: both(15.0, 55.0)}
    days = trade_days(OPEN, LEGS, [D1, D2], marks(table))
    assert days[0].value is None
    changes = daily_changes(days)
    assert D1 not in changes and changes[D2] == days[1].value  # the whole move from zero, nothing invented
