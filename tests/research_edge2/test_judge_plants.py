"""Judge 642 m1: one test for each plant that survived round 1 (RC1 drawing from every cycle and its >= boundary, the
gate's traded-volume filter, the code hash's files, the EWMA lambda, F6's seal-day exit filter and its H5 lag)."""

import hashlib
import math
from datetime import date

import pytest
from f1study import stats
from f1study.gate import LAMBDA, ewma_sigma, traded_pairs
from f6study import summary as f6_summary
from f6study.trades import FuturesRates, run

from .f1_fakes import EXPIRY, quote
from .test_f6 import bar, sessions


def row(net, status="taken", i=0):
    return {"net": net, "status": status, "expiry": f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}", "index": "NIFTY"}


def test_rc1_draws_from_every_cycle_not_only_the_taken_ones():
    rows = [row(100.0, i=0), row(-100.0, i=1)] + [row(0.0, "no_trade_cap", i) for i in range(2, 20)]
    p = stats.random_gate_p(rows, 2, 100.0)
    assert p is not None and 0.4 < p < 0.6  # 18 of the 37 draws holding a taken trade hold only the +100 one


def test_rc1_counts_an_equal_mean_as_reaching_the_gated_mean():
    rows = [row(50.0, i=i) for i in range(10)]
    assert stats.random_gate_p(rows, 3, 50.0) == 1.0


def test_the_gate_pairs_only_strikes_whose_call_and_put_both_traded():
    quotes = [quote(22000, "CE", 100.0), quote(22000, "PE", 90.0), quote(22050, "CE", 70.0, volume=0),
              quote(22050, "PE", 110.0)]  # fmt: skip
    assert traded_pairs(quotes, EXPIRY) == {22000.0: (100.0, 90.0)}


def test_the_f1_code_hash_covers_the_package_and_the_study_script():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "research" / "edge2" / "study.py"
    spec = importlib.util.spec_from_file_location("edge2_f1_study", path)  # not EDGE1's study.py on the same path
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)
    files = sorted((study.HERE / "f1study").glob("*.py")) + [study.HERE / "study.py"]
    assert study.code_hash() == hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()


def test_the_ewma_uses_lambda_094():
    returns = [0.01] * 20 + [0.03, -0.02]
    closes = [100.0]
    for r in returns:
        closes.append(closes[-1] * math.exp(r))
    v = sum(r * r for r in returns[:20]) / 20
    for r in returns[20:]:
        v = 0.94 * v + 0.06 * r * r
    assert LAMBDA == 0.94 and ewma_sigma(closes) == pytest.approx(math.sqrt(252 * v))


def test_f6_drops_trades_that_exit_after_the_seal_day():
    s = sessions([100, 150, 200, 250, 300], bars=[(bar(),)] * 5)
    rows = run("FD", "H1", s, FuturesRates(), 1.0, exit_by=s[2].day)
    assert [r["exit"] for r in rows] == [s[2].day.isoformat()]


def test_f6_h5_uses_newey_west_lag_4():
    nets = [100.0, 300.0, 250.0, -50.0, 400.0, 350.0, 0.0, -100.0, 200.0, 150.0]
    rows = [{"status": "taken", "side": 1, "gross": n, "charges": 0.0, "pads": 0.0, "net": n,
             "exit": f"2020-01-{i + 1:02d}"} for i, n in enumerate(nets)]  # fmt: skip
    found = f6_summary.describe(rows, rows, rows, "H5")
    assert found["se"] == pytest.approx(f6_summary.newey_west_se(nets, 4))
    assert found["se"] != pytest.approx(f6_summary.newey_west_se(nets, 0))
    assert f6_summary.describe(rows, rows, rows, "H1")["se"] == pytest.approx(f6_summary.newey_west_se(nets, 0))


def test_the_fakes_date_is_fixed():
    assert date(2024, 3, 7) == EXPIRY
