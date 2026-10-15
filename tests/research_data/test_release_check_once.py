"""Story A8 on GitHub Actions: `participant-oi check-once`, one check per scheduled run (no AI session)."""

from datetime import date, datetime, time

import pytest

import fno.composition
from fno.cli import main
from fno.constants import RELEASE_ABSENT, RELEASE_PRESENT, RELEASE_REWRITTEN, RELEASE_UNREACHABLE
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.release_check_once import CheckOnceResult, ReleaseCheckOnce, due_day
from fno.research_data.release_times import ReleaseLog, ReleaseTimeRecorder
from fno.research_data.reread_log import RereadLog
from fno.storage.raw_source import ParticipantOiSource, RawFileSource, RawSourceUnavailable

SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-20,holiday,Diwali (test),{SOURCE}\n")
FRIDAY, MONDAY, SATURDAY = date(2026, 10, 9), date(2026, 10, 12), date(2026, 10, 10)


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


class Archive(RawFileSource):
    """Answers per day: the bytes (or None, or an error) for each day's file, the latest answer kept."""

    def __init__(self, answers: dict):
        self.answers, self.asked = dict(answers), []

    def fetch(self, path):
        self.asked.append(path)
        answer = self.answers[path]
        if isinstance(answer, Exception):
            raise answer
        return answer


class Clock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def build(tmp_path, answers: dict, now: datetime):
    archive, clock = Archive({ParticipantOiSource.path_for(d): a for d, a in answers.items()}), Clock(now)
    log = ReleaseLog(tmp_path / "release_checks_v2.csv")
    recorder = ReleaseTimeRecorder(archive, ParticipantOiSource.path_for, CALENDAR, log, clock, lambda s: None)
    return ReleaseCheckOnce(recorder, RereadLog(tmp_path / "release_rereads.csv")), archive, clock, log


def test_one_check_per_run_until_present_then_nothing(tmp_path):
    once, archive, clock, log = build(tmp_path, {MONDAY: None}, at(MONDAY, 17, 37))
    assert once.run(MONDAY).alerts == [] and [c.outcome for c in log.checks()] == [RELEASE_ABSENT]
    archive.answers[ParticipantOiSource.path_for(MONDAY)] = b"file"
    clock.now = at(MONDAY, 17, 52)
    result = once.run(MONDAY)
    assert result.alerts == [] and result.lines == [
        f"{MONDAY}: present at 2026-10-12 17:52 IST {log.checks()[-1].sha256[:12]}"
    ]
    clock.now = at(MONDAY, 23, 22)  # later runs: no request, no row, no "still absent" alert
    assert once.run(MONDAY).lines == [f"{MONDAY}: already recorded present at 17:52 IST; nothing checked"]
    assert len(archive.asked) == 2 and len(log.checks()) == 2


def test_a_closed_day_checks_nothing(tmp_path):
    once, archive, _, log = build(tmp_path, {}, at(SATURDAY, 18))
    assert once.run(SATURDAY).lines == [f"{SATURDAY}: not a trading day; nothing checked"]
    assert archive.asked == [] and log.checks() == []


def test_unreachable_alerts_every_time(tmp_path):
    once, _, clock, log = build(tmp_path, {MONDAY: RawSourceUnavailable("down")}, at(MONDAY, 18))
    first = once.run(MONDAY).alerts
    clock.now = at(MONDAY, 18, 15)
    assert len(first) == 1 and "unreachable at 2026-10-12 18:00 IST" in first[0] and len(once.run(MONDAY).alerts) == 1
    assert [c.outcome for c in log.checks()] == [RELEASE_UNREACHABLE] * 2


def test_still_absent_alerts_once_from_23_15(tmp_path):
    once, _, clock, _ = build(tmp_path, {MONDAY: None}, at(MONDAY, 23, 7))
    assert once.run(MONDAY).alerts == []  # before 23:15: no alert
    clock.now = at(MONDAY, 23, 22)
    alerts = once.run(MONDAY).alerts
    assert len(alerts) == 1 and "still absent at 2026-10-12 23:22 IST, past 23:15" in alerts[0]
    clock.now = at(MONDAY, 23, 37)  # a late run after the first late one: no second alert
    assert once.run(MONDAY).alerts == []


def test_a_run_github_starts_after_midnight_checks_the_evening_still_due():
    """14 Oct 2026: GitHub started scheduled runs 4.5 to 5.5 hours late, so an evening run may start next morning."""
    assert due_day(at(MONDAY, 12)) == MONDAY and due_day(at(MONDAY, 23, 59)) == MONDAY
    assert due_day(at(date(2026, 10, 13), 1, 30)) == MONDAY and due_day(at(date(2026, 10, 13), 11, 59)) == MONDAY


def test_still_absent_alerts_at_a_late_run_after_midnight_when_none_ran_from_23_15(tmp_path):
    once, _, clock, log = build(tmp_path, {MONDAY: None}, at(MONDAY, 22, 52))
    assert once.run(MONDAY).alerts == []
    clock.now = at(date(2026, 10, 13), 1, 30)  # the 23:22 run, started 2 hours late
    alerts = once.run(MONDAY).alerts
    assert len(alerts) == 1 and "the 2026-10-12 file is still absent at 2026-10-13 01:30 IST, past 23:15" in alerts[0]
    assert [c.day for c in log.checks()] == [MONDAY, MONDAY]


def test_recent_files_are_re_read_once_a_day_and_a_rewrite_alerts(tmp_path):
    once, archive, clock, log = build(tmp_path, {FRIDAY: b"v1", MONDAY: None}, at(FRIDAY, 19))
    once.run(FRIDAY)  # Friday's file seen
    archive.answers[ParticipantOiSource.path_for(FRIDAY)] = b"v2"  # NSE rewrites it over the weekend
    clock.now = at(MONDAY, 17, 37)
    alerts = once.run(MONDAY).alerts
    assert len(alerts) == 1 and alerts[0].startswith(f"Omenix F&O participant OI: REWRITTEN {FRIDAY}")
    clock.now = at(MONDAY, 17, 52)
    asked = len(archive.asked)
    assert once.run(MONDAY).alerts == [] and len(archive.asked) == asked + 1  # only Monday's file: no second re-read
    assert [c.outcome for c in log.checks()] == [RELEASE_PRESENT, RELEASE_REWRITTEN, RELEASE_ABSENT, RELEASE_ABSENT]


def test_a_late_run_for_the_previous_day_does_not_stand_for_the_next_days_re_read(tmp_path):
    """Judge 89's probe: Monday's file found at 00:30 Tuesday, Friday's file rewritten on Tuesday; Tuesday's evening
    run must still re-read Friday's file and alert."""
    tuesday = date(2026, 10, 13)
    once, archive, clock, _ = build(tmp_path, {FRIDAY: b"v1", MONDAY: None, tuesday: None}, at(FRIDAY, 19))
    once.run(FRIDAY)
    clock.now = at(MONDAY, 17, 37)
    assert once.run(MONDAY).alerts == []  # Monday's re-read: Friday unchanged; Monday's file absent
    archive.answers[ParticipantOiSource.path_for(MONDAY)] = b"monday"
    clock.now = at(tuesday, 0, 30)
    assert once.run(due_day(clock.now)).alerts == []  # a late run: Monday's file present, no second Monday re-read
    archive.answers[ParticipantOiSource.path_for(FRIDAY)] = b"v2"
    clock.now = at(tuesday, 18)
    alerts = once.run(due_day(clock.now)).alerts
    assert [a.split(":")[1].strip() for a in alerts] == [f"REWRITTEN {FRIDAY}"]


def test_a_re_read_that_could_not_reach_nse_is_tried_again(tmp_path):
    once, archive, clock, _ = build(tmp_path, {FRIDAY: b"v1", MONDAY: None}, at(FRIDAY, 19))
    once.run(FRIDAY)
    archive.answers[ParticipantOiSource.path_for(FRIDAY)] = RawSourceUnavailable("down")
    clock.now = at(MONDAY, 17, 37)
    once.run(MONDAY)
    archive.answers[ParticipantOiSource.path_for(FRIDAY)] = b"v2"
    clock.now = at(MONDAY, 17, 52)
    alerts = once.run(MONDAY).alerts
    assert len(alerts) == 1 and f"REWRITTEN {FRIDAY}" in alerts[0]


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent"


class FakeOnce:
    alerts: list[str] = []
    days: list[date] = []

    def run(self, day):
        self.days.append(day)
        return CheckOnceResult(["line"], list(self.alerts))


def test_the_command_checks_the_due_day_by_default(monkeypatch):
    from fno.research_data import participant_oi_cli

    monkeypatch.setattr(FakeOnce, "alerts", [])
    monkeypatch.setattr(FakeOnce, "days", [])
    monkeypatch.setattr(participant_oi_cli, "now_ist", lambda: at(date(2026, 10, 13), 1, 30))
    monkeypatch.setattr(fno.composition, "build_release_check_once", FakeOnce)
    assert main(["participant-oi", "check-once"]) == 0 and FakeOnce.days == [MONDAY]


@pytest.mark.parametrize(("alerts", "code"), [([], 0), (["Omenix F&O participant OI: x"], 1)])
def test_the_command_posts_each_alert_and_fails_only_then(monkeypatch, capsys, alerts, code):
    sender = FakeSender()
    monkeypatch.setattr(FakeOnce, "alerts", alerts)
    monkeypatch.setattr(FakeOnce, "days", [])
    monkeypatch.setattr(fno.composition, "build_alert_sender", lambda: sender)
    monkeypatch.setattr(fno.composition, "build_release_check_once", FakeOnce)
    assert main(["participant-oi", "check-once", "--day", "2026-10-12"]) == code
    assert FakeOnce.days == [MONDAY] and sender.sent == alerts
    assert capsys.readouterr().out == "\n".join(["line", *alerts, *(["alert sent"] if alerts else [])]) + "\n"
