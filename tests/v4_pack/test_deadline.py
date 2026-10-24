"""Story G10 completion, criterion 7: the 15:10 deadline verdict from GitHub's receipt time (15:10:00 on time,
15:10:01 late; never a commit's own time); an unknown receipt time writes nothing for its day and fails the run; today
only from 15:12; the catch-up checks every live session without a verdict, except in a rehearsal (today only); the
commitments are the live CSV rows and G7b's live-record receipts, the AI books left out by their own set."""

import inspect
import json
from datetime import date, datetime

import pytest

from fno.constants import BOOK2_HYBRID
from fno.models import IST
from fno.storage.data_store import DataStore
from fno.storage.receipts import ReceiptFolder
from fno.v4_pack.commitment import CommitmentTimes, CommitmentTimeUnknown
from fno.v4_pack.commitments import FILE, ROW, SEALED_COMMITMENTS, Commitment, CommitmentSource, RecordCommitments
from fno.v4_pack.deadline import NOT_LIVE, DeadlineRun, parse_verdicts
from fno.v4_pack.paths import deadline_path
from fno.v4_pack.sessions import sessions_between
from tests.v4_pack.test_release import FakeDrive

THU, FRI, MON = date(2026, 10, 22), date(2026, 10, 23), date(2026, 10, 26)
WEEKDAYS = sessions_between(lambda d: d.weekday() < 5)


def at(day, hh, mm, ss=0):
    return datetime(day.year, day.month, day.day, hh, mm, ss, tzinfo=IST)


class Source(CommitmentSource):
    def commitments(self, day):
        return [
            Commitment("base_rate", "q1", ROW, "research/forecasts/v4/base_rate/q1.csv", f"{day},0.1,ok,live"),
            Commitment("v4_rule", "q4", FILE, f"receipts/data/v4/records/live/v4_rule/q4/2026/{day}.json.sha256"),
        ]


class Times(CommitmentTimes):
    def __init__(self, received, unknown_on=None):
        self.received, self.unknown_on, self.asked = received, unknown_on, []

    def row_received_at(self, path, row_text, day):
        return self._at(day, ("row", path, row_text))

    def file_received_at(self, path):
        return self._at(date.fromisoformat(path.rsplit("/", 1)[1][:10]), ("file", path))

    def _at(self, day, asked):
        self.asked.append(asked)
        if day == self.unknown_on:
            raise CommitmentTimeUnknown("push time unknown: outside GitHub's log")
        return self.received(day)


def deadline(tmp_path, now, received, live_from=THU, unknown_on=None, catch_up=True, drive=None):
    drive = drive or FakeDrive()
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "v4-deadline", "run-1")
    times = Times(received, unknown_on)
    run = DeadlineRun(store, lambda path: drive.get(path) is not None, Source(), times, WEEKDAYS, live_from,
                      lambda: now, catch_up)  # fmt: skip
    return run, drive, times


def verdicts(drive, day):
    return parse_verdicts(drive.files[f"data/{deadline_path(day)}"])[1]


@pytest.mark.parametrize(("second", "expected"), [(0, "on_time"), (1, "late")])
def test_received_at_15_10_00_is_on_time_and_15_10_01_late(tmp_path, second, expected):
    run, drive, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 15, 10, second), live_from=MON)
    assert run.run(MON) == [
        f"v4 deadline 2026-10-26: {2 if second == 0 else 0} on time, {0 if second == 0 else 2} late"
    ]
    assert verdicts(drive, MON) == {("base_rate", "q1"): expected, ("v4_rule", "q4"): expected} and not run.failed


def test_the_catch_up_checks_every_live_session_without_a_verdict_and_a_rerun_writes_nothing(tmp_path):
    run, drive, times = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12))
    assert [line[12:22] for line in run.run(MON)] == ["2026-10-22", "2026-10-23", "2026-10-26"]
    before, asked = dict(drive.files), len(times.asked)
    assert run.run(MON) == [] and drive.files == before and len(times.asked) == asked


def test_an_unknown_receipt_time_writes_nothing_for_its_day_and_fails(tmp_path):
    run, drive, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12), unknown_on=FRI)
    lines = run.run(MON)
    assert lines[1] == ("v4 deadline 2026-10-23: NOT checked (push time unknown: outside GitHub's log); the next run "
                        "retries it") and run.failed  # fmt: skip
    assert f"data/{deadline_path(FRI)}" not in drive.files and f"data/{deadline_path(MON)}" in drive.files


def test_today_is_never_checked_before_15_12(tmp_path):
    run, drive, _ = deadline(tmp_path, at(MON, 15, 11, 59), lambda day: at(day, 14, 12), live_from=MON)
    assert run.run(MON) == ["v4 deadline 2026-10-26: not checked before 15:12"] and drive.files == {}


def test_a_rehearsal_checks_the_replayed_day_only(tmp_path):
    run, _, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12), catch_up=False)
    assert [line[12:22] for line in run.run(MON)] == ["2026-10-26"]


def test_not_live_and_a_day_with_no_commitment(tmp_path):
    run, drive, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12), live_from=None)
    assert run.run(MON) == [NOT_LIVE] and drive.files == {}

    class Nothing(CommitmentSource):
        def commitments(self, day):
            return []

    run, drive, _ = deadline(tmp_path / "e", at(MON, 15, 15), lambda day: at(day, 14, 12), live_from=MON)
    run.source = Nothing()
    assert run.run(MON) == ["v4 deadline 2026-10-26: 0 on time, 0 late"]
    assert json.loads(drive.files[f"data/{deadline_path(MON)}"])["commitments"] == []


def test_the_commitments_are_live_rows_and_live_record_receipts_without_the_ai_books(tmp_path):
    folder = tmp_path / "research/forecasts/v4"
    header = "day,value,status,label\n"
    (folder / "base_rate").mkdir(parents=True)
    (folder / "base_rate/q1.csv").write_text(
        header + "2026-10-26,0.1,ok,backfill_exploratory\n2026-10-26,0.2,ok,live\n"
    )
    (folder / BOOK2_HYBRID).mkdir()
    (folder / BOOK2_HYBRID / "q1.csv").write_text(header + "2026-10-26,0.3,ok,live\n")
    receipts = tmp_path / "receipts/data/v4/records/live"
    for forecaster in ("v4_rule", BOOK2_HYBRID):
        (receipts / forecaster / "q4/2026").mkdir(parents=True)
        (receipts / forecaster / "q4/2026/2026-10-26.json.sha256").write_text("x")
        (receipts / forecaster / "q4/2026/2026-10-23.json.sha256").write_text("x")
    found = RecordCommitments(tmp_path, "research/forecasts/v4", "receipts/data/v4/records/live").commitments(MON)
    assert found == [
        Commitment("base_rate", "q1", ROW, "research/forecasts/v4/base_rate/q1.csv", "2026-10-26,0.2,ok,live"),
        Commitment("v4_rule", "q4", FILE, "receipts/data/v4/records/live/v4_rule/q4/2026/2026-10-26.json.sha256"),
    ]


def test_a_pack_reader_is_still_checked_only_the_ai_books_are_exempt(tmp_path, monkeypatch):
    """G7b adds its V4 and V5 forecasters to PACK_READERS: their records are still checked here (judge 580 SF3)."""
    import fno.v4_pack.commitments as commitments
    import fno.v4_pack.guard as guard

    monkeypatch.setattr(guard, "PACK_READERS", guard.PACK_READERS | {"v4_rule"})
    assert {"book2_hybrid", "book3_ai"} == SEALED_COMMITMENTS and SEALED_COMMITMENTS is not guard.PACK_READERS
    assert "from .guard" not in inspect.getsource(commitments)  # its own set, never the guard's PACK_READERS
    receipt = tmp_path / "receipts/data/v4/records/live/v4_rule/q4/2026/2026-10-26.json.sha256"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("x")
    found = RecordCommitments(tmp_path, "research/forecasts/v4", "receipts/data/v4/records/live").commitments(MON)
    assert [c.forecaster for c in found] == ["v4_rule"]


def test_the_catch_up_starts_at_the_first_live_v4_session_not_at_its_own_live_date(tmp_path):
    """Review finding 2: the check goes live after 22 Oct's live rows; they are checked too, as the release's catch-up
    settles their labels, so no live row is left unchecked for good."""
    run, drive, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12), live_from=MON)
    run.checks_from = THU
    assert [line[12:22] for line in run.run(MON)] == ["2026-10-22", "2026-10-23", "2026-10-26"]


def test_an_unreadable_record_line_names_the_file_and_the_day_is_retried(tmp_path):
    """Review finding 3: never a traceback, never a guessed time; a blank line is no row."""
    folder = tmp_path / "research/forecasts/v4/base_rate"
    folder.mkdir(parents=True)
    (folder / "q1.csv").write_text("day,value,status,label\n\n2026-10-26,0.2,ok,live\n2026-10-26,0.2,ok\n")
    source = RecordCommitments(tmp_path, "research/forecasts/v4", "receipts/data/v4/records/live")
    run, drive, _ = deadline(tmp_path, at(MON, 15, 15), lambda day: at(day, 14, 12), live_from=MON)
    run.source = source
    assert run.run(MON) == ["v4 deadline 2026-10-26: NOT checked (research/forecasts/v4/base_rate/q1.csv line 4: not "
                            "one record row (3 fields for 4 columns)); the next run retries it"]  # fmt: skip
    assert drive.files == {} and run.failed
