"""Story O8 criterion 2 for the desk run (in-file `decisions` finish), A16's marks (its own per-mark status, counted)
and the evening data jobs (push receipt of the commit that first added the session's row)."""

import json
from datetime import time, timedelta

import pytest

from fno.constants import (
    DAILY_RUN_STEPS,
    DESK_RUN_STEPS,
    HEALTH_LATE,
    HEALTH_MISSED,
    HEALTH_NOT_DUE,
    HEALTH_NOT_EXPECTED,
    HEALTH_OK,
    NO_DECISION_LATE,
    RUN_LOG_DECISIONS_STEP,
    STEP_FAILED,
    STEP_NOT_LIVE,
    STEP_REFUSED,
)
from fno.desk.daily_steps import COLLECTED_LATE, COLLECTION_GRACE
from fno.desk.run_log import RUNS_FOLDER
from fno.health.data_checks import PanelDayCheck, SessionRowCheck
from fno.health.desk_checks import MarksCheck, RunLogCheck
from fno.health.expectations import (
    CLOSES_FILE,
    FLOW_HISTORY_BY,
    FLOWS_BY,
    INDEX_CLOSE_BY,
    PANEL_DAY_BY,
    PANEL_MANIFEST,
)
from fno.health.model import Deadline
from fno.intraday.slots import MARKS_PER_SESSION

from .fakes import DAY, Repo, ist

EVENING = ist(DAY, 17, 51)
DESK_DEADLINE = Deadline(time(15, 12))
SECOND = timedelta(seconds=1)
AT_DEADLINE = ist(DAY, 15, 12)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def _run_log(repo, steps=DAILY_RUN_STEPS, decided=AT_DEADLINE, results=None, finished=None):
    def body(step):
        return {"started_at": decided.isoformat(), "finished_at": (finished or decided).isoformat(), "inputs": {},
                "result": (results or {}).get(step, {})}  # fmt: skip

    repo.write_json(f"journal/{RUNS_FOLDER}/{DAY.isoformat()}.json",
                    {"day": DAY.isoformat(), "kind": "daily_run", "steps": {s: body(s) for s in steps}})  # fmt: skip


@pytest.mark.parametrize(("after", "status"), [(COLLECTION_GRACE, HEALTH_OK), (COLLECTION_GRACE + SECOND, HEALTH_LATE)])
def test_the_desk_run_is_on_time_by_its_decisions_start_within_e3s_grace(repo, after, status):
    """E3 collects at the deadline and fails closed after deadline + COLLECTION_GRACE (fno/desk/daily_steps.py): a
    start one second past the grace is late, whatever the finish."""
    _run_log(repo, decided=AT_DEADLINE + after)
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == status


@pytest.mark.parametrize(
    ("start", "finish", "status"),
    [(29, 31, HEALTH_OK), (31, 31, HEALTH_LATE), (31, 29, HEALTH_LATE)],  # seconds after the deadline
)
def test_the_start_decides_never_the_finish(repo, start, finish, status):
    """Judge 552: started inside the grace and finished after it is on time; started after it is late."""
    _run_log(repo, decided=AT_DEADLINE + start * SECOND, finished=AT_DEADLINE + finish * SECOND)
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == status


def test_e3s_own_collected_late_verdict_wins_over_an_on_time_start(repo):
    """E3 reads its clock a few ms after the run log's start: when it failed closed, its reason decides."""
    why = COLLECTED_LATE.format(started="2026-10-15T15:12:30.004+05:30", deadline="2026-10-15T15:12:00+05:30")
    late = {"book1_rules": {"decision": NO_DECISION_LATE, "reason": why}}
    _run_log(repo, decided=AT_DEADLINE + COLLECTION_GRACE, results={RUN_LOG_DECISIONS_STEP: late})
    result = RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING)
    assert result.status == HEALTH_LATE and "E3 collected late" in result.detail


def test_a_book_late_for_its_own_reason_is_not_read_as_a_late_collection(repo):
    """Only E3's COLLECTED_LATE text is a late collection; a book that committed nothing in time is another matter."""
    book_late = {"book1_rules": {"decision": NO_DECISION_LATE, "reason": "nothing visible at the deadline 15:12"}}
    _run_log(repo, results={RUN_LOG_DECISIONS_STEP: book_late})
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_OK


@pytest.mark.parametrize(("now", "status"), [(29, HEALTH_NOT_DUE), (30, HEALTH_MISSED)])
def test_no_decisions_step_waits_for_the_same_grace(repo, now, status):
    _run_log(repo, steps=tuple(s for s in DAILY_RUN_STEPS if s != RUN_LOG_DECISIONS_STEP))
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, AT_DEADLINE + now * SECOND).status == status


@pytest.mark.parametrize("day", ["2026-10-19", "2026-10-21", "2026-10-22", "2026-10-23"])
def test_the_real_run_logs_of_the_dry_run_read_on_time(day):
    """The O1 dry run (docs/dryruns/DRY1_2026-10-23.md, f3): started 15:12:00.0003, finished about 1.3 s later."""
    from datetime import date

    from fno.config import ROOT

    result = RunLogCheck(ROOT, DESK_DEADLINE).check(date.fromisoformat(day), ist(date.fromisoformat(day), 17, 51))
    assert result.status != HEALTH_LATE  # the old finish-time rule read all four late; other steps may still be missed


@pytest.mark.parametrize("missing", ["exits", "trade_marks", "card"])  # E2d's marking step after the exits, O1's last
def test_a_run_log_missing_a_step_is_a_miss_naming_it(repo, missing):
    _run_log(repo, steps=tuple(step for step in DAILY_RUN_STEPS if step != missing))
    result = RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and result.detail == f"steps not run: {missing}"


def test_a_run_log_without_decisions_and_no_run_log_at_all(repo):
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).detail.startswith("never ran")
    _run_log(repo, steps=("versions", "pack"))
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, ist(DAY, 15, 0)).status == HEALTH_NOT_DUE
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_MISSED


def test_a_skipped_run_is_not_expected(repo):
    _run_log(repo, steps=("skipped",))
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_NOT_EXPECTED


def test_the_check_reads_the_daily_run_s_own_tuple(repo):
    """Story O1 merged second: the steps expected are `DAILY_RUN_STEPS`, the tuple the run loops over (O1's
    `tests/daily/test_day_run.py` proves the run writes exactly it), never a copy: a desk-only log misses O1's."""
    _run_log(repo, steps=DESK_RUN_STEPS)
    detail = RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).detail
    assert detail == (
        "steps not run: quotes, owner_timing_fills, margin_check, weather, forecasts_v4, book1, reviews, "
        "quotes_done, card, price_distribution, premium_ranges, price_distribution_scores, price_ranges, "
        "price_range_scores, premium_range_scores, candles, close_read, close_recheck"
    )


def test_a_failed_or_refused_o1_step_is_a_problem_with_its_reason_not_live_is_not(repo):
    refused = {"status": STEP_REFUSED, "reason": "nothing written: stale closes"}
    failed = {"status": STEP_FAILED, "reason": "Slack refused"}
    not_live = {"status": STEP_NOT_LIVE, "reason": "no live date"}
    _run_log(repo, results={"weather": not_live, "card": failed, "forecasts_v4": refused})
    result = RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED
    assert (
        result.detail == "steps not ok: forecasts_v4 refused: nothing written: stale closes; card failed: Slack refused"
    )
    _run_log(repo, results={"weather": {"status": STEP_NOT_LIVE, "reason": "no live date"}})
    assert RunLogCheck(repo.root, DESK_DEADLINE).check(DAY, EVENING).status == HEALTH_OK


def _marks(repo, statuses):
    for i, status in enumerate(statuses):
        mark = ist(DAY, 9, 15) + timedelta(minutes=15 * i)
        repo.write(f"research/data/intraday/slots/2026/10/15/nifty_20261015_{mark:%H%M}.csv",
                   f"session,mark,status\n{DAY},{mark.isoformat()},{status}\n")  # fmt: skip


@pytest.mark.parametrize(
    ("statuses", "status"),
    [
        (["good"] * MARKS_PER_SESSION, HEALTH_OK),
        (["good"] * (MARKS_PER_SESSION - 1) + ["late"], HEALTH_LATE),
        (["good"] * (MARKS_PER_SESSION - 1) + ["missed"], HEALTH_MISSED),
        (["good"] * (MARKS_PER_SESSION - 1), HEALTH_MISSED),  # 25 of 26: one never written
    ],
)
def test_a16_marks_are_counted_by_their_own_status(repo, statuses, status):
    _marks(repo, statuses)
    result = MarksCheck(repo.root / "research/data/intraday").check(DAY, EVENING)
    assert result.status == status and f"of {MARKS_PER_SESSION} good" in result.detail


def test_no_marks_is_not_due_before_the_last_mark_and_missed_after(repo):
    check = MarksCheck(repo.root / "research/data/intraday")
    assert check.check(DAY, ist(DAY, 15, 29)).status == HEALTH_NOT_DUE
    assert check.check(DAY, ist(DAY, 15, 31)).status == HEALTH_MISSED


@pytest.mark.parametrize(("deadline", "on_time", "late"), [
    (INDEX_CLOSE_BY, ist(DAY + timedelta(1), 12, 0), ist(DAY + timedelta(1), 12, 0, 1)),
    (FLOWS_BY, ist(DAY + timedelta(1), 12, 0), ist(DAY + timedelta(1), 12, 0, 1)),
    (FLOW_HISTORY_BY, ist(DAY + timedelta(1), 9, 0), ist(DAY + timedelta(1), 9, 0, 1)),  # A23: 21:30, retry 07:15
])  # fmt: skip
def test_a_session_row_is_on_time_by_the_push_that_first_added_it(repo, deadline, on_time, late):
    repo.write(CLOSES_FILE, f"date,close\n2026-10-14,1\n{DAY},2\n")
    check = SessionRowCheck(repo.evidence, CLOSES_FILE, deadline)
    repo.receipts.row(CLOSES_FILE, f"{DAY},", on_time)
    assert check.check(DAY, ist(DAY + timedelta(2), 17, 51)).status == HEALTH_OK
    repo.receipts.row(CLOSES_FILE, f"{DAY},", late)
    assert check.check(DAY, ist(DAY + timedelta(2), 17, 51)).status == HEALTH_LATE


def test_a_missing_row_is_not_due_until_its_deadline_then_missed(repo):
    repo.write(CLOSES_FILE, "date,close\n2026-10-14,1\n")
    check = SessionRowCheck(repo.evidence, CLOSES_FILE, INDEX_CLOSE_BY)
    assert check.check(DAY, EVENING).status == HEALTH_NOT_DUE  # an evening job at 17:51
    assert check.check(DAY, ist(DAY + timedelta(1), 12, 0, 1)).status == HEALTH_MISSED


def test_a_panel_day_needs_status_ok_and_its_push(repo):
    repo.write(PANEL_MANIFEST, json.dumps({"days": {DAY.isoformat(): {"status": "ok"}}}, indent=1))
    repo.receipts.row(PANEL_MANIFEST, f'"{DAY.isoformat()}": {{', ist(DAY + timedelta(1), 1, 40))
    assert PanelDayCheck(repo.evidence, PANEL_MANIFEST, PANEL_DAY_BY).check(DAY, EVENING).status == HEALTH_OK
    repo.write(PANEL_MANIFEST, json.dumps({"days": {DAY.isoformat(): {"status": "failed"}}}, indent=1))
    result = PanelDayCheck(repo.evidence, PANEL_MANIFEST, PANEL_DAY_BY).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "failed" in result.detail
