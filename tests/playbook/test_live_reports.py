"""The gate's reports (B7 follow-up of judge 44): a committed report counts only if its per-day values equal a fresh
recomputation, so hand-edited values cannot pass the gate."""

import copy

import pytest

from fno.playbook.live_reports import CommittedLiveReports, RecomputedLiveReports
from fno.research_engine.live_gate import report_passes
from fno.research_engine.live_validation import LiveUseRule
from fno.research_engine.results_file import results_json

from .builders import FixedReports, report

F1 = "F1_live_atm_iv_minus_rv20"


def test_committed_reports_are_read_from_the_folder(tmp_path):
    (tmp_path / f"{F1}.json").write_text(results_json(report(F1, 20)))
    assert CommittedLiveReports(tmp_path).report(F1)["comparisons"][0]["day"] == "2026-11-01"
    assert CommittedLiveReports(tmp_path / "missing").report(F1) is None


def test_the_gate_reads_the_recomputation_with_its_later_days():
    later = report(F1, 20, days=25)  # the recomputation runs on more recorded days than the committed report
    reports = RecomputedLiveReports(FixedReports({F1: report(F1, 20)}), lambda name: later)
    assert reports.report(F1) == later


def disagreeing_days(days: int, bad: set[int]) -> dict:
    """A report over `days` days where the days numbered in `bad` disagree."""
    result = report(F1, days, days=days)
    for n in bad:
        result["comparisons"][n].update(close=-1.0, agrees=False)
    return result


@pytest.mark.parametrize(
    "bad",
    [{3, 9, 15, 22, 24}, {20, 21, 22, 23, 24}],  # cherry-picked middle days; a truncated end
)
def test_removing_bad_days_from_the_committed_report_does_not_pass_the_gate(bad):
    """Judge 67: 25 recorded days, 5 disagree (80%); the committed report without those 5 rows (100%) must not pass."""
    rule = LiveUseRule()
    recorded = disagreeing_days(25, bad)
    committed = copy.deepcopy(recorded)
    committed["comparisons"] = [row for n, row in enumerate(recorded["comparisons"]) if n not in bad]
    assert report_passes(committed, rule)  # what the old gate decided on
    used = RecomputedLiveReports(FixedReports({F1: committed}), lambda name: recorded).report(F1)
    if bad == {20, 21, 22, 23, 24}:  # a shorter report is a report made earlier: the gate reads all 25 days
        assert used == recorded and not report_passes(used, rule)
    else:  # a gap in the record is refused outright: no report, no gate pass
        assert used is None


def test_no_committed_report_means_none_without_recomputing():
    def never(name):
        raise AssertionError("recomputed without a committed report")

    assert RecomputedLiveReports(FixedReports({}), never).report(F1) is None


def test_the_full_honest_report_passes():
    honest = report(F1, 20)
    used = RecomputedLiveReports(FixedReports({F1: honest}), lambda name: report(F1, 20)).report(F1)
    assert used == honest and report_passes(used, LiveUseRule())


@pytest.mark.parametrize("removed", [0, 7])  # the first and a middle committed day (a missing end = an older report)
def test_a_committed_report_with_a_missing_day_is_refused_as_the_red_teams_record(removed):
    """Judge 67 / orchestrator: the committed report equals the recomputation day for day, no gap."""
    committed = report(F1, 20)
    del committed["comparisons"][removed]
    assert RecomputedLiveReports(FixedReports({F1: committed}), lambda name: report(F1, 20)).report(F1) is None
