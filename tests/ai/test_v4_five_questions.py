"""Story G11 criteria C2-C4: the five v4 questions in their own forms and measures.

- C2: V1 and V2 answers are variances (squared log returns), finite, above 0 and at most 1 (above 1 is a unit error);
  V6a, V6b and V7 are probabilities in [0, 1]; null is no forecast; a missing answer is that question's problem only.
- C3: Hybrid's primary baseline is G8's own series, so V1 switches one way to HAR intraday exactly as G8 scores it.
- C4: each point question's history is in its own measure (V1 intraday, V2 close proxy), dated before the day only;
  Book 3 is shown no rule or baseline value."""

import math
from datetime import date, timedelta

import pytest

from fno.ai.answer import VARIANCE_CAP, check_answer
from fno.ai.envelope import Envelope
from fno.ai.v4_book_inputs import V4BookInputs
from fno.ai.v4_input import PRIMARY
from fno.ai.versions import current_version
from fno.constants import (
    BOOK2_HYBRID,
    BOOK3_AI,
    FORECAST_PROTOCOL_V4,
    V1_RV_1S,
    V2_RV_5S,
    V4_BASELINE_HAR_DAILY,
    V4_BASELINE_HAR_INTRADAY,
    V4_SLOT_RULES,
    V6_BIG_MOVE_1S,
    V7_VIX_UP_5S,
)
from fno.forecast_scoring.v4.g7_series import G7Series
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_scoring.v4.records import Registration, SlotRegistry
from fno.forecast_v4_rules import records
from tests.ai.test_v4_input import DAY, QUESTIONS, a_pack

LABELS = {"book": BOOK3_AI, "day": DAY.isoformat(), "export_sha256": "e" * 64, "pack_sha256": "d" * 64,
          "version": "book3_ai/v2"}  # fmt: skip


def answer(**entries):
    base = {V1_RV_1S: {"value": 9e-05, "reason": "r"}, V2_RV_5S: {"value": 4e-04, "reason": "r"},
            V6_BIG_MOVE_1S: {"probability": 0.05, "reason": "r"},
            "v6_abs_move_2pct_within_5_sessions": {"probability": 0.2, "reason": "r"},
            V7_VIX_UP_5S: {"probability": 0.47, "reason": "r"}}  # fmt: skip
    return {**LABELS, "model_reported": "m", "forecasts": base | entries}


def problems(**entries):
    return check_answer(answer(**entries), LABELS, None, QUESTIONS).problems


def test_good_answers_are_kept_by_kind():
    checked = check_answer(answer(), LABELS, None, QUESTIONS)
    assert checked.probabilities[V1_RV_1S] == 9e-05 and checked.probabilities[V7_VIX_UP_5S] == 0.47
    assert not any(checked.problems.values())


@pytest.mark.parametrize(
    ("question", "entry", "why"),
    [(V1_RV_1S, {"value": 0, "reason": "r"}, "variance above 0"),
     (V1_RV_1S, {"value": -1e-05, "reason": "r"}, "variance above 0"),
     (V1_RV_1S, {"value": math.nan, "reason": "r"}, "variance above 0"),
     (V2_RV_5S, {"value": 15.2, "reason": "vol points"}, "at most 0.05"),
     (V1_RV_1S, {"value": 0.64, "reason": "a 0.8% day in percent squared"}, "at most 0.01"),
     (V1_RV_1S, {"value": 0.0225, "reason": "annualised"}, "at most 0.01"),
     (V1_RV_1S, {"value": 10**400, "reason": "huge"}, "variance above 0"),
     (V7_VIX_UP_5S, {"probability": 10**400, "reason": "huge"}, "probability must be"),
     (V1_RV_1S, {"probability": 0.5, "reason": "r"}, '"value"'),
     (V7_VIX_UP_5S, {"probability": 1.2, "reason": "r"}, "probability must be"),
     (V7_VIX_UP_5S, {"value": 0.4, "reason": "r"}, '"probability"')],
)  # fmt: skip
def test_bad_answers_are_refused_for_that_question_only(question, entry, why):
    found = problems(**{question: entry})
    assert why in found[question] and sum(bool(p) for p in found.values()) == 1


def test_the_boundaries_of_each_kind():
    assert problems(**{V1_RV_1S: {"value": VARIANCE_CAP[V1_RV_1S], "reason": "r"}})[V1_RV_1S] == ""
    assert "at most 0.01" in problems(**{V1_RV_1S: {"value": 0.010001, "reason": "r"}})[V1_RV_1S]
    assert problems(**{V2_RV_5S: {"value": 0.05, "reason": "r"}})[V2_RV_5S] == ""
    assert "at most 0.05" in problems(**{V2_RV_5S: {"value": 0.050001, "reason": "r"}})[V2_RV_5S]
    assert problems(**{V7_VIX_UP_5S: {"probability": 0, "reason": "r"}})[V7_VIX_UP_5S] == ""
    assert problems(**{V7_VIX_UP_5S: {"probability": 1, "reason": "r"}})[V7_VIX_UP_5S] == ""


def test_null_is_no_forecast_and_a_malformed_entry_is_that_questions_problem():
    checked = check_answer(answer(**{V1_RV_1S: {"value": None, "reason": "no intraday data"}}), LABELS, None, QUESTIONS)
    assert checked.probabilities[V1_RV_1S] is None and checked.problems[V1_RV_1S] == ""
    assert "must be" in problems(**{V2_RV_5S: {}})[V2_RV_5S]


def test_a_variance_envelope_keeps_its_span_inside_at_significant_digits():
    envelope = Envelope.span({V1_RV_1S: [1.23456789e-04]}, 0.10, 0.25)
    low, high = envelope.bounds[V1_RV_1S]
    assert low <= 1.23456789e-04 * 0.75 and high >= 1.23456789e-04 * 1.25 and low > 0
    assert envelope.problem(V1_RV_1S, 1.23456789e-04) == "" and "outside" in envelope.problem(V1_RV_1S, high * 1.01)


class Rules(SlotRegistry):
    def registered(self):
        return {(V1_RV_1S, V4_SLOT_RULES): Registration("v1_close_blend", DAY - timedelta(days=10))}


def v1_inputs(tmp_path, daily, intraday, closes_text=""):
    """G7-format live rows of daily and intraday HAR for V1 (value per day; None writes no row)."""
    v4 = tmp_path / "v4"
    audit = dict(label=records.LIVE, kind="baseline", slot="", method_sha256="b" * 64, inputs_sha256="c" * 64,
                 made_at="2026-10-26T08:50:00+00:00")  # fmt: skip
    for name, values in ((V4_BASELINE_HAR_DAILY, daily), (V4_BASELINE_HAR_INTRADAY, intraday)):
        rows = [records.record(d, V1_RV_1S, "ok", v, **audit) for d, v in sorted(values.items()) if v is not None]
        records.write(v4, name, V1_RV_1S, rows)
    return V4BookInputs(tmp_path, Rules(), ForecastFiles(v4), G7Series(closes_text, list))


def test_v1s_primary_baseline_switches_one_way_to_har_intraday(tmp_path):
    first, second, third = DAY - timedelta(days=2), DAY - timedelta(days=1), DAY
    inputs = v1_inputs(tmp_path, {first: 1e-04, second: 2e-04, third: 3e-04}, {second: 5e-05})
    assert inputs._rules(first, [V1_RV_1S])[V1_RV_1S][PRIMARY] == 1e-04  # daily HAR before intraday is eligible
    assert inputs._rules(second, [V1_RV_1S])[V1_RV_1S][PRIMARY] == 5e-05  # intraday HAR from its first day
    assert inputs._rules(third, [V1_RV_1S])[V1_RV_1S][PRIMARY] is None  # never back to daily HAR: no primary


def closes_text(days):
    rows = ["date,session,underlying,vix,index_file,index_sha256"] + [
        f"{d.isoformat()},regular,{c},{12.0 + i / 10},ind.csv,{'a' * 64}" for i, (d, c) in enumerate(days)]  # fmt: skip
    return "\n".join(rows) + "\n"


def test_v2s_history_is_the_close_proxy_before_the_day_only(tmp_path):
    days = [(DAY - timedelta(days=n), 25000.0 + 37 * (n % 5)) for n in (7, 6, 5, 4, 1, 0)]  # weekdays, with DAY itself
    inputs = v1_inputs(tmp_path, {}, {}, closes_text(sorted(days)))
    shown = inputs._history(DAY, [V2_RV_5S, V6_BIG_MOVE_1S])
    closes = [c for _, c in sorted(days)]
    expected = [math.log(b / a) ** 2 for a, b in zip(closes, closes[1:], strict=False)][
        :-1
    ]  # DAY's own return left out
    assert list(shown) == [V2_RV_5S] and shown[V2_RV_5S]["rv_s"] == pytest.approx(expected, rel=1e-5)
    assert all(date.fromisoformat(d) < DAY for d in shown[V2_RV_5S]["dates"])


def test_v1s_history_is_a16s_intraday_rv_with_void_sessions_kept_void(tmp_path):
    class Series:
        def close_proxy_rv(self):
            return {}

        def intraday_rv(self):
            return {DAY - timedelta(days=2): 9e-05, DAY - timedelta(days=1): None, DAY: 1e-04}

    inputs = V4BookInputs(tmp_path, Rules(), ForecastFiles(tmp_path / "v4"), Series())
    assert inputs._history(DAY, [V1_RV_1S])[V1_RV_1S] == {
        "dates": [(DAY - timedelta(days=2)).isoformat(), (DAY - timedelta(days=1)).isoformat()],
        "rv_s": [9e-05, None],
    }
    assert inputs._history(DAY, [V6_BIG_MOVE_1S]) == {}  # no point question asked: no history


def test_book3_is_shown_no_rule_or_baseline_value(tmp_path):
    inputs = v1_inputs(tmp_path, {DAY: 1e-04}, {})
    built = inputs.build(current_version(BOOK3_AI, FORECAST_PROTOCOL_V4), DAY, [V1_RV_1S], a_pack(), "d" * 64)
    hybrid = inputs.build(current_version(BOOK2_HYBRID, FORECAST_PROTOCOL_V4), DAY, [V1_RV_1S], a_pack(), "d" * 64)
    assert "rules" not in built and hybrid["rules"]["by_question"][V1_RV_1S][PRIMARY] == 1e-04
