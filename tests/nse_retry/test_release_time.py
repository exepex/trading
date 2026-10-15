"""Story A9b with the orchestrator's decision 37 (A8): a check's `checked_at` is when NSE's answer arrived (a 503
retried first is not seeing the file) and `started_at` when the check began; the log before A9b is read beside the
current one and never written."""

from datetime import date, datetime, timedelta

import pytest

from fno.constants import RELEASE_PRESENT, RELEASE_UNREACHABLE
from fno.models import IST
from fno.research_data.release_times import LEGACY_LOG_NAME, ReleaseLog, ReleaseTimeRecorder, first_seen_times
from fno.storage.raw_source import ParticipantOiSource
from tests.nse_retry.fake_nse import ScriptedNse, answer
from tests.research_data.test_participant_oi_availability import CALENDAR, FRIDAY, FakeClock, at

LEGACY = (
    "day,checked_at,outcome,sha256,last_modified\n"
    "2026-10-08,2026-10-08T18:30:00+05:30,absent,,\n"
    "2026-10-08,2026-10-08T18:45:00+05:30,present,abc,\n"
)


def recorder(tmp_path, *answers):
    clock = FakeClock(at(FRIDAY, 19))
    source = ParticipantOiSource(ScriptedNse(*answers), sleep=clock.sleep)
    log = ReleaseLog(tmp_path / "release_checks_v2.csv")
    return ReleaseTimeRecorder(source, ParticipantOiSource.path_for, CALENDAR, log, clock, clock.sleep), log


def test_a_503_then_the_file_records_the_answer_time_and_the_start_time(tmp_path):
    rec, log = recorder(tmp_path, answer(503), answer(200, b"file"))
    check = rec.check(FRIDAY)
    assert (check.outcome, check.started_at, check.checked_at) == (
        RELEASE_PRESENT,
        at(FRIDAY, 19),
        at(FRIDAY, 19) + timedelta(seconds=5),
    )
    assert log.checks() == [check]
    row = log.path.read_text().splitlines()[1].split(",")
    assert row[1] == "2026-10-09T19:00:05+05:30" and row[-1] == "2026-10-09T19:00:00+05:30"


def test_a_check_answered_at_once_has_equal_times(tmp_path):
    rec, _ = recorder(tmp_path, answer(200, b"file"))
    check = rec.check(FRIDAY)
    assert check.started_at == check.checked_at == at(FRIDAY, 19)


def test_nse_down_after_its_retries_is_unreachable_at_the_time_it_gave_up(tmp_path):
    rec, _ = recorder(tmp_path, *[answer(503)] * 4)
    check = rec.check(FRIDAY)
    assert check.outcome == RELEASE_UNREACHABLE and check.checked_at - check.started_at == timedelta(seconds=65)


def test_the_legacy_log_is_read_first_and_never_written(tmp_path):
    (tmp_path / LEGACY_LOG_NAME).write_text(LEGACY)
    rec, log = recorder(tmp_path, answer(200, b"file"))
    rec.check(FRIDAY)
    checks = log.checks()
    assert [c.day for c in checks] == [date(2026, 10, 8), date(2026, 10, 8), FRIDAY]
    assert checks[0].started_at is None  # legacy: one try, its checked_at the start
    assert first_seen_times(checks)[date(2026, 10, 8)] == datetime(2026, 10, 8, 18, 45, tzinfo=IST)
    assert (tmp_path / LEGACY_LOG_NAME).read_text() == LEGACY


def test_a_legacy_log_with_another_header_is_refused(tmp_path):
    (tmp_path / LEGACY_LOG_NAME).write_text("day,when\n2026-10-08,x\n")
    with pytest.raises(ValueError, match="its header is not"):
        ReleaseLog(tmp_path / "release_checks_v2.csv").checks()


def test_an_empty_log_file_gets_its_header_and_the_legacy_name_is_never_a_log_to_write(tmp_path):
    (tmp_path / "release_checks_v2.csv").write_text("")
    rec, log = recorder(tmp_path, answer(200, b"file"))
    rec.check(FRIDAY)
    assert log.path.read_text().splitlines()[0] == "day,checked_at,outcome,sha256,last_modified,started_at"
    with pytest.raises(ValueError, match="read only, never written"):
        ReleaseLog(tmp_path / LEGACY_LOG_NAME)
