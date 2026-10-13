"""Story B7 criteria 2 and 3: the validation report on 20 fixture days equals a hand computation, and a strategy
whose live features are not validated cannot reach status paper."""

import json
from datetime import date, datetime, time, timedelta

import pytest
from feature_fixtures import make_panel

from fno.research_data.quote_snapshots import CutoffSnapshot
from fno.research_engine.features import DecisionContext, Feature, ResearchData
from fno.research_engine.live_gate import (
    LiveFeaturesNotValidated,
    require_validated,
    unvalidated,
    validated_from_reports,
)
from fno.research_engine.live_validation import LiveUseRule, validate

START = date(2026, 11, 2)
DAYS = [START + timedelta(days=i) for i in range(22)]  # 20 recorded days, then one unrecorded and one off-panel
CLOSE = [2.0] * 10 + [-1.0] * 10
LIVE = [2.5] * 8 + [None, -0.5] + [-1.25] * 9 + [0.5]


def snapshot(day):
    return CutoffSnapshot(day, datetime.combine(day, time(14, 56)), 20000.0, None, ())


class Known(Feature):
    def __init__(self, name, values):
        self.name, self.values = name, dict(zip(DAYS, values))

    def value(self, data, decision_day, context):
        return self.values[decision_day]


def report(live=LIVE, close=CLOSE, recorded=20, rule=None):
    panel = make_panel(DAYS[:21], [20000.0] * 21)  # day 22 is not in the panel yet
    snapshots = {d: snapshot(d) for d in DAYS[:recorded]} | {DAYS[21]: snapshot(DAYS[21])}  # day 21 unrecorded
    data = ResearchData(panel, (), snapshots)
    context = DecisionContext(date(2026, 12, 29), START, START)
    return validate(
        Known("live", [*live, 9.0, 9.0]), Known("close", [*close, 9.0, 9.0]), data, DAYS, lambda d: context, rule
    )


def test_the_report_equals_the_hand_computation():
    """Conditions differ on days 9, 10 and 20 (live None, live -0.5 against close 2, live 0.5 against close -1):
    agreement 17/20 = 0.85. Numeric differences on 19 days: 8 x 0.5 + 2.5 + 9 x 0.25 + 1.5 = 10.25, mean 10.25 / 19,
    largest 2.5. Live available 19/20. Not validated: 0.85 is below 0.90."""
    summary = report().summary()
    assert summary["days"] == 20  # the unrecorded day and the day the panel lacks are left out
    assert summary["agreement"] == 0.85 and summary["live_available"] == 0.95
    assert summary["mean_abs_difference"] == pytest.approx(10.25 / 19) and summary["largest_abs_difference"] == 2.5
    assert summary["disagreement_days"] == [DAYS[8].isoformat(), DAYS[9].isoformat(), DAYS[19].isoformat()]
    assert summary["validated"] is False


def test_the_use_rule_passes_at_twenty_days_and_ninety_percent():
    live = LIVE[:9] + [1.0] + LIVE[10:19] + [-0.5]  # only day 9 (None) still differs: 19/20 = 0.95
    assert report(live).validated is True
    assert report(live, recorded=19).validated is False  # 19 days: too few
    assert report(live, rule=LiveUseRule(min_agreement=0.96)).validated is False  # the owner can be stricter


def test_a_live_feature_that_is_never_computed_cannot_pass_vacuously():
    never = report([None] * 20, [-1.0] * 20)
    assert never.agreement == 1.0 and never.available == 0.0 and never.validated is False


def test_an_unvalidated_live_feature_keeps_a_strategy_from_paper(tmp_path):
    (tmp_path / "f1.json").write_text(json.dumps({"live_feature": "F1_live", "validated": True}))
    (tmp_path / "f2.json").write_text(json.dumps({"live_feature": "F2_live", "validated": False}))
    validated = validated_from_reports(tmp_path)
    assert unvalidated(["F1_live", "F2_live", "F3_live"], validated) == ["F2_live", "F3_live"]
    with pytest.raises(LiveFeaturesNotValidated, match="cannot reach status paper"):
        require_validated("sc_when_premium_high", ["F1_live", "F2_live"], validated)
    require_validated("sc_when_premium_high", ["F1_live"], validated)  # every live feature validated: allowed


def test_the_wired_validation_runs_on_the_repository_and_reports_no_days_yet():
    """No A4 day is committed yet (and the panel ends 12 Oct 2026): 0 days, not validated, never an error."""
    from fno.composition import run_live_validation
    from fno.config import load_app_config

    summary = run_live_validation(load_app_config(), "F1_live_atm_iv_minus_rv20", date(2026, 10, 12)).summary()
    assert (summary["days"], summary["validated"]) == (0, False)
