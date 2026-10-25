"""F8 protocol sections 3-8: the two spreads' strikes, the forward at the open, the trade held to settlement at the
opening prices, the futility rule, the random-side control, the held-out verdict and its seal."""

from datetime import date

import pytest
from f1study.seal import SealBroken
from f8study import summary
from f8study.entries import forward_at_open
from f8study.spreads import CALL, PUT, CreditSpread, EntryQuote, as_quotes, spread_trade

from fno.config import load_app_config

ENTRY, EXPIRY = date(2024, 3, 1), date(2024, 3, 7)
STRIKES = {22000.0 + 50 * i for i in range(-10, 11)}
CHARGES = load_app_config()["charges"]


def test_an_atm_put_spread_sells_the_forward_strike_and_buys_half_a_percent_below():
    short, long_ = CreditSpread(PUT, 0.0, 0.005).build(STRIKES, 22010.0, 0.0)
    assert (short.strike, short.kind, short.side) == (22000.0, "PE", -1)
    assert (long_.strike, long_.kind, long_.side) == (21900.0, "PE", 1)  # 110 points, nearest listed below: 21900


def test_an_out_of_the_money_call_spread_sits_beyond_the_forward():
    short, long_ = CreditSpread(CALL, 0.005, 0.005).build(STRIKES, 22000.0, 0.0)
    assert short.strike == 22100.0 and long_.strike == 22200.0 and short.kind == long_.kind == "CE"


def test_the_forward_at_the_open_uses_parity_at_the_strike_nearest_the_previous_close():
    quotes = [EntryQuote(22000.0, "CE", 130.0, 1.0, 5), EntryQuote(22000.0, "PE", 100.0, 1.0, 5),
              EntryQuote(22050.0, "CE", 110.0, 1.0, 0), EntryQuote(22050.0, "PE", 120.0, 1.0, 5),
              EntryQuote(22500.0, "CE", 10.0, 1.0, 5), EntryQuote(22500.0, "PE", 400.0, 1.0, 5)]  # fmt: skip
    assert forward_at_open(quotes, 22040.0) == pytest.approx(22030.0)  # 22050's call did not trade
    assert forward_at_open([], 22000.0) is None


def chain(volume=5):
    out = []
    for k in sorted(STRIKES):
        out += [
            EntryQuote(k, "CE", max(22000.0 - k, 0) + 60.0, 1.0, volume),
            EntryQuote(k, "PE", max(k - 22000.0, 0) + 60.0 - (22000.0 - k) * 0.1 * (k < 22000), 1.0, volume),
        ]
    return as_quotes(out, EXPIRY, at_open=True)  # fmt: skip


def test_a_put_spread_settled_above_its_short_keeps_its_credit_less_costs():
    t = spread_trade("P0W5", PUT, ENTRY, EXPIRY, chain(), 22000.0, 65, 22500.0, CHARGES, 1.0)
    assert t.status == "taken" and t.credit > 0
    assert t.gross == pytest.approx(t.credit * 65)
    assert t.pads == 2 * 65 * 1.0 and t.net == pytest.approx(t.gross - t.charges - t.pads)


def test_a_put_spread_settled_below_its_long_loses_the_width_less_credit():
    t = spread_trade("P0W5", PUT, ENTRY, EXPIRY, chain(), 22000.0, 65, 20000.0, CHARGES, 1.0)
    width = t.legs[0].strike - t.legs[1].strike
    assert t.gross == pytest.approx((t.credit - width) * 65)


def test_untraded_legs_are_refused():
    assert spread_trade("P0W5", CALL, ENTRY, EXPIRY, chain(volume=0), 22000.0, 65, 22000.0, CHARGES, 1.0).status != (
        "taken")  # fmt: skip


def side_rows(nets, side="put"):
    return [{"cycle": f"2020-01-{i + 1:02d}", "side": side, "status": "taken", "gross": n, "charges": 0.0,
             "pads": 0.0, "net": n, "credit": 1.0, "width": 100.0} for i, n in enumerate(nets)]  # fmt: skip


@pytest.mark.parametrize(("put", "call", "futile"), [(-200.0, -399.0, False), (-200.0, -401.0, True)])
def test_the_futility_line_is_minus_300_on_the_side_average(put, call, futile):
    sides = {"put": side_rows([put] * 3), "call": side_rows([call] * 3, "call")}
    assert summary.discovery_row(sides, sides, sides)["futile"] is futile


def test_random_sides_keep_the_call_count_and_are_seeded():
    pairs = list(zip(side_rows([100.0] * 20), side_rows([-100.0] * 20, "call"), strict=True))
    p = summary.random_side_p(pairs, 10, 100.0)
    assert p == summary.random_side_p(pairs, 10, 100.0) and p == 0.0  # no random half-and-half reaches all puts
    assert summary.random_side_p(pairs, 0, 100.0) == 1.0


def held(p, p_side, pad2=1.0, gross=300.0):
    return {"p": p, "p_side": p_side, "mean_net_pad2": pad2, "mean_gross": gross}


def test_the_verdict_needs_both_holm_tests_the_pad_and_the_gross_bar():
    rows = {"A": held(0.001, 0.001), "B": held(0.001, 0.2), "C": held(0.001, 0.001, pad2=-1.0),
            "D": held(0.001, 0.001, gross=250.0)}  # fmt: skip
    assert summary.verdicts(rows) == ["A"]


def test_the_seal_refuses_held_out_cycles(monkeypatch):
    import study_f8

    monkeypatch.setattr(study_f8, "market", lambda: pytest.fail("must not read"))
    with pytest.raises(SealBroken):
        study_f8.cycle_inputs(study_f8.HELD_OUT, held_out_open=False)
