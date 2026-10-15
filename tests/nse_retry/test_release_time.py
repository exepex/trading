"""Story A9b with the orchestrator's decisions 37 and 49 (A8): a check's `checked_at` is when NSE's answer arrived (a
503 retried first is not seeing the file) and its start time goes to a side log beside the check log. A writer that
commits only the check log (the A8 routine does, by path) loses start times, never evidence."""

from datetime import date, datetime, timedelta

import pytest

from fno.constants import RELEASE_PRESENT, RELEASE_UNREACHABLE
from fno.models import IST
from fno.research_data.release_times import (
    LOG_FIELDS,
    STARTS_NAME,
    ReleaseLog,
    ReleaseTimeRecorder,
    first_seen_times,
)
from fno.storage.raw_source import ParticipantOiSource
from tests.nse_retry.fake_nse import ScriptedNse, answer
from tests.research_data.test_participant_oi_availability import CALENDAR, FRIDAY, FakeClock, at

BEFORE = (
    "day,checked_at,outcome,sha256,last_modified\n"
    "2026-10-08,2026-10-08T18:30:00+05:30,absent,,\n"
    "2026-10-08,2026-10-08T18:45:00+05:30,present,abc,\n"
)


def recorder(tmp_path, *answers):
    clock = FakeClock(at(FRIDAY, 19))
    source = ParticipantOiSource(ScriptedNse(*answers), sleep=clock.sleep)
    log = ReleaseLog(tmp_path / "release_checks.csv")
    return ReleaseTimeRecorder(source, ParticipantOiSource.path_for, CALENDAR, log, clock, clock.sleep), log


def test_a_503_then_the_file_records_the_answer_time_and_the_start_beside_it(tmp_path):
    rec, log = recorder(tmp_path, answer(503), answer(200, b"file"))
    check = rec.check(FRIDAY)
    assert (check.outcome, check.started_at, check.checked_at) == (
        RELEASE_PRESENT,
        at(FRIDAY, 19),
        at(FRIDAY, 19) + timedelta(seconds=5),
    )
    assert log.checks() == [check]
    assert log.path.read_text().splitlines() == [
        ",".join(LOG_FIELDS),
        f"2026-10-09,2026-10-09T19:00:05+05:30,present,{check.sha256},",
    ]
    assert (tmp_path / STARTS_NAME).read_text().splitlines()[
        1
    ] == "2026-10-09,2026-10-09T19:00:05+05:30,2026-10-09T19:00:00+05:30"


def test_a_check_answered_at_once_has_equal_times(tmp_path):
    rec, _ = recorder(tmp_path, answer(200, b"file"))
    check = rec.check(FRIDAY)
    assert check.started_at == check.checked_at == at(FRIDAY, 19)


def test_nse_down_after_its_retries_is_unreachable_at_the_time_it_gave_up(tmp_path):
    rec, _ = recorder(tmp_path, *[answer(503)] * 4)
    check = rec.check(FRIDAY)
    assert check.outcome == RELEASE_UNREACHABLE and check.checked_at - check.started_at == timedelta(seconds=65)


def test_checks_before_a9b_keep_their_rows_and_read_without_a_start(tmp_path):
    (tmp_path / "release_checks.csv").write_text(BEFORE)
    rec, log = recorder(tmp_path, answer(200, b"file"))
    rec.check(FRIDAY)
    checks = log.checks()
    assert [c.day for c in checks] == [date(2026, 10, 8), date(2026, 10, 8), FRIDAY]
    assert checks[0].started_at is None and checks[-1].started_at == at(FRIDAY, 19)
    assert first_seen_times(checks)[date(2026, 10, 8)] == datetime(2026, 10, 8, 18, 45, tzinfo=IST)
    assert log.path.read_text().startswith(BEFORE)  # earlier rows untouched, same header


def test_a_lost_start_log_loses_start_times_never_evidence(tmp_path):
    rec, log = recorder(tmp_path, answer(404), answer(200, b"file"))
    rec.check(FRIDAY)
    rec.sleep(300)
    rec.check(FRIDAY)
    (tmp_path / STARTS_NAME).unlink()  # a writer that committed the check log only (the A8 routine)
    assert [(c.outcome, c.started_at) for c in log.checks()] == [("absent", None), ("present", None)]
    assert first_seen_times(log.checks()) == {FRIDAY: at(FRIDAY, 19, 5)}


@pytest.mark.parametrize("name", ["release_checks.csv", STARTS_NAME])
def test_a_log_with_another_header_is_refused_and_an_empty_one_gets_its_header(tmp_path, name):
    (tmp_path / name).write_text("day,when\n2026-10-08,x\n")
    with pytest.raises(ValueError, match="its header is not"):
        ReleaseLog(tmp_path / "release_checks.csv").checks()
    (tmp_path / name).write_text("")
    rec, log = recorder(tmp_path, answer(200, b"file"))
    rec.check(FRIDAY)
    assert len(log.checks()) == 1 and log.checks()[0].started_at == at(FRIDAY, 19)
