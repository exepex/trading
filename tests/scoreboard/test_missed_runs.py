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
    assert held == [{"day": "2026-11-10", "missed_decision": False, "missed_exit_review": True}]
    assert runs.missed_runs("book1_rules", [MON, TUE], lambda day: False) == []
