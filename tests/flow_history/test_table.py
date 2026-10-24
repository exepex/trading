"""Scope 2-3 and criterion 2 at the table: write times through A8's sweep, point-in-time dates, waiting sessions,
damaged files; one new part per run."""

from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime, time

import pytest

from fno.flow_history.table import COLUMNS, FlowTableJob
from fno.flow_history.values import ParticipantVolumeValues
from fno.models import IST
from fno.research_data.write_sweep import LastWriteSweep, read_sweeps
from fno.storage.data_store import DataStore
from fno.storage.part_table import PartTable
from fno.storage.raw_source import ParticipantVolumeSource, RawFileSource, RawSourceUnavailable
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

from .sheets import participant_volume
from .test_availability import _next

SOURCE = ParticipantVolumeSource
MON, TUE, WED = date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 22)  # 21 Oct: the test calendar's holiday


def ist(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute), IST)


class Nse(RawFileSource):
    def __init__(self, written: dict):
        self.written, self.asked = written, []

    def fetch(self, path):
        raise AssertionError("the table never downloads")

    def last_written(self, path):
        day = SOURCE.day_for_path(path)
        self.asked.append(day)
        answer = self.written.get(day)
        if isinstance(answer, Exception):
            raise answer
        return answer


class Desk:
    def __init__(self, tmp_path, written: dict, files: dict | None = None, run_id: str = "run-1"):
        self.raw, self.drive = LocalFolderStore(tmp_path / "raw"), LocalFolderStore(tmp_path / "drive")
        for day, data in (files or {d: participant_volume(d) for d in written}).items():
            self.raw.put(SOURCE.path_for(day), data)
        self.nse, self.log = Nse(written), tmp_path / "write_times.csv"
        store = DataStore(self.drive, "data", ReceiptFolder(tmp_path / "receipts"), "flow-history", run_id,
                          clock=lambda: datetime(2026, 10, 23, tzinfo=UTC))  # fmt: skip
        sweep = LastWriteSweep(self.nse, SOURCE.path_for, self.log, clock=lambda: ist(WED, 21, 30))
        self.job = FlowTableJob(ParticipantVolumeValues(), self.raw, sweep, lambda: read_sweeps(self.log), _next,
                                PartTable(store, "flows/history/participant-volume", COLUMNS),
                                lambda: date(2026, 10, 23))  # fmt: skip

    def rows(self) -> list[dict]:
        data = self.drive.get("data/flows/history/participant-volume/2026/10/2026-10-23.run-1.csv")
        return list(csv.DictReader(io.StringIO(data.decode()))) if data else []


def test_an_evening_file_is_available_next_session_and_a_late_write_is_rewritten(tmp_path):
    desk = Desk(tmp_path, {MON: ist(MON, 19, 14), TUE: ist(WED, 10, 0)})
    result = desk.job.run([MON, TUE], set())
    assert result.entered == [MON, TUE] and result.rewritten == [TUE] and result.problems == []
    by_day = {row["session"]: row for row in desk.rows()}
    assert (by_day["2026-10-19"]["available_from"], by_day["2026-10-19"]["rewritten"]) == ("2026-10-20", "no")
    late = by_day["2026-10-20"]  # written Thu 22 Oct 10:00; Fri 23 Oct is muhurat only
    assert (late["available_from"], late["rewritten"]) == ("2026-10-26", "yes")
    assert len(desk.rows()) == 2 * 56 and set(read_sweeps(desk.log)) == {MON, TUE}


def test_no_last_modified_is_entered_as_rewritten_with_no_write_time(tmp_path):
    desk = Desk(tmp_path, {MON: None})
    result = desk.job.run([MON], set())
    row = desk.rows()[0]
    assert result.rewritten == [MON] and (row["last_modified"], row["rewritten"], row["available_from"]) == (
        "", "yes", "2026-10-20")  # fmt: skip


def test_an_unreachable_write_time_waits_for_the_next_run(tmp_path):
    desk = Desk(tmp_path, {MON: RawSourceUnavailable("HTTP 503"), TUE: ist(TUE, 19, 14)})
    result = desk.job.run([MON, TUE], set())
    assert result.entered == [TUE] and result.waiting == {MON: "HTTP 503"}
    assert result.problems == ["2026-10-19 waits: HTTP 503"]


def test_sessions_already_entered_are_skipped_and_logged_write_times_never_asked_again(tmp_path):
    written = {MON: ist(MON, 19, 14), TUE: ist(TUE, 19, 14)}
    Desk(tmp_path, written).job.run([MON], set())
    later = Desk(tmp_path, written, run_id="run-2")  # same folders and log, a later run that already entered MON
    result = later.job.run([MON, TUE], {MON})
    assert result.entered == [TUE] and later.nse.asked == [TUE]


def test_a_damaged_or_missing_archived_file_waits_named(tmp_path):
    desk = Desk(tmp_path, {MON: ist(MON, 19, 14), TUE: ist(TUE, 19, 14)}, files={MON: b"<html>"})
    result = desk.job.run([MON, TUE], set())
    assert result.entered == [] and desk.rows() == []
    assert "fao_participant_vol_19102026.csv" in result.waiting[MON]
    assert result.waiting[TUE].endswith("is in the manifest but not in Drive")


@pytest.mark.parametrize("entered", [set(), {MON}])
def test_nothing_new_writes_no_part(tmp_path, entered):
    desk = Desk(tmp_path, {MON: ist(MON, 19, 14)})
    desk.job.run([MON] if entered else [], entered)
    assert desk.drive.checksums("data/flows/history/participant-volume/2026/10") == {}  # no part, not an empty one


def test_the_first_write_time_log_is_created_with_its_folder(tmp_path):
    """Back-fill, 22 Oct 2026: research/data/flow_history/ does not exist in a fresh checkout."""
    desk = Desk(tmp_path, {MON: ist(MON, 19, 14)})
    desk.log = tmp_path / "fresh" / "flow_history" / "write_times.csv"
    desk.job.sweep = LastWriteSweep(desk.nse, SOURCE.path_for, desk.log, clock=lambda: ist(WED, 21, 30))
    desk.job.logged = lambda: read_sweeps(desk.log)
    assert desk.job.run([MON], set()).entered == [MON] and desk.log.is_file()
