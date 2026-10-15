"""Story O8 criteria 1, 5 and 6: one health run over the window (muhurat and `live_from` handled, an unknown never
turned into ok), one message with at most one line per check, and the watcher's own run record."""

from datetime import date, datetime, timedelta

import pytest

from fno.constants import HEALTH_MISSED, HEALTH_NOT_DUE, HEALTH_NOT_EXPECTED, HEALTH_OK, HEALTH_UNKNOWN
from fno.health.checker import HealthCheck
from fno.health.expectations import Expectation
from fno.health.model import CheckResult, EvidenceUnknown, SessionCheck
from fno.health.report import message, table, verdict
from fno.health.run_record import RunRecord
from fno.quotes.recorder import RECORDED_SESSION_KINDS

from .fakes import CALENDAR, DAY, ist

MUHURAT = date(2026, 10, 21)
EVENING = ist(DAY, 17, 51)


class Planted(SessionCheck):
    def __init__(self, results: dict[date, CheckResult] | None = None, error: Exception | None = None):
        self.results, self.error, self.asked = results or {}, error, []

    def check(self, session: date, now: datetime) -> CheckResult:
        self.asked.append(session)
        if self.error:
            raise self.error
        return self.results.get(session, CheckResult(HEALTH_OK, "fine"))


def _run(tmp_path, expectations, now=EVENING, record=None):
    return HealthCheck(expectations, CALENDAR, record or RunRecord(tmp_path / "runs.csv"), 6).run(now)


def test_all_ok_is_exactly_one_line(tmp_path):
    run = _run(tmp_path, [Expectation("A", Planted(), RECORDED_SESSION_KINDS, date(2026, 10, 1))])
    assert message(run) == "health 15 Oct: all on time (1 checks, sessions 9 Oct to 15 Oct)"
    assert verdict(run) == "all on time" and len(table(run)) == 5


def test_problems_take_one_line_per_check_never_one_per_session(tmp_path):
    missed = CheckResult(HEALTH_MISSED, "none")
    bad = Planted({DAY: missed, DAY - timedelta(1): missed, DAY - timedelta(2): CheckResult(HEALTH_UNKNOWN, "x")})
    run = _run(tmp_path, [Expectation("NSE recorder", bad, RECORDED_SESSION_KINDS, date(2026, 10, 1)),
                          Expectation("Fine", Planted(), RECORDED_SESSION_KINDS, date(2026, 10, 1))])  # fmt: skip
    lines = message(run).splitlines()
    assert lines[0].startswith("health 15 Oct: 1 problem (2 checks")
    assert lines[1:] == ["- NSE recorder: unknown (x) 13 Oct; missed (none) 14 Oct, 15 Oct"]


def test_a_muhurat_session_is_not_expected_for_a_3pm_job_and_checked_for_an_evening_one(tmp_path):
    three_pm, evening = Planted(), Planted()
    run = _run(tmp_path, [Expectation("3 pm", three_pm, RECORDED_SESSION_KINDS, date(2026, 10, 1)),
                          Expectation("evening", evening, (*RECORDED_SESSION_KINDS, "muhurat"), date(2026, 10, 1))],
               now=ist(MUHURAT, 23, 0))  # fmt: skip
    found = {(f.check, f.session): f.result.status for f in run.findings}
    assert found[("3 pm", MUHURAT)] == HEALTH_NOT_EXPECTED and MUHURAT not in three_pm.asked
    assert MUHURAT in evening.asked


def test_a_check_before_live_from_or_not_live_is_silent(tmp_path):
    later, never = Planted(), Planted()
    run = _run(tmp_path, [Expectation("later", later, RECORDED_SESSION_KINDS, DAY),
                          Expectation("never", never, RECORDED_SESSION_KINDS, None)])  # fmt: skip
    assert later.asked == [DAY] and never.asked == [] and run.checks == ("later",)


def test_an_unknown_is_a_problem_never_ok(tmp_path):
    run = _run(tmp_path, [Expectation("A", Planted(error=EvidenceUnknown("push time unknown: HTTP 403")),
                                      RECORDED_SESSION_KINDS, DAY)])  # fmt: skip
    assert run.findings[0].result == CheckResult(HEALTH_UNKNOWN, "push time unknown: HTTP 403")
    assert verdict(run) == "1 problem"


@pytest.mark.parametrize("error", [TypeError("naive time"), ValueError("bad"), KeyError("x"), AttributeError("y")])
def test_a_malformed_file_is_that_checks_unknown_and_the_others_still_run(tmp_path, error):
    run = _run(tmp_path, [Expectation("A", Planted(error=error), RECORDED_SESSION_KINDS, DAY),
                          Expectation("B", Planted(), RECORDED_SESSION_KINDS, DAY)])  # fmt: skip
    found = {f.check: f.result for f in run.findings}
    assert found["A"] == CheckResult(HEALTH_UNKNOWN, f"evidence malformed ({type(error).__name__})")
    assert found["B"].status == HEALTH_OK


def test_another_error_stops_the_run(tmp_path):
    with pytest.raises(ZeroDivisionError):
        _run(tmp_path, [Expectation("A", Planted(error=ZeroDivisionError()), RECORDED_SESSION_KINDS, DAY)])


def test_not_due_is_listed_on_its_own_line_and_is_not_a_problem(tmp_path):
    run = _run(tmp_path, [Expectation("Index closes", Planted({DAY: CheckResult(HEALTH_NOT_DUE, "no row")}),
                                      RECORDED_SESSION_KINDS, DAY)])  # fmt: skip
    assert message(run).splitlines()[1:] == ["not due yet: Index closes 15 Oct"] and verdict(run) == "all on time"


def test_a_window_with_no_session_says_so(tmp_path):
    calendar_gap = HealthCheck([], CALENDAR, RunRecord(tmp_path / "r.csv"), 0)
    run = calendar_gap.run(ist(date(2026, 10, 18), 17, 51))  # a Sunday, window of 0 days
    assert message(run) == "health 18 Oct: no session in the window"


def test_the_run_record_appends_one_row_per_run(tmp_path):
    record = RunRecord(tmp_path / "ops" / "health_runs.csv")
    record.append(DAY, ist(DAY, 17, 51), ist(DAY, 17, 52), "all on time")
    record.append(DAY, ist(DAY, 19, 0), ist(DAY, 19, 1), "1 problem")
    lines = (tmp_path / "ops" / "health_runs.csv").read_text().splitlines()
    assert lines[0] == "date,started_at,finished_at,result" and len(lines) == 3


def test_missing_runs_are_reported_inside_the_window_and_never_before_the_first_row(tmp_path):
    record = RunRecord(tmp_path / "runs.csv")
    assert record.missing(DAY, 6) == []  # the first run has no history
    for day in (date(2026, 10, 11), date(2026, 10, 13), date(2026, 10, 14)):
        record.append(day, ist(day, 17, 51), ist(day, 17, 52), "all on time")
    assert record.missing(DAY, 6) == [date(2026, 10, 12)]  # 9 and 10 Oct are before the first row
    assert record.missing(date(2026, 10, 14), 6) == [date(2026, 10, 12)]  # a second run that day: nothing new


def test_a_missing_run_is_one_problem_line(tmp_path):
    record = RunRecord(tmp_path / "runs.csv")
    for day in (date(2026, 10, 12), date(2026, 10, 14)):
        record.append(day, ist(day, 17, 51), ist(day, 17, 52), "all on time")
    run = _run(tmp_path, [Expectation("A", Planted(), RECORDED_SESSION_KINDS, DAY)], record=record)
    assert message(run).splitlines()[1:] == ["- health check did not run on 13 Oct"]
