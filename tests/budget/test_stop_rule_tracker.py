"""Story BG1 criterion 6: the review date, projected while v4 is not frozen, and the tests' missing inputs."""

from datetime import date

import pytest

from fno.budget.stop_rule_tracker import INPUTS, StopRuleInput, review_date, stop_test_status
from fno.research_data.calendar import CsvSessionCalendar

HEADER = "date,kind,description,source_url\n"
CAL_2027 = CsvSessionCalendar(HEADER + "2027-05-31,holiday,made-up holiday,https://example.org/c\n")
CAL_2026 = CsvSessionCalendar(HEADER + "2026-01-26,holiday,Republic Day,https://example.org/c\n")


def test_a_november_freeze_gives_31_may_2027_projected_with_its_dependency():
    review = review_date(None, "2026-11", CAL_2026)
    assert review.day == date(2027, 5, 31) and review.basis.startswith("projected: depends on protocol v4 (story G6)")
    assert "no 2027 rows" in review.notes[0]


def test_the_calendar_decides_the_last_session_when_it_has_the_year():
    review = review_date(date(2026, 11, 20), "2026-11", CAL_2027)
    assert review.day == date(2027, 5, 28) and review.notes == () and "freeze on 2026-11-20" in review.basis


@pytest.mark.parametrize(
    "freeze, review", [(date(2026, 12, 1), date(2027, 6, 30)), (date(2027, 8, 5), date(2028, 2, 29))]
)
def test_six_full_months_after_the_freeze_month(freeze, review):
    assert review_date(freeze, "2026-11", CAL_2026).day == review


def test_both_tests_are_not_computable_while_inputs_are_missing(tmp_path):
    for test, stories in (("A", ["G6", "G8", "A16"]), ("B", ["R1", "R3"])):
        status, missing = stop_test_status(tmp_path, test)
        assert status == "not computable yet" and [i.story for i in missing] == stories
    assert len(INPUTS) == 5


def test_an_input_exists_only_when_its_story_names_a_path_that_is_there(tmp_path):
    (tmp_path / "scores.csv").write_text("x\n")
    assert StopRuleInput("A", "w", "G8", "scores.csv").exists(tmp_path)
    assert not StopRuleInput("A", "w", "G8").exists(tmp_path)
