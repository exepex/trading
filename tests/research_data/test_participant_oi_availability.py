"""Story A8 criterion 3: a decision on day D never sees D's participant-OI file unless the measured release rule allows
it; until 20 days are measured, the conservative default (the next session's decision time) applies."""

import hashlib
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from fno.constants import RELEASE_ABSENT, RELEASE_PRESENT, RELEASE_REWRITTEN, RELEASE_UNREACHABLE
from fno.models import IST
from fno.research_data.availability import LastWriteBoundRule, MeasuredReleaseRule, NextSessionRule
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.positioning import PointInTimeParticipantOi
from fno.research_data.release_times import (
    MIN_MEASURED_DAYS,
    ReleaseCheck,
    ReleaseLog,
    ReleaseTimeRecorder,
    choose_availability_rule,
    first_seen_times,
)
from fno.storage.raw_source import ParticipantOiSource, PublishedFile, RawFileSource, RawSourceUnavailable

NSE = Path(__file__).resolve().parents[1] / "fixtures" / "nse"
SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf"
# October 2026: Fri 9th and Mon 12th are sessions (10th, 11th weekend); 20 Oct is a holiday in NSE's 2026 circular.
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-20,holiday,Diwali (test),{SOURCE}\n")
DECISION = time(15, 0)
FRIDAY, MONDAY = date(2026, 10, 9), date(2026, 10, 12)


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


def history(rule) -> PointInTimeParticipantOi:
    """The real 9 Oct 2026 file, stored under both 8 and 9 Oct (8 Oct's copy only stands in for an older day)."""
    data = (NSE / "fao_participant_oi_09102026.csv").read_bytes()
    files = {FRIDAY: data, date(2026, 10, 8): data.replace(b"Oct 09, 2026", b"Oct 08, 2026")}
    return PointInTimeParticipantOi(files.get, ParticipantOiSource.filename_for, CALENDAR, rule)


def test_by_default_a_decision_on_day_d_never_sees_ds_file():
    reader = history(NextSessionRule(CALENDAR, DECISION))
    assert reader.as_of(at(FRIDAY, 15)).day == date(2026, 10, 8)  # D's decision sees D-1's file
    assert reader.as_of(at(FRIDAY, 23, 59)).day == date(2026, 10, 8)  # even late that evening
    assert reader.as_of(at(MONDAY, 14, 59)).day == date(2026, 10, 8)  # not before the next session's decision time
    assert reader.as_of(at(MONDAY, 15)).day == FRIDAY  # usable from the next session's decision time


def test_the_default_skips_holidays_and_weekends():
    rule = NextSessionRule(CALENDAR, DECISION)
    assert rule.usable_from(FRIDAY) == at(MONDAY, 15)
    assert rule.usable_from(date(2026, 10, 19)) == at(date(2026, 10, 21), 15)  # 20 Oct holiday


def measured_checks(release: time, days: int, absent_before=timedelta(minutes=5)) -> list[ReleaseCheck]:
    sessions = CALENDAR.sessions(date(2026, 9, 1), date(2026, 10, 30))[:days]
    checks = []
    for day in sessions:
        seen = datetime.combine(day, release, IST)
        checks += [ReleaseCheck(day, seen - absent_before, RELEASE_ABSENT), ReleaseCheck(day, seen, RELEASE_PRESENT)]
    return checks


def test_the_default_holds_until_twenty_days_are_measured():
    early = measured_checks(time(14, 0), MIN_MEASURED_DAYS - 1)
    assert isinstance(choose_availability_rule(early, CALENDAR, DECISION), NextSessionRule)
    rule = choose_availability_rule(measured_checks(time(14, 0), MIN_MEASURED_DAYS), CALENDAR, DECISION)
    assert isinstance(rule, MeasuredReleaseRule)


def test_only_a_measured_rule_can_let_day_d_see_ds_file():
    """Hypothetical evidence: NSE released by 14:00 on 20 days; then 14:30 (with the margin) beats 15:00."""
    rule = choose_availability_rule(measured_checks(time(14, 0), MIN_MEASURED_DAYS), CALENDAR, DECISION)
    assert history(rule).as_of(at(FRIDAY, 15)).day == FRIDAY
    assert history(rule).as_of(at(FRIDAY, 14, 59)).day == date(2026, 10, 8)  # before the decision time: no


def test_measured_evening_releases_give_the_next_session_and_a_late_one_pushes_further():
    evening = choose_availability_rule(measured_checks(time(19, 16), MIN_MEASURED_DAYS), CALENDAR, DECISION)
    assert evening.usable_from(FRIDAY) == at(MONDAY, 15)
    checks = measured_checks(time(19, 16), MIN_MEASURED_DAYS)
    late_day = checks[-1].day
    checks += [
        ReleaseCheck(late_day + timedelta(1), at(late_day + timedelta(1), 9), RELEASE_ABSENT),
        ReleaseCheck(late_day + timedelta(1), at(late_day + timedelta(2), 15, 10), RELEASE_PRESENT),
    ]  # once, a file appeared only after the next session's decision time
    rule = choose_availability_rule(checks, CALENDAR, DECISION)
    assert rule.usable_from(FRIDAY) == at(date(2026, 10, 13), 15)  # stricter than the default


def test_a_day_counts_as_measured_only_when_seen_absent_before_present():
    day = FRIDAY
    only_present = [ReleaseCheck(day, at(day, 20), RELEASE_PRESENT)]
    unreachable_then_present = [ReleaseCheck(day, at(day, 18), RELEASE_UNREACHABLE), *only_present]
    assert first_seen_times(only_present) == {}
    assert first_seen_times(unreachable_then_present) == {}
    bracketed = [ReleaseCheck(day, at(day, 18), RELEASE_ABSENT), *only_present]
    assert first_seen_times(bracketed) == {day: at(day, 20)}


class FakeArchive(RawFileSource):
    def __init__(self, answers):
        self.answers, self.asked = list(answers), []

    def fetch(self, path):
        self.asked.append(path)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


class FakeClock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def recorder(tmp_path, answers, start):
    clock = FakeClock(start)
    archive = FakeArchive(answers)
    log = ReleaseLog(tmp_path / "release_checks.csv")
    return ReleaseTimeRecorder(archive, ParticipantOiSource.path_for, CALENDAR, log, clock, clock.sleep), archive, log


def test_the_recorder_logs_every_check_until_the_file_appears_and_never_asks_again(tmp_path):
    rec, archive, log = recorder(tmp_path, [None, RawSourceUnavailable("down"), b"file"], at(FRIDAY, 18, 50))
    found = rec.watch(FRIDAY, at(FRIDAY, 22), timedelta(minutes=5))
    assert (found.outcome, found.checked_at) == (RELEASE_PRESENT, at(FRIDAY, 19))
    assert [c.outcome for c in log.checks()] == [RELEASE_ABSENT, RELEASE_UNREACHABLE, RELEASE_PRESENT]
    assert archive.asked == [ParticipantOiSource.path_for(FRIDAY)] * 3
    assert rec.watch(FRIDAY, at(FRIDAY, 22), timedelta(minutes=5)) == found and len(archive.asked) == 3
    assert first_seen_times(log.checks()) == {FRIDAY: at(FRIDAY, 19)}
    assert log.path.read_text().splitlines()[0] == "day,checked_at,outcome,sha256,last_modified,started_at"


def test_the_recorder_stops_at_the_cutoff_and_skips_closed_days(tmp_path):
    rec, archive, log = recorder(tmp_path, [None, None, None], at(FRIDAY, 21, 50))
    last = rec.watch(FRIDAY, at(FRIDAY, 22), timedelta(minutes=5))
    assert last.outcome == RELEASE_ABSENT and len(archive.asked) == 3  # 21:50, 21:55, 22:00
    assert rec.watch(date(2026, 10, 10), at(date(2026, 10, 10), 22), timedelta(minutes=5)) is None  # a Saturday
    assert len(archive.asked) == 3


def test_the_wired_rule_follows_the_committed_evidence_file():
    from fno.composition import build_participant_oi_rule
    from fno.storage.wiring import PARTICIPANT_OI_RELEASE_LOG

    assert PARTICIPANT_OI_RELEASE_LOG.is_file()  # the evidence file exists before any use
    measured = len(first_seen_times(ReleaseLog(PARTICIPANT_OI_RELEASE_LOG).checks()))
    rule = build_participant_oi_rule()
    assert isinstance(rule, LastWriteBoundRule)  # every wired rule respects the recorded last writes (judge 15)
    assert isinstance(rule.rule, NextSessionRule) == (measured < MIN_MEASURED_DAYS)


def test_a_day_rewritten_later_is_not_used_before_its_own_last_write():
    """Judge 15: Friday's bytes held today were written the following Wednesday evening (a rewrite), so no decision
    before Thursday 15:00 may use them; it uses Thursday's file instead. Other days keep the next-session rule."""
    rewritten = {FRIDAY: at(date(2026, 10, 14), 19, 0)}
    rule = LastWriteBoundRule(NextSessionRule(CALENDAR, DECISION), CALENDAR, DECISION, rewritten)
    assert rule.usable_from(FRIDAY) == at(date(2026, 10, 15), 15)
    assert rule.usable_from(date(2026, 10, 8)) == at(FRIDAY, 15)  # not rewritten: unchanged
    assert history(rule).as_of(at(MONDAY, 15)).day == date(2026, 10, 8)  # the default alone would give Friday
    assert not rule.is_usable(FRIDAY, at(date(2026, 10, 15), 14, 59))
    on_time = LastWriteBoundRule(NextSessionRule(CALENDAR, DECISION), CALENDAR, DECISION, {FRIDAY: at(FRIDAY, 19)})
    assert on_time.usable_from(FRIDAY) == at(MONDAY, 15)  # written that evening: the base rule decides


def test_the_wired_rule_holds_the_real_rewritten_day_back_until_its_rewrite():
    """15 Jan 2024's file was last written on 15 Jan 2025 at 19:00 IST (judge 15 confirmed it live)."""
    from fno.composition import build_participant_oi_rule

    rule = build_participant_oi_rule()
    assert rule.usable_from(date(2024, 1, 15)) == at(date(2025, 1, 16), 15)
    assert rule.usable_from(date(2026, 10, 9)) == at(MONDAY, 15)  # an ordinary day: next session


class PublishingArchive(RawFileSource):
    def __init__(self, answers):
        self.answers = list(answers)

    def fetch(self, path):
        raise AssertionError("the recorder asks for the file with its last-write time")

    def fetch_published(self, path):
        return self.answers.pop(0)


def test_the_recorder_stores_the_last_write_and_flags_a_later_rewrite(tmp_path):
    clock = FakeClock(at(MONDAY, 19))
    log = ReleaseLog(tmp_path / "release_checks.csv")
    first, later = at(FRIDAY, 18, 48), at(MONDAY, 18, 30)
    archive = PublishingArchive([PublishedFile(b"v1", first), PublishedFile(b"v2", later), PublishedFile(b"v2", later)])
    rec = ReleaseTimeRecorder(archive, ParticipantOiSource.path_for, CALENDAR, log, clock, clock.sleep)
    assert rec.check(FRIDAY).last_modified == first
    assert [c.outcome for c in rec.recheck_recent(MONDAY)] == [RELEASE_REWRITTEN]  # Friday's bytes changed
    assert rec.check(FRIDAY).outcome == RELEASE_REWRITTEN  # still other bytes than first seen
    assert [c.last_modified for c in log.checks()] == [first, later, later]  # kept through the CSV
    assert (
        rec.watch(FRIDAY, at(MONDAY, 22), timedelta(minutes=5)).sha256 == hashlib.sha256(b"v1").hexdigest()
    )  # first sight stays


def test_the_log_refuses_to_append_under_an_old_header(tmp_path):
    path = tmp_path / "release_checks.csv"
    path.write_text("day,checked_at,outcome,sha256\n")
    with pytest.raises(ValueError, match="header"):
        ReleaseLog(path).append(ReleaseCheck(FRIDAY, at(FRIDAY, 19), RELEASE_ABSENT))
    assert path.read_text() == "day,checked_at,outcome,sha256\n"
