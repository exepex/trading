"""Section 9's historical-STT side run: each order is charged at its own trade date's rate (entry at entry, the exit
at its exit day, settlement at expiry), and the schedule's dates are those of the Finance Acts and Budget 2026."""

from datetime import date

import pytest
from edge1study.structures import SC2, structure
from edge1study.stt_history import charges_on, rates_on
from edge1study.trade import EXP, T21, run_trade

from .edge1_fakes import DAYS, ENTRY, EXIT, EXPIRY, cycle, panel, terms


@pytest.mark.parametrize(("day", "rates"), [
    (date(2019, 1, 1), (0.05, 0.125)), (date(2023, 3, 31), (0.05, 0.125)), (date(2023, 4, 1), (0.0625, 0.125)),
    (date(2024, 9, 30), (0.0625, 0.125)), (date(2024, 10, 1), (0.1, 0.125)), (date(2026, 3, 31), (0.1, 0.125)),
    (date(2026, 4, 1), (0.15, 0.15)),
])  # fmt: skip
def test_the_schedule_changes_on_each_acts_first_day(day, rates):
    assert rates_on(day) == rates


def test_a_day_before_the_schedule_is_refused():
    with pytest.raises(ValueError):
        rates_on(date(2010, 1, 1))


def test_only_the_two_stt_rates_change():
    decided = terms(65, 1.0).charges
    found = charges_on(decided)(date(2020, 1, 1))
    assert {k for k in decided if found[k] != decided[k]} == {"stt_sell_pct", "stt_exercise_pct"}


def _trade(exit_rule, on=None):
    return run_trade(structure(SC2), panel({}), cycle(), terms(65, 1.0), exit_rule, DAYS, lambda e: 23000.0,
                     charges_on=on)  # fmt: skip


@pytest.mark.parametrize(("exit_rule", "closing_day"), [(T21, EXIT), (EXP, EXPIRY)])
def test_each_order_is_charged_on_its_own_trade_date(exit_rule, closing_day):
    seen = []
    decided = terms(65, 1.0).charges

    def on(day):
        seen.append(day)
        return decided

    assert _trade(exit_rule, on).charges == pytest.approx(_trade(exit_rule).charges)
    assert seen == [ENTRY, closing_day]


def test_a_lower_historical_rate_lowers_only_the_charges():
    decided, older = _trade(T21), _trade(T21, lambda day: {**terms(65, 1.0).charges, "stt_sell_pct": 0.05})
    assert older.charges < decided.charges and older.gross == pytest.approx(decided.gross)
    assert older.net - decided.net == pytest.approx(decided.charges - older.charges)
