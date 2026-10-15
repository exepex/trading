"""Story S6 section 5 and criterion 9 (scoreboard B, as it ran): missed decisions and missed exit reviews read from E3's
run logs, per book, on sessions only."""

import json
from datetime import date

from fno.scoreboard.committed_runs import CommittedRuns
from tests.scoreboard.builders import write_log
from tests.scoreboard.matched_builders import weekdays

FRI, MON, TUE = date(2026, 11, 6), date(2026, 11, 9), date(2026, 11, 10)


def with_exits(root, day):
    path = root / "journal" / "runs" / f"{day.isoformat()}.json"
    log = json.loads(path.read_text())
    log["steps"]["exits"] = {"started_at": "", "finished_at": "", "inputs": {}, "result": {}}
    path.write_text(json.dumps(log))


def test_a_session_without_a_log_or_without_the_books_run_is_a_missed_decision(tmp_path):
    write_log(tmp_path, MON, {"book1_rules": "r1", "book2_hybrid": None})
    with_exits(tmp_path, MON)
    sessions = weekdays(FRI, MON)  # Friday, then Monday: the weekend is never a session
    book2 = CommittedRuns(tmp_path).missed_runs("book2_hybrid", sessions, lambda day: False)
    book1 = CommittedRuns(tmp_path).missed_runs("book1_rules", sessions, lambda day: False)
    assert [m["day"] for m in book2] == ["2026-11-06", "2026-11-09"] and all(m["missed_decision"] for m in book2)
    assert [m["day"] for m in book1] == ["2026-11-06"]  # Friday has no log at all


def test_a_run_stopped_before_exits_is_a_missed_exit_review_only_while_a_trade_was_held(tmp_path):
    for day in (MON, TUE):
        write_log(tmp_path, day, {"book1_rules": f"r-{day}"})
    with_exits(tmp_path, MON)  # Tuesday's run stopped before its exits step
    runs = CommittedRuns(tmp_path)
    held = runs.missed_runs("book1_rules", [MON, TUE], lambda day: day == MON)
    assert held == [
        {"day": "2026-11-10", "missed_decision": False, "missed_exit_review": True, "exit_review": "no exit review ran"}
    ]
    assert runs.missed_runs("book1_rules", [MON, TUE], lambda day: False) == []


def test_an_exits_step_where_the_books_review_failed_or_was_held_up_is_a_missed_exit_review(tmp_path):
    for day, outcome in (
        (MON, {"reviewed": False, "error": "no snapshot"}),
        (TUE, {"reviewed": False, "waiting": ["NIFTY-C"], "reason": "held up"}),
    ):  # E3's shapes
        write_log(tmp_path, day, {"book1_rules": f"r-{day}"})
        path = tmp_path / "journal" / "runs" / f"{day.isoformat()}.json"
        log = json.loads(path.read_text())
        log["steps"]["exits"] = {"started_at": "", "finished_at": "", "inputs": {}, "result": {"book1_rules": outcome}}
        path.write_text(json.dumps(log))
    found = CommittedRuns(tmp_path).missed_runs("book1_rules", [FRI, MON, TUE, date(2026, 11, 11)], lambda day: True)
    assert [(m["day"], m["missed_exit_review"], m["exit_review"]) for m in found] == [
        ("2026-11-06", False, ""), ("2026-11-09", True, "exit review failed: no snapshot"),
        ("2026-11-10", True, "not checked against prices: held up")]  # fmt: skip
    # Friday: no log, a missed decision, and no trade held before it; 11 Nov, the report day, has not run yet


def test_a_real_nse_holiday_is_never_listed(tmp_path):
    from fno.composition import build_session_calendar

    sessions = build_session_calendar().sessions(date(2026, 10, 1), date(2026, 10, 5))  # 2 Oct: Gandhi Jayanti
    found = CommittedRuns(tmp_path).missed_runs("book1_rules", sessions, lambda day: False)
    assert date(2026, 10, 2) not in sessions and "2026-10-02" not in [m["day"] for m in found]


def exits_log(root, day, result):
    write_log(root, day, {"book1_rules": f"r-{day}"})
    path = root / "journal" / "runs" / f"{day.isoformat()}.json"
    log = json.loads(path.read_text())
    log["steps"]["exits"] = {"started_at": "", "finished_at": "", "inputs": {}, "result": result}
    path.write_text(json.dumps(log))


def test_only_an_exit_review_that_says_reviewed_counts_as_reviewed(tmp_path):
    """Review 120 (response 200 fix 3): `reviewed: false` without an error, or no outcome for the book at all, is a
    missed exit review; E3 writes `reviewed: true` only when the review ran."""
    wed, thu = date(2026, 11, 11), date(2026, 11, 12)
    exits_log(tmp_path, MON, {"book1_rules": {"reviewed": True, "results": []}})
    exits_log(tmp_path, TUE, {"book1_rules": {"reviewed": True, "results": []}})
    exits_log(tmp_path, wed, {"book1_rules": {"reviewed": False}})
    exits_log(tmp_path, thu, {"book2_hybrid": {"reviewed": True, "results": []}})
    found = CommittedRuns(tmp_path).missed_runs("book1_rules", [MON, TUE, wed, thu], lambda day: True)
    assert [(m["day"], m["exit_review"]) for m in found] == [
        ("2026-11-11", "exit review not recorded as done"),
        ("2026-11-12", "exit review not recorded as done"),
    ]
