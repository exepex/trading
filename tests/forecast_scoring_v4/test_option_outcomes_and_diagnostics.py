"""Story G7b completion, part e: V4's and V5's outcomes reach G8 from G7b's stored records (void, resolved, unresolved,
a day outside the sessions); the report prints protocol 1.4 and 1.5's notes and its descriptive lines (the pack / EOD
IV30 median drift, and the two RV level lines as a ratio of sums, never a median of daily ratios)."""

from datetime import date, timedelta

import pytest

from fno.constants import V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.diagnostic_lines import (
    IV30_LABEL,
    LEVEL_LABEL,
    W8_LABEL,
    diagnostic_lines,
    level_line,
    median_line,
)
from fno.forecast_scoring.v4.g7_series import StoredOptionOutcomes
from fno.forecast_scoring.v4.outcomes import VOID_PLACEHOLDER, OptionOutcomeSource, OutcomeSeries, SeriesOutcomes
from fno.forecast_scoring.v4.render import QUESTION_NOTES, report_json, report_lines
from fno.forecast_scoring.v4.scoring import STATUS_NO_DATA, QuestionReport
from fno.forecast_v4_rules.option_history import DayOutcome

START = date(2026, 10, 19)
DAYS = [START + timedelta(n) for n in range(5)]  # Mon-Fri
SESSIONS = [(d, 25000.0 + 10 * i, 12.0 + i) for i, d in enumerate(DAYS)]


class FiveSessions(OutcomeSeries):
    def sessions(self):
        return SESSIONS

    def close_proxy_rv(self):
        return {}

    def big_move_outcomes(self, question):
        return {}

    def vix_up_outcomes(self):
        return {}

    def intraday_rv(self):
        return {}


class Options(OptionOutcomeSource):
    def __init__(self, by_question):
        self.by_question = by_question

    def outcomes(self, question):
        return self.by_question.get(question, {})


class History:
    def v4(self):
        return {DAYS[0]: DayOutcome(True, DAYS[4]), DAYS[1]: DayOutcome(None, DAYS[1])}

    def v5(self):
        return {DAYS[2]: DayOutcome(False, DAYS[4])}


def test_stored_outcomes_route_v4_and_v5_to_their_own_history_and_keep_void_as_none():
    stored = StoredOptionOutcomes(History())
    assert stored.outcomes(V4_RV_BELOW_WEEKLY_IV) == {DAYS[0]: True, DAYS[1]: None}
    assert stored.outcomes(V5_INSIDE_STRADDLE) == {DAYS[2]: False}


def test_v4_and_v5_outcomes_are_resolved_void_or_absent_and_carry_the_next_session_s_regime():
    off_calendar, last = date(2026, 10, 25), DAYS[4]  # a Sunday; the last session has no next session yet
    options = Options({V4_RV_BELOW_WEEKLY_IV: {DAYS[0]: True, DAYS[1]: None, off_calendar: False, last: True},
                       V5_INSIDE_STRADDLE: {DAYS[2]: False}})  # fmt: skip
    found = SeriesOutcomes(FiveSessions(), options).outcomes(V4_RV_BELOW_WEEKLY_IV)
    assert set(found) == {DAYS[0], DAYS[1]}  # DAYS[2] and DAYS[3] unresolved: absent
    assert found[DAYS[0]].value is True and found[DAYS[0]].void is False and found[DAYS[0]].vix == 13.0
    assert found[DAYS[1]].void is True and found[DAYS[1]].value == VOID_PLACEHOLDER
    assert found[DAYS[1]].log_return == pytest.approx(0.0004, rel=0.01)  # log(25020 / 25010)
    v5 = SeriesOutcomes(FiveSessions(), options).outcomes(V5_INSIDE_STRADDLE)
    assert list(v5) == [DAYS[2]] and v5[DAYS[2]].value is False


def test_without_option_records_v4_and_v5_have_no_outcomes():
    assert SeriesOutcomes(FiveSessions()).outcomes(V4_RV_BELOW_WEEKLY_IV) == {}
    assert SeriesOutcomes(FiveSessions()).outcomes(V5_INSIDE_STRADDLE) == {}


def days(n):
    return [START + timedelta(i) for i in range(n)]


def test_the_iv30_line_is_the_median_of_paired_ratios_and_its_recent_drift():
    pairs = [(d, 1.0 if i < 15 else 1.2, 1.0) for i, d in enumerate(days(30))] + [(date(2027, 1, 1), None, 1.0)]
    line = median_line(IV30_LABEL, pairs)
    assert line.startswith(f"{IV30_LABEL}: 30 paired day(s); median ratio 1.1000, latest 20 1.2000, drift 0.1000")


def test_the_rv_lines_are_a_ratio_of_sums_not_a_median_of_daily_ratios():
    pairs = [(DAYS[0], 4.0, 1.0), (DAYS[1], 1.0, 1.0), (DAYS[2], 1.0, 2.0)]  # median of ratios 1.0, sums 6 / 4
    pairs += [(DAYS[3], None, 1.0), (DAYS[4], 1.0, 0.0)]  # unpaired: a missing side, a zero denominator
    assert "3 paired day(s); ratio of sums 1.5000, latest 20 1.5000, drift 0.0000" in level_line(pairs)
    assert "3 paired day(s); median ratio 1.0000" in median_line(W8_LABEL, pairs)  # W8's line: the median


def test_the_latest_20_is_the_last_20_paired_days_in_date_order():
    pairs = [(d, 2.0 if i >= 5 else 1.0, 1.0) for i, d in enumerate(days(25))]
    assert "ratio of sums 1.8000, latest 20 2.0000, drift 0.2000" in level_line(list(reversed(pairs)))


def test_with_no_pairs_every_line_says_n_a():
    lines = diagnostic_lines([], [], [])
    assert [line.split(":")[0] for line in lines] == [IV30_LABEL, W8_LABEL, LEVEL_LABEL]
    assert all("0 paired day(s)" in line and line.count("n/a") == 3 for line in lines)


def test_the_report_prints_v4_and_v5_s_notes_and_the_diagnostics_in_text_and_json():
    reports = [QuestionReport(q, STATUS_NO_DATA) for q in (V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE)]
    notes, counts = ["drift line"], DayCounts(0, 0, 0, 0)
    lines = report_lines(reports, frozen=False, as_of="2026-10-24", days=counts, diagnostics=notes)
    assert lines[4] == "drift line"  # after the exploratory, title, secondary and day-count lines
    assert f"{V4_RV_BELOW_WEEKLY_IV}: {STATUS_NO_DATA}{QUESTION_NOTES[V4_RV_BELOW_WEEKLY_IV]}" in lines
    assert "not a variance-risk-premium estimate" in QUESTION_NOTES[V4_RV_BELOW_WEEKLY_IV]
    assert "not evidence of money" in QUESTION_NOTES[V5_INSIDE_STRADDLE]
    as_json = report_json(reports, frozen=False, as_of="2026-10-24", days=counts, diagnostics=notes)
    assert as_json["diagnostics"] == notes
