"""REC1d's two sections (items 5 and 6; criteria b, c, e, g and h): the standing answer from the latest record before
today, the previous session's checks only and each dated, a waiting day with no such check named, an unreadable file
named by path and class, and the evening's answers with its no-record line."""

from fno.recommend import report_words as w
from fno.recommend.report_section import EveningSection, MorningSection
from fno.recommend.shelf import check_path
from fno.recommend.store import record_path
from tests.recommend.builders import DAY
from tests.recommend.report_fakes import TUESDAY, WEDNESDAY, Store, quiet, traded


def morning(store, day=TUESDAY):
    return MorningSection(store.ports()).render(day)


def test_an_empty_history_says_no_recommendation_yet(tmp_path):
    assert morning(Store(tmp_path)) == (w.NOTHING_YET,)


def test_the_standing_answer_is_the_latest_record_before_today_never_today_s(tmp_path):
    store = Store(tmp_path)
    store.record(day=DAY)
    store.record(day=TUESDAY)
    lines = morning(store, TUESDAY)
    assert lines[0] == w.STANDING.format(day=DAY), "today's record is made at 15:20; the morning shows the one before"
    assert lines[1] == "Real money: DO NOT TRADE (no version has passed)."
    assert lines[2] == "Rungs: school:CS1@1: rung 1 (exploratory); school:N0@1: rung 0 (unproven)."


def test_only_the_previous_session_s_checks_are_shown_each_dated(tmp_path):
    store = Store(tmp_path)
    monday = store.record(traded(DAY))
    store.check(monday, DAY)  # open on Monday evening: an older check, never shown on Wednesday
    store.check(monday, TUESDAY, net=-120.5)  # final on Tuesday evening
    lines = morning(store, WEDNESDAY)
    checks = [line for line in lines if line.startswith("Check of")]
    assert checks == [
        "Check of 02 Nov 2026 on 03 Nov 2026: complete. Its candidates' closed trades made Rs -120.50 after costs, "
        "so abstaining saved Rs 120.50. (1 closed, 0 open, 0 no trade, 0 ticket(s))."
    ]


def test_a_day_still_waiting_with_no_check_dated_the_previous_session_is_named(tmp_path):
    store = Store(tmp_path)
    monday = store.record(traded(DAY))
    store.check(monday, DAY)  # not known yet, and no check of it is dated Tuesday
    lines = morning(store, WEDNESDAY)
    assert lines[-1] == "No check of 02 Nov 2026 is dated the previous session (03 Nov 2026); still waiting."
    assert not any(line.startswith("Check of") for line in lines), "an older check is never shown"


def test_a_day_final_before_the_previous_session_waits_for_nothing(tmp_path):
    store = Store(tmp_path)
    store.check(store.record(traded(DAY)), DAY, net=10.0)  # closed and complete on Monday evening
    assert morning(store, WEDNESDAY)[-1] == w.NO_CHECKS.format(on=TUESDAY)


def test_a_failed_check_is_named_with_its_problem_and_an_unknown_problem_is_withheld(tmp_path):
    store = Store(tmp_path)
    store.record(day=DAY)
    store.failed_check(DAY, DAY, "never closed in 60 sessions")
    assert morning(store)[-1] == (
        "Check of 02 Nov 2026 on 02 Nov 2026: data check failed. The check failed: never closed in 60 sessions; "
        "no total is given. (0 closed, 0 open, 0 no trade, 0 ticket(s))."
    )
    store.failed_check(DAY, DAY, "the 51200 put lost Rs 300")
    assert f"a problem whose text is not shown here; see {check_path(DAY, DAY)}" in morning(store)[-1]


def test_a_complete_day_on_which_nothing_traded_reads_its_record(tmp_path):
    store = Store(tmp_path)
    store.check(store.record(quiet()), DAY)
    assert "complete. No candidate traded, so abstaining cost nothing." in morning(store)[-1]


def test_a_day_not_known_yet_gives_its_open_count_never_an_answer_or_a_total(tmp_path):
    store = Store(tmp_path)
    store.check(store.record(traded(DAY)), DAY)
    assert morning(store)[-1] == (
        "Check of 02 Nov 2026 on 02 Nov 2026: not known yet. 1 position(s) still open, so the day is not known yet. "
        "(0 closed, 1 open, 0 no trade, 0 ticket(s))."
    )


def test_an_unreadable_record_or_check_is_named_by_path_and_class(tmp_path):
    store = Store(tmp_path)
    store.check(store.record(quiet()), DAY)
    store.files[record_path(DAY)] = b"{damaged"
    lines = morning(store)
    assert lines[0] == f"The recommendation of 02 Nov 2026 was not read ({record_path(DAY)}, RecordRefused)."
    del store.files[check_path(DAY, DAY)]
    assert morning(store)[-1] == f"Check of 02 Nov 2026 on 02 Nov 2026 was not read ({check_path(DAY, DAY)}, KeyError)."


def test_the_evening_shows_today_s_answers_and_says_tonight_s_check_comes_later(tmp_path):
    store = Store(tmp_path)
    store.record(day=DAY)
    assert EveningSection(store.ports()).render(DAY) == (
        "Real money: DO NOT TRADE (no version has passed).",
        "Paper: NO TRADE (no_established_version: no version has passed: none is established on forward paper "
        "results).",
        w.TONIGHT,
    )


def test_the_evening_with_no_record_names_the_step_status_and_code_only(tmp_path):
    store = Store(tmp_path)
    assert EveningSection(store.ports()).render(DAY) == ("No recommendation recorded for 02 Nov 2026.",)
    store.steps[DAY] = ("failed", "recommend:NOT_POSTED")
    assert EveningSection(store.ports()).render(DAY) == (
        "No recommendation recorded for 02 Nov 2026 (recommend step: failed, recommend:NOT_POSTED).",
    )
