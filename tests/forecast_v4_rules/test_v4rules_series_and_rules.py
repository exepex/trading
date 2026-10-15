"""Story G7: the v4 series (closes, close-proxy RV, V6 outcomes, A16 rows) and the two rule forecasters."""

import math
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from fno.forecast_v4.terms import V1_INTRADAY_METHOD
from fno.forecast_v4_rules.baselines import MISSING, NOT_ELIGIBLE, OK, BaseRate, Ewma, Value
from fno.forecast_v4_rules.rules import big_move_probability, v1_close_blend, v6_ewma_t4
from fno.forecast_v4_rules.series import (
    DayValue,
    big_move_outcomes,
    close_proxy_rv,
    closes_rows,
    live_intraday_rv,
    regular_closes,
    vix_closes,
)
from fno.intraday.realised_vol import QuoteSnapshotRv15m
from fno.intraday.rv_table import PATTERN

ROOT = Path(__file__).resolve().parents[2]
CLOSES = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"
HEADER = "date,session,underlying,vix,index_file,index_sha256\n"


DISCLOSED_THROUGH = date(2026, 10, 14)  # the counts response 127 disclosed were taken on the panel up to this session


def committed(through: date = DISCLOSED_THROUGH):
    """The committed panel's closes up to `through`: the panel gains a session every day, so a fixed count needs a
    fixed end (the 15 Oct session made V6a's count 2,410)."""
    return [c for c in regular_closes(closes_rows(CLOSES.read_text())) if c.day <= through]


def test_committed_closes_reproduce_the_disclosed_v6_counts():
    closes = committed()
    v6a, v6b = big_move_outcomes(closes, 1), big_move_outcomes(closes, 5)
    assert (sum(o.value for o in v6a), len(v6a)) == (100, 2409)
    assert (sum(o.value for o in v6b), len(v6b)) == (331, 2405)


def test_judge_127_hand_values_from_the_committed_closes():
    closes = committed()
    ewma, today = Ewma(close_proxy_rv(closes)), date(2026, 10, 15)
    assert ewma.variance(today) == pytest.approx(7.7224e-05, rel=1e-4)
    p1, p5 = v6_ewma_t4(ewma.forecast(today, 1))
    assert (round(p1.value, 4), round(p5.value, 4)) == (0.0323, 0.1515)
    assert BaseRate(big_move_outcomes(closes, 1)).forecast(today).value == pytest.approx(20 / 750)


def closes_from_returns(returns, start=date(2024, 1, 1)):
    level, out = 100.0, [DayValue(start, 100.0)]
    for i, r in enumerate(returns, start=1):
        level *= math.exp(r)
        out.append(DayValue(start + timedelta(days=i), level))
    return out


def test_a_move_of_two_percent_counts_and_just_under_does_not():
    outcomes = big_move_outcomes(closes_from_returns([0.0200001, -0.0199999, -0.0200001]), 1)
    assert [o.value for o in outcomes] == [True, False, True]
    assert outcomes[0].resolved_on == date(2024, 1, 2)  # V6a resolves at t+1's close


def test_v6b_looks_at_the_next_five_returns_and_resolves_at_the_fifth():
    outcomes = big_move_outcomes(closes_from_returns([0, 0, 0, 0, 0.025, 0]), 5)
    assert [o.value for o in outcomes] == [True, True] and outcomes[0].resolved_on == date(2024, 1, 6)
    assert big_move_outcomes(closes_from_returns([0.01] * 4), 5) == []  # empty: no full window yet


def test_special_and_muhurat_sessions_sit_inside_the_next_regular_return():
    text = HEADER + "2024-01-19,regular,100,15,f,s\n2024-01-20,special,110,15,f,s\n2024-01-22,regular,101,15,f,s\n"
    closes = regular_closes(closes_rows(text))
    assert [c.day for c in closes] == [date(2024, 1, 19), date(2024, 1, 22)]
    assert close_proxy_rv(closes)[0].value == pytest.approx(math.log(1.01) ** 2)
    assert [v.value for v in vix_closes(closes_rows(text))] == [15.0, 15.0]


def test_zero_return_is_a_zero_rv_kept_as_observed():
    assert close_proxy_rv(closes_from_returns([0.0]))[0].value == 0.0


def test_a16_rows_void_is_no_value_and_candle_backfill_is_never_read():
    rows = [
        {"session": "2026-10-16", "status": "ok", "rv_session": "0.0001", "first_seen_at": "2026-10-16T10:05:00+00:00",
         "method": V1_INTRADAY_METHOD},
        {"session": "2026-10-19", "status": "void", "rv_session": "", "first_seen_at": "2026-10-19T10:05:00+00:00",
         "method": V1_INTRADAY_METHOD},
    ]  # fmt: skip
    found = live_intraday_rv(rows)
    assert [r.value for r in found] == [0.0001, None]
    assert found[0].first_seen_at == datetime.fromisoformat("2026-10-16T10:05:00+00:00")
    assert PATTERN == "rv/*/nifty_rv_*.csv"  # A16b writes rv-candle/: a different folder (decision 56)


def test_t4_tail_probability_matches_the_t_table():
    s = 0.02 * math.sqrt(2) / 2.776445  # the 97.5% point of t(4): two-sided 5%
    assert big_move_probability(s**2) == pytest.approx(0.05, abs=1e-5)


def test_rule_forecasters_pass_on_missing_inputs_and_blend_two_values():
    assert v6_ewma_t4(Value(NOT_ELIGIBLE)) == (Value(NOT_ELIGIBLE), Value(NOT_ELIGIBLE))
    assert v1_close_blend(Value(OK, 2e-4), Value(OK, 1e-4)).value == pytest.approx(1.5e-4)
    assert v1_close_blend(Value(OK, 2e-4), Value(NOT_ELIGIBLE)) == Value(MISSING)
    p1 = v6_ewma_t4(Value(OK, 1e-4))[0].value
    assert v6_ewma_t4(Value(OK, 1e-4))[1].value == pytest.approx(1 - (1 - p1) ** 5)


def test_v1_reads_only_the_pinned_a16_method():
    first_seen = "2026-10-16T10:05:00+00:00"
    v1 = {"session": "2026-10-16", "status": "ok", "rv_session": "0.0001", "first_seen_at": first_seen,
          "method": V1_INTRADAY_METHOD}  # fmt: skip
    newer = dict(v1, rv_session="0.0009", method="rv-quote-5m-v2")  # same date, a new A16 sampling method
    found = live_intraday_rv([newer, v1, dict(v1, session="2026-10-19", method="")])
    assert [(r.day, r.value) for r in found] == [(date(2026, 10, 16), 0.0001)]  # only the pinned method's row


def test_the_pinned_method_is_a16s_live_method():
    assert QuoteSnapshotRv15m.method == V1_INTRADAY_METHOD
