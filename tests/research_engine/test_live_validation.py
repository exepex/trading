"""Story B7 criteria 2 and 3: the validation report on 20 fixture days equals a hand computation, and a strategy
whose live features are not validated cannot reach status paper."""

import json
from datetime import date, datetime, time, timedelta

import pytest
from feature_fixtures import make_panel

from fno.research_data.quote_snapshots import CutoffSnapshot
from fno.research_engine.features import DecisionContext, Feature, ResearchData
from fno.research_engine.live_gate import LiveFeaturesNotValidated, reports_from_folder, require_validated, unvalidated
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
    """Decision states differ on days 9, 10 and 20 (live None against close 2, live -0.5 against close 2, live 0.5
    against close -1):
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
    assert never.numbers == (20, 0.0, 0.0) and never.validated is False  # None is not "at most zero"


def test_agreement_compares_the_policys_three_decision_states():
    """Judge 44's case: close -1 on all 20 days; live None on 2, +0.5 on 2, -1 on 16. P5 trades a butterfly on a close
    of -1 but nothing on a live None, so only the 16 days agree: 0.80, not validated (the old measure said 0.90)."""
    judged = report([None, None, 0.5, 0.5] + [-1.0] * 16, [-1.0] * 20)
    assert judged.numbers == (20, 0.8, 0.9) and judged.validated is False
    assert report([None] * 20, [None] * 20).numbers == (20, 1.0, 0.0)  # both unknown agree; availability still fails


def write_reports(folder, **reports):
    for name, summary in reports.items():
        (folder / f"{name}.json").write_text(json.dumps(summary))
    return reports_from_folder(folder)


def test_the_gate_rechecks_every_report_under_the_strategys_frozen_rule(tmp_path):
    live = LIVE[:9] + [1.0] + LIVE[10:19] + [-0.5]  # 19 of 20 agree: 0.95
    passing, ninety = report(live).summary(), report(LIVE[:9] + [1.0] + LIVE[10:]).summary()  # 0.95 and 0.90
    reports = write_reports(tmp_path, F1_live={**passing, "live_feature": "F1_live"},
                            F2_live={**ninety, "live_feature": "F2_live"})  # fmt: skip
    default, strict = LiveUseRule(), LiveUseRule(min_agreement=0.95)
    assert unvalidated(["F1_live", "F2_live", "F3_live"], reports, default) == ["F3_live"]  # no report: refused
    assert unvalidated(["F1_live", "F2_live"], reports, strict) == ["F2_live"]  # 0.90 fails a 95% strategy
    with pytest.raises(LiveFeaturesNotValidated, match="cannot reach status paper"):
        require_validated("sc_when_premium_high", ["F1_live", "F2_live"], reports, strict)
    require_validated("sc_when_premium_high", ["F1_live"], reports, strict)


def test_a_forged_flag_or_summary_does_not_pass_the_gate(tmp_path):
    forged = {**report().summary(), "live_feature": "F1_live", "validated": True, "agreement": 1.0, "days": 99}
    reports = write_reports(tmp_path, F1_live=forged)
    assert unvalidated(["F1_live"], reports, LiveUseRule()) == ["F1_live"]  # recomputed from the per-day values: 0.85


def test_each_compared_day_carries_its_capture_time():
    rows = report().summary()["comparisons"]
    assert rows[0]["captured_at"] == f"{DAYS[0].isoformat()}T14:56:00"


def test_the_wired_validation_runs_on_the_repository_and_reports_no_days_yet():
    """No A4 day is committed yet (and the panel ends 12 Oct 2026): 0 days, not validated, never an error."""
    from fno.composition import run_live_validation
    from fno.config import load_app_config

    summary = run_live_validation(load_app_config(), "F1_live_atm_iv_minus_rv20", date(2026, 10, 12)).summary()
    assert (summary["days"], summary["validated"]) == (0, False)
