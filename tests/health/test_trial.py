"""Story O10: the go-live trial. A problem is silent unless its job recorded it (its own evidence, or a capture-error
row from one of its jobs within 2 days); a session is judged once, when final;
a session with no row breaks the streak."""

from __future__ import annotations

from datetime import date, timedelta

from fno.constants import HEALTH_LATE, HEALTH_MISSED, HEALTH_NOT_DUE, HEALTH_OK, HEALTH_UNKNOWN
from fno.health.capture_errors import CaptureError, CaptureErrorLog
from fno.health.checker import Finding, HealthRun
from fno.health.model import CheckResult
from fno.health.trial import TrialDay, TrialLedger, TrialReport, errors_line, judge, trial_line

from .fakes import CALENDAR, DAY

JOBS = (("Index closes", ("index-closes",)), ("NSE recorder", ("quote-recorder-nse",)))
MON, TUE, WED, FRI = date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 16)


def run(*findings, sessions=(DAY,)):
    return HealthRun(DAY, tuple(sessions), ("Index closes", "NSE recorder"), tuple(findings), (), (), JOBS)


def found(check, status, recorded=False, session=DAY):
    return Finding(check, session, CheckResult(status, "x", recorded))


def error(job, day=DAY, kind="failure"):
    return CaptureError(day, job, "step", kind, "m", "u")


def test_a_problem_with_no_record_is_silent():
    assert judge(run(found("Index closes", HEALTH_MISSED), found("NSE recorder", HEALTH_OK)), []) == [
        TrialDay(DAY, ("Index closes",))
    ]


def test_a_row_from_its_job_within_two_days_records_it():
    findings = (found("Index closes", HEALTH_MISSED),)
    assert judge(run(*findings), [error("index-closes", DAY + timedelta(days=2))]) == [TrialDay(DAY, ())]
    assert judge(run(*findings), [error("index-closes", DAY + timedelta(days=3))])[0].silent == ("Index closes",)
    assert judge(run(*findings), [error("panel-days")])[0].silent == ("Index closes",)  # another job's row
    assert judge(run(*findings), [error("index-closes", kind="http_error_recovered")])[0].silent == ("Index closes",)


def test_the_job_s_own_evidence_records_it_and_late_or_unknown_are_problems():
    assert judge(run(found("NSE recorder", HEALTH_MISSED, recorded=True)), []) == [TrialDay(DAY, ())]
    assert judge(run(found("NSE recorder", HEALTH_LATE)), [])[0].silent == ("NSE recorder",)
    assert judge(run(found("NSE recorder", HEALTH_UNKNOWN)), [])[0].silent == ("NSE recorder",)


def test_a_session_with_a_check_not_due_is_not_judged_yet():
    assert judge(run(found("Index closes", HEALTH_NOT_DUE), found("NSE recorder", HEALTH_OK)), []) == []


def test_each_session_is_appended_once(tmp_path):
    ledger = TrialLedger(tmp_path / "trial_days.csv")
    ledger.append(ledger.new([TrialDay(DAY, ("Index closes", "NSE recorder"))]))
    assert ledger.new([TrialDay(DAY, ())]) == []
    assert ledger.days() == {DAY: TrialDay(DAY, ("Index closes", "NSE recorder"))}
    assert (tmp_path / "trial_days.csv").read_text().splitlines() == [
        "session,silent_count,silent_checks", "2026-10-15,2,Index closes;NSE recorder"]  # fmt: skip


def test_the_streak_counts_back_and_names_what_broke_it():
    clean = {d: TrialDay(d, ()) for d in (MON, TUE, WED, DAY, FRI)}
    assert trial_line(clean, CALENDAR) == "trial: 5 clean sessions in a row"
    assert trial_line({**clean, WED: TrialDay(WED, ("Index closes",))}, CALENDAR) == (
        "trial: 2 clean sessions in a row (last silent: Index closes 14 Oct)")  # fmt: skip
    missing = {d: TrialDay(d, ()) for d in (MON, WED, DAY, FRI)}
    assert trial_line(missing, CALENDAR) == "trial: 3 clean sessions in a row (not proven: 13 Oct)"
    assert trial_line({}, CALENDAR) == "trial: no session judged yet"


def test_weekends_and_holidays_never_break_it():
    days = {d: TrialDay(d, ()) for d in (FRI, date(2026, 10, 19), date(2026, 10, 21))}  # 17-18 weekend, 20 holiday
    assert trial_line(days, CALENDAR) == "trial: 3 clean sessions in a row"


def test_the_errors_line_names_the_window_s_jobs():
    rows = [error("index-closes"), error("nse-margins"), error("index-closes", DAY - timedelta(days=9)),
            error("news-capture", kind="stale_recovered")]  # fmt: skip
    assert (
        errors_line(rows, DAY - timedelta(days=6), DAY) == "capture errors: 2 in the window (index-closes, nse-margins)"
    )
    assert errors_line([], DAY, DAY) is None


def test_the_report_appends_only_when_asked(tmp_path):
    log = CaptureErrorLog(tmp_path / "capture_errors.csv")
    log.append(error("index-closes"))
    report = TrialReport(TrialLedger(tmp_path / "trial_days.csv"), log, CALENDAR)
    lines = report.lines(run(found("Index closes", HEALTH_MISSED), found("NSE recorder", HEALTH_MISSED)))
    assert lines == ["capture errors: 1 in the window (index-closes)",
                     "trial: 0 clean sessions in a row (last silent: NSE recorder 15 Oct)"]  # fmt: skip
    assert not (tmp_path / "trial_days.csv").exists()  # a dry run stops here
    report.record()
    assert TrialLedger(tmp_path / "trial_days.csv").days() == {DAY: TrialDay(DAY, ("NSE recorder",))}


class Recording:
    def __init__(self):
        self.recorded = 0

    def lines(self, run):
        return ["trial: 1 clean session in a row"]

    def record(self):
        self.recorded += 1


def test_the_cli_appends_on_a_real_run_only(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from fno.health import cli as health_cli
    from fno.health.run_record import RunRecord

    from .fakes import ist

    trial, sent = Recording(), []

    class Sender:
        def send(self, text):
            sent.append(text)
            return "alert sent to #fno-desk"

    def cli(dry_run, broken=False):
        def build(cfg):
            if broken:
                raise KeyError("x")
            return SimpleNamespace(run=lambda now: HealthRun(DAY, (DAY,), ("A",), (), ()))

        monkeypatch.setattr("fno.health.wiring.build_health_check", build)
        monkeypatch.setattr("fno.health.wiring.build_trial_report", lambda: trial)
        monkeypatch.setattr("fno.health.wiring.build_run_record", lambda: RunRecord(tmp_path / "runs.csv"))
        monkeypatch.setattr("fno.composition.build_alert_sender", lambda: Sender())
        return health_cli.cmd_health(SimpleNamespace(at=ist(DAY, 17, 51), dry_run=dry_run), out=lambda line: None)

    assert cli(dry_run=True) == 0 and trial.recorded == 0
    assert cli(dry_run=False) == 0 and trial.recorded == 1
    assert sent[-1].endswith("\ntrial: 1 clean session in a row")  # one message, the trial line last
    assert cli(dry_run=False, broken=True) == 1 and trial.recorded == 1
