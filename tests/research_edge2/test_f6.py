"""F6 protocol sections 3-7: signals from day t's file trade from t+1's open; the futures charges match the protocol's
stated round trip; the contract does not roll inside a trade; Newey-West, Holm, the random-sign control, nomination
and the date seal."""

from datetime import date, timedelta

import pytest
from f1study.seal import SealBroken
from f6study import summary
from f6study.data import FutureBar, Session
from f6study.trades import FLAT, NO_PRICE, NO_SIGNAL, TAKEN, FuturesRates, order_charges, side_of, stt_on, trade

RATES = FuturesRates()
EXPIRY = date(2024, 3, 28)


def bar(open_=25000.0, close=25000.0, expiry=EXPIRY, lot=65):
    return FutureBar(expiry, open_, close, lot, False)


def sessions(fii, client=None, bars=None):
    start = date(2024, 3, 1)
    client = client or [0] * len(fii)
    bars = bars or [(bar(),)] * len(fii)
    return [Session(start + timedelta(days=i), f, c, b) for i, (f, c, b) in enumerate(zip(fii, client, bars))]


def test_the_round_trip_matches_the_protocol_figure():
    buy, sell = order_charges(25000.0, 65, True, RATES), order_charges(25000.0, 65, False, RATES)
    assert buy + sell == pytest.approx(966.22, abs=0.01)
    assert sell - buy == pytest.approx(812.50 - 32.50)


def test_historical_stt_by_date():
    assert [stt_on(d) for d in (date(2022, 1, 3), date(2023, 4, 3), date(2024, 10, 1), date(2026, 4, 1))] == [
        0.01, 0.0125, 0.02, 0.05]  # fmt: skip


@pytest.mark.parametrize(("signal", "fii", "client", "expected"),
                         [("FD", [100, 150], None, 1), ("FD", [100, 50], None, -1), ("FD", [100, 100], None, 0),
                          ("CD", [0, 0], [10, 20], -1), ("CD", [0, 0], [20, 10], 1),
                          ("FD", [None, 150], None, None)])  # fmt: skip
def test_signals_and_their_directions(signal, fii, client, expected):
    assert side_of(signal, sessions(fii, client), 1) == expected


def test_the_level_signal_needs_twenty_files_and_reads_none_after_its_day():
    nets = list(range(19)) + [100, -1000]
    s = sessions(nets)
    assert side_of("FL", s, 18) is None
    assert side_of("FL", s, 19) == 1  # day 19's level is above its mean; day 20's file is not read


def test_a_signal_trades_from_the_next_open_to_the_horizon_close():
    s = sessions([100, 150, 150, 150], bars=[(bar(1, 1),), (bar(2, 2),), (bar(25000.0, 25100.0),), (bar(9, 9),)])
    row = trade("FD", "H1", s, 1, RATES, 1.0)
    assert (row["entry"], row["exit"], row["status"]) == (s[2].day.isoformat(), s[2].day.isoformat(), TAKEN)
    assert row["gross"] == pytest.approx(100.0 * 65)
    assert row["net"] == pytest.approx(row["gross"] - row["charges"] - 2 * 65)


def test_a_short_pays_stt_on_its_opening_sale():
    s = sessions([100, 50, 50], bars=[(bar(),), (bar(),), (bar(25000.0, 24900.0),)])
    row = trade("FD", "H1", s, 1, RATES, 0.0)
    assert row["side"] == -1 and row["gross"] == pytest.approx(6500.0)
    assert row["charges"] == pytest.approx(order_charges(24900.0, 65, True, RATES) + order_charges(25000.0, 65,
                                           False, RATES))  # fmt: skip


def test_no_roll_inside_a_trade():
    near, far = bar(expiry=date(2024, 3, 4)), bar(25000.0, 25200.0, expiry=date(2024, 4, 25))
    s = sessions([100, 150, 150, 150, 150, 150, 150], bars=[(near, far)] * 3 + [(far,)] * 4)
    row = trade("FD", "H5", s, 1, RATES, 1.0)
    assert row["status"] == TAKEN and row["gross"] == pytest.approx(200.0 * 65)


def test_missing_prices_and_flat_or_missing_signals_are_counted():
    s = sessions([100, 150, 150], bars=[(bar(),), (bar(),), ()])
    assert trade("FD", "H1", s, 1, RATES, 1.0)["status"] == NO_PRICE
    assert trade("FD", "H1", sessions([100, 100, 100]), 1, RATES, 1.0)["status"] == FLAT
    assert trade("FD", "H1", sessions([None, 100, 100]), 1, RATES, 1.0)["status"] == NO_SIGNAL
    assert trade("FD", "H5", sessions([100, 150, 150]), 1, RATES, 1.0) is None


def test_newey_west_lag_zero_is_the_plain_error_and_overlap_widens_it():
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    plain = summary.newey_west_se(values, 0)
    assert plain == pytest.approx((sum((v - 3.5) ** 2 for v in values) / 6 / 6) ** 0.5)
    assert summary.newey_west_se(values, 4) > plain
    assert summary.newey_west_se([1.0], 0) is None


def row(net, side=1, exit_="2020-01-02"):
    return {"status": "taken", "side": side, "gross": side * net, "charges": 0.0, "pads": 0.0, "net": net,
            "exit": exit_}  # fmt: skip


def test_random_signs_keep_the_long_count_and_are_seeded():
    rows = [row(10.0 * (i % 3) - 5, 1 if i % 2 else -1) for i in range(30)]
    p = summary.random_sign_p(rows, 5.0)
    assert p == summary.random_sign_p(rows, 5.0) and 0.0 <= p <= 1.0


def base(**changes):
    r = {"holm": True, "mean_net_pad2": 1.0, "p_sign": 0.05, "halves": {"2019-2021": 1.0, "2022-2024": 1.0}}
    return {**r, **changes}


@pytest.mark.parametrize(("changes", "expected"),
                         [({}, True), ({"holm": False}, False), ({"mean_net_pad2": 0.0}, False),
                          ({"p_sign": 0.11}, False), ({"p_sign": None}, False),
                          ({"halves": {"2019-2021": 1.0, "2022-2024": -1.0}}, False),
                          ({"halves": {"2019-2021": None, "2022-2024": 1.0}}, False)])  # fmt: skip
def test_nomination_needs_all_four_conditions(changes, expected):
    assert summary.eligible(base(**changes)) is expected


def test_the_family_runs_holm_over_six_and_reports_each():
    rows = [row(100.0 + i % 7, exit_=f"20{19 + i % 6}-01-02") for i in range(60)]
    runs = {f"EDGE2-F6-{s}-{h}": {"pad1": rows, "pad2": rows, "hist": rows} for s in ("FD", "FL", "CD")
            for h in ("H1", "H5")}  # fmt: skip
    found = summary.family(runs)
    assert len(found) == 6 and all(r["holm"] for r in found.values())
    assert found["EDGE2-F6-FD-H1"]["p_sign"] == 1.0  # all long: every random series is the same series
    assert summary.nominated(found) == []


def test_the_seal_refuses_held_out_dates(monkeypatch):
    import study_f6

    monkeypatch.setattr(study_f6.data, "sessions", lambda days: pytest.fail("must not read"))
    with pytest.raises(SealBroken):
        study_f6.loaded(date(2025, 1, 2), held_out_open=False)
