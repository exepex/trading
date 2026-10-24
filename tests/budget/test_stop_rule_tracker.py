"""Story BG1 criterion 6: the review date, projected while v4 is not frozen, and the tests' missing inputs."""

import subprocess
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
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # the root is a repository, as in production
    for test, stories in (("A", ["G6", "G8", "A16"]), ("B", ["R1", "R3"])):
        status, missing = stop_test_status(tmp_path, test)
        assert status == "not computable yet" and [i.story for i in missing] == stories
    assert len(INPUTS) == 5


def test_an_input_exists_only_when_its_story_names_a_path_that_is_there(tmp_path):
    (tmp_path / "scores.csv").write_text("x\n")
    assert StopRuleInput("A", "w", "G8", "scores.csv").exists(tmp_path)
    assert not StopRuleInput("A", "w", "G8").exists(tmp_path)


def test_a_month_ending_on_a_weekend_falls_back_to_its_friday():
    """Judge 104 should-fix 1: July 2027 ends on a Saturday; the calendar has no 2027 rows here."""
    review = review_date(date(2027, 1, 10), "2026-11", CAL_2026)
    assert review.day == date(2027, 7, 30) and review.day.weekday() == 4


def test_the_freeze_date_in_config_is_read_by_the_wiring():
    from fno.budget.wiring import build_review_date
    from fno.config import load_app_config

    config = load_app_config()
    config["budget"]["stop_rule"]["v4_freeze_date"] = "2026-12-03"
    review = build_review_date(config)
    assert review.day == date(2027, 6, 30) and "freeze on 2026-12-03" in review.basis
    assert build_review_date().basis.startswith("projected")


def test_the_review_date_reached_alert_comes_only_on_or_after_the_date():
    from fno.budget.stop_rule_tracker import review_reached

    review = review_date(None, "2026-11", CAL_2026)
    assert review_reached(review, date(2027, 5, 30)) == ""
    text = review_reached(review, date(2027, 5, 31))
    assert text.startswith("Omenix F&O SYSTEM: the stop-rule review date (31 May 2027") and "Test A and Test B" in text


def test_a_review_date_on_the_weekday_fallback_says_so_in_the_alert_itself():
    """Response 239 item 5 (A7 audit): the printed lines carried the fallback note; the #fno-desk alert dropped it."""
    from fno.budget.stop_rule_tracker import review_reached

    guessed = review_reached(review_date(None, "2026-11", CAL_2026), date(2027, 5, 31))
    assert guessed.endswith(
        "; the date is not confirmed: the NSE calendar has no 2027 rows, so the last weekday is used until NSE's 2027 "
        "circular is added"
    )
    confirmed = review_reached(review_date(date(2026, 11, 20), "2026-11", CAL_2027), date(2027, 5, 28))
    assert "not confirmed" not in confirmed and confirmed.endswith("(design v2 section 8.2)")


def test_test_b_reads_resolved_shadow_trades_from_the_shadow_accounts_folder(tmp_path):
    """Judge 210 finding 1, criterion 7: Test B's R3 input is `journal/shadow`, where E6 opens each shadow account."""
    from playbook.builders import document

    from fno.desk.wiring import start_shadow_books
    from fno.playbook.schema import parse_strategy

    [r3] = [i for i in INPUTS if i.story == "R3"]
    assert r3.path == "journal/shadow" and not r3.exists(tmp_path)
    start_shadow_books([parse_strategy(document(name="cand-c"))], date(2026, 10, 14), tmp_path)
    assert r3.exists(tmp_path)
