"""F1 protocol sections 4, 6 and 7: weekly cycles from the files' own expiries, the structures centred on the forward,
the cap, the settlement P&L and the held-out lots."""

from datetime import date, timedelta

import pytest
from f1study.cycles import MOVED, NO_ENTRY_FILE, SHORT, TAKEN_CYCLE, expiry_days, weekly_cycles
from f1study.gate import implied
from f1study.held_out_lots import held_out_lot
from f1study.inputs import IndexCloses, cycle_inputs
from f1study.trades import CycleInputs, run_cycle, structure_for

from fno.config import load_app_config

from .f1_fakes import ENTRY, EXPIRY, chain, rows

PREV = date(2024, 2, 29)
SESSIONS = [PREV, ENTRY, date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6), EXPIRY]
CHARGES = load_app_config()["charges"]


def expiry_rows(day):
    return rows(day, chain(expiry=day))


def test_an_expiry_day_is_a_session_listing_options_of_that_date():
    data = [expiry_rows(PREV), rows(ENTRY, chain()), expiry_rows(EXPIRY)]
    assert expiry_days(data) == [PREV, EXPIRY]


def test_a_cycle_enters_the_session_after_the_previous_expiry():
    data = [expiry_rows(PREV), rows(ENTRY, chain()), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    assert (c.entry_day, c.expiry, c.sessions, c.status) == (ENTRY, EXPIRY, 4, TAKEN_CYCLE)


def test_a_cycle_with_fewer_than_two_sessions_is_short():
    data = [expiry_rows(date(2024, 3, 5)), rows(date(2024, 3, 6), chain()), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    assert c.status == SHORT


def test_a_target_no_longer_listed_on_entry_is_a_moved_expiry():
    data = [expiry_rows(PREV), rows(ENTRY, chain(expiry=EXPIRY + timedelta(days=1))), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    assert c.status == MOVED


def test_an_entry_day_without_a_file_is_counted():
    data = [expiry_rows(PREV), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    assert c.status == NO_ENTRY_FILE


def test_no_cycle_outside_the_period():
    data = [expiry_rows(PREV), rows(ENTRY, chain()), expiry_rows(EXPIRY)]
    assert weekly_cycles("NIFTY", data, SESSIONS, EXPIRY + timedelta(days=1), EXPIRY + timedelta(days=30)) == []


def inputs_for(settlement, lot=25, forward=22000.0):
    data = [expiry_rows(PREV), rows(ENTRY, chain(forward=forward), lots={EXPIRY: lot}), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    closes = {date(2024, 1, 1) + timedelta(days=i): 22000.0 * (1.001 ** (i % 3)) for i in range(59)}
    closes.update({ENTRY: forward, EXPIRY: settlement})
    found, skips, _ = cycle_inputs([c], data, IndexCloses.of(closes))
    return found, skips


def test_a_fly_settled_at_its_body_keeps_the_credit_less_charges_and_entry_pads():
    (inputs,), _ = inputs_for(settlement=22000.0)
    trade = run_cycle("WF", inputs, CHARGES, pad=1.0)
    assert trade.status == "taken"
    assert trade.legs[0].strike == trade.legs[1].strike == 22000.0
    assert trade.pads == 4 * 1.0 * 25
    assert trade.net == pytest.approx(trade.gross - trade.charges - trade.pads)
    assert trade.gross == pytest.approx(trade.credit * 25)


def test_a_fly_settled_beyond_a_wing_loses_at_most_the_width_less_credit():
    (inputs,), _ = inputs_for(settlement=30000.0)
    trade = run_cycle("WF", inputs, CHARGES, pad=1.0)
    assert trade.gross == pytest.approx((trade.credit - trade.width) * 25)
    assert -trade.gross <= 10000.0


def test_the_cap_picks_a_narrower_width_or_refuses():
    (inputs,), _ = inputs_for(settlement=22000.0, lot=2000)
    assert run_cycle("WF", inputs, CHARGES, pad=1.0).status == "no_trade_cap"


def test_the_condor_shorts_sit_one_implied_move_from_the_forward():
    (inputs,), _ = inputs_for(settlement=22000.0)
    move = structure_for("WC", inputs).offset * 22000.0
    trade = run_cycle("WC", inputs, CHARGES, pad=1.0)
    call, put = trade.legs[0].strike, trade.legs[1].strike
    assert abs(call - 22000.0 - move) <= 25 and abs(22000.0 - put - move) <= 25


def test_a_cycle_without_a_settlement_close_is_skipped():
    data = [expiry_rows(PREV), rows(ENTRY, chain(), lots={EXPIRY: 25}), expiry_rows(EXPIRY)]
    (c,) = weekly_cycles("NIFTY", data, SESSIONS, PREV, EXPIRY)
    closes = {date(2024, 1, 1) + timedelta(days=i): 22000.0 for i in range(60)} | {ENTRY: 22000.0}
    found, skips, _ = cycle_inputs([c], data, IndexCloses.of(closes))
    assert not found and skips[0].reason == "no_settlement"


def test_the_gate_reads_only_closes_before_the_entry_session():
    closes = IndexCloses.of({date(2024, 2, 27): 1.0, date(2024, 2, 28): 2.0, ENTRY: 3.0})
    assert closes.before(ENTRY) == [1.0, 2.0]
    assert closes.on(ENTRY) == 3.0 and closes.on(PREV) is None


def test_the_cycle_inputs_quotes_are_only_the_target_expiry():
    (inputs,), _ = inputs_for(settlement=22000.0)
    assert {q.expiry for q in inputs.quotes} == {EXPIRY}
    assert isinstance(inputs, CycleInputs) and implied(inputs.quotes, EXPIRY, 22000.0, 4).status == "ok"


@pytest.mark.parametrize(("index", "expiry", "lot"),
                         [("FINNIFTY", date(2023, 5, 2), 40), ("MIDCPNIFTY", date(2023, 5, 1), 75),
                          ("FINNIFTY", date(2024, 7, 2), None), ("NIFTY", date(2021, 8, 5), 50)])  # fmt: skip
def test_held_out_lots(index, expiry, lot):
    assert held_out_lot(index, expiry) == lot
