"""Story A17: every failure is named and leaves the table untouched; empty and malformed inputs are refused; the
command stops with one line and exit 1 on a Drive or setup failure."""

from argparse import Namespace
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.global_cues import wiring
from fno.global_cues.as_of import DECISION, value_for
from fno.global_cues.check_files import CHECK_FILES, CueChecks
from fno.global_cues.cli import cmd_global_cues
from fno.global_cues.collector import CueCollector
from fno.global_cues.job import GlobalCueJob
from fno.global_cues.other_sources import EiaBrentSource, FbilUsdInrSource, RbiUsdInrSource
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.treasury_source import TreasuryTenYearSource
from fno.global_cues.verify import CueTableVerifier
from fno.models import IST
from fno.research_data.calendar import CalendarError
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from fno.storage.report_files import csv_reports
from fno.storage.row_log import TableFileBroken
from tests.global_cues.fakes import EIA, RBI, FakeSource, csv_table, fake_file

SEEN = datetime(2026, 10, 15, 6, 15, tzinfo=IST)
GOOD = fake_file(("2026-10-13", 1.0), ("2026-10-14", 2.0))


class RefusingStore(LocalFolderStore):
    """Accepts the first copy, then refuses (as Drive's duplicate-name check would)."""

    def put(self, path, data):
        if any(self.folder.rglob("*_*")):
            raise RawFileConflict(f"{path} already exists")
        super().put(path, data)


def test_a_save_failure_after_some_copies_is_named_and_gives_no_values(tmp_path):
    store, log = RefusingStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeSource({"a.csv": GOOD, "b.csv": GOOD})
    result = CueCollector(None, store, log, lambda: SEEN).collect(source, date(2026, 1, 1), date(2026, 12, 31))
    assert result.failure.startswith("saving failed after 1 of 2 copies: b.csv") and result.values == []
    assert len(log.paths_by_sha256("fake")) == 1  # the saved copy stays logged


@pytest.mark.parametrize(
    "source, data, reason",
    [
        (TreasuryTenYearSource(), b"", "no Date and 10 Yr columns"),
        (TreasuryTenYearSource(), b'Date,"1 Mo"\n10/14/2026,4.1\n', "no Date and 10 Yr columns"),
        (RbiUsdInrSource(), RBI.split(b"<tr><td height")[0], "no values"),
        (FbilUsdInrSource(), b"[]", "no values"),
        (FbilUsdInrSource(), b'[{"subProdName": "INR / 1 EUR", "rate": 1}]', "none named 'INR / 1 USD'"),
    ],
)
def test_an_empty_answer_is_refused_never_taken_as_no_change(source, data, reason):
    with pytest.raises(ValueError, match=reason):
        source.parse(data)


def test_an_empty_table_file_gets_its_header_and_one_without_a_final_newline_is_refused(tmp_path):
    table = csv_table(tmp_path, "fake", lambda d: d)
    table.log.path.write_text("")
    result = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    values = result.collect(FakeSource({"a.csv": GOOD}), date(2026, 1, 1), date(2026, 12, 31)).values
    table.merge(values[:1], SEEN)
    assert table.rows()[0]["value_date"] == "2026-10-13"
    table.log.path.write_text(table.log.path.read_text().rstrip("\n"))
    before = table.log.path.read_bytes()
    with pytest.raises(TableFileBroken):
        table.merge(values, SEEN)
    assert table.log.path.read_bytes() == before


def test_verify_names_a_date_held_twice_rows_out_of_order_and_an_unreadable_copy(tmp_path):
    store, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeSource({"a.csv": GOOD})
    values = CueCollector(None, store, log, lambda: SEEN).collect(source, date(2026, 1, 1), date(2026, 12, 31)).values
    table = csv_table(tmp_path / "tables", "fake", lambda d: d)
    table.merge(values, SEEN)
    first, second = table.rows()
    verifier = CueTableVerifier(store, log, lambda d: d)
    assert "fake 2026-10-13: the table holds this date twice" in verifier.problems(source, [first, first, second])
    assert "fake: the table's dates are not in order" in verifier.problems(source, [second, first])
    path = next(iter(log.paths_by_sha256("fake").values()))
    (tmp_path / "raw" / path).write_bytes(b"<html>damaged</html>")
    assert "missing from the archive or not the logged bytes" in verifier.problems(source, [first])[0]


def test_no_rows_gives_no_value():
    assert value_for([], date(2026, 10, 15), DECISION, False, FakeSource({}).available_at) is None


def test_a_drive_or_setup_failure_stops_with_a_named_line_and_exit_1(monkeypatch, capsys):
    def no_drive():
        raise RuntimeError("set FNO_GDRIVE_FOLDER_ID to archive the global cues in Drive")

    monkeypatch.setattr(wiring, "build_job", no_drive)
    assert cmd_global_cues(Namespace(action="fill", cue=None, start=None, end=None)) == 1
    assert capsys.readouterr().out.startswith("STOPPED (RuntimeError): set FNO_GDRIVE_FOLDER_ID")


def test_a_new_years_empty_treasury_file_is_valid_but_a_cue_with_no_value_at_all_fails(tmp_path):
    assert TreasuryTenYearSource().parse(b'Date,"10 Yr"\n') == []
    assert TreasuryTenYearSource().parse(b'Date,"10 Yr"\n01/02/2027,\n') == []
    store, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    empty = FakeSource({"a.csv": b"date,value\n"})
    empty.parse = lambda data: []
    result = CueCollector(None, store, log, lambda: SEEN).collect(empty, date(2026, 1, 1), date(2026, 12, 31))
    assert result.failure == "no values in any file, nothing saved" and not (tmp_path / "raw").exists()


def test_the_fetch_time_is_taken_after_the_last_download(tmp_path):
    times = iter([datetime(2026, 10, 15, 9, 14, tzinfo=IST), datetime(2026, 10, 15, 9, 16, tzinfo=IST)])
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: next(times))
    result = collect.collect(FakeSource({"a.csv": GOOD}), date(2026, 1, 1), date(2026, 12, 31))
    assert result.fetched_at == datetime(2026, 10, 15, 9, 16, tzinfo=IST)


def test_a_shifted_brent_week_an_unreadable_rbi_row_and_a_changed_rbi_form_are_refused():
    shifted = EIA.replace(b"<td class='B3'>62.00</td>", b"<td class='B3 holiday'>62.00</td>")
    with pytest.raises(ValueError, match="has 4 cells, not 5"):
        EiaBrentSource().parse(shifted)
    nbsp = EIA.replace(b"<td class='B3'></td>", b"<td class='B3'>&nbsp;</td>")
    assert EiaBrentSource().parse(nbsp) == EiaBrentSource().parse(EIA)
    odd = RBI.replace(b'align="right">95.2477', b'align="right" class="x">95.2477')
    with pytest.raises(ValueError, match="2 rows but 1 readable"):
        RbiUsdInrSource().parse(odd)

    class NoViewState:
        def get(self, url, timeout):
            return type("A", (), {"text": "<form></form>", "raise_for_status": lambda self: None})()

    (request,) = RbiUsdInrSource().requests(date(2026, 10, 1), date(2026, 10, 14))
    with pytest.raises(ValueError, match="no __VIEWSTATE"):
        RbiUsdInrSource().download(NoViewState(), request)


def test_a_broken_revisions_file_writes_no_table_row_either(tmp_path):
    table = csv_table(tmp_path, "fake", lambda d: d)
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    values = collect.collect(FakeSource({"a.csv": GOOD}), date(2026, 1, 1), date(2026, 12, 31)).values
    table.merge(values[:1], SEEN)
    table.revision_log.path.write_text("cue,value_date,kind,table_value,new_value,source_sha256,seen_at")  # no newline
    before = table.log.path.read_bytes()
    with pytest.raises(TableFileBroken):
        table.merge(values, SEEN)
    assert table.log.path.read_bytes() == before


def test_a_stale_cue_and_a_run_stopped_midway_are_reported_with_what_came_before(tmp_path):
    tables = {c: csv_table(tmp_path / "tables", c, lambda d: d) for c in ("fake", "broken")}
    collect = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)

    class Broken(FakeSource):
        cue = "broken"

        def download(self, session, request):
            raise RuntimeError("Drive settings missing")

    job = GlobalCueJob(collect, tables, CueChecks(tables, csv_reports(tmp_path / "checks", CHECK_FILES)))
    lines, ok = job.run([FakeSource({"a.csv": GOOD}), Broken({"b.csv": GOOD})], date(2026, 1, 1), date(2026, 10, 30))
    assert not ok and "STALE: older than 7 days on 2026-10-30" in lines[0]
    assert lines[1].startswith("broken: FAILED, run stopped (RuntimeError): Drive settings missing")
    assert tables["fake"].rows()  # written before the stop, and said so above
    _, fresh = job.run([FakeSource({"a.csv": GOOD})], date(2026, 1, 1), date(2026, 10, 21))
    assert fresh  # 7 days old on 21 Oct: not stale (the boundary)


def test_after_the_calendars_last_year_the_label_is_never_guessed():
    calendar = wiring.storage.build_session_calendar()
    after = wiring.next_nse_session(calendar, calendar.first)
    assert after(date(2012, 3, 2)) == date(2012, 3, 5)  # before the calendar: the next weekday (Friday to Monday)
    with pytest.raises(CalendarError):
        after(date(calendar.last.year + 1, 1, 5))


def test_verify_names_a_wrong_label_and_a_first_seen_before_its_copy(tmp_path):
    store, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeSource({"a.csv": GOOD})
    values = CueCollector(None, store, log, lambda: SEEN).collect(source, date(2026, 1, 1), date(2026, 12, 31)).values
    table = csv_table(tmp_path / "tables", "fake", lambda d: d)
    table.merge(values, SEEN)
    verifier = CueTableVerifier(store, log, lambda d: d)
    row = dict(table.rows()[0], provenance="live")
    assert verifier.problems(source, [row]) == ["fake 2026-10-13: labelled live, should be backfilled"]
    early = dict(table.rows()[0], first_seen_at="2026-10-15T06:00:00+05:30")
    assert "before its copy was fetched" in verifier.problems(source, [early])[0]


def test_verify_names_a_cue_whose_table_is_empty_and_fill_refuses_a_reversed_range(monkeypatch, capsys):
    monkeypatch.setattr(wiring, "build_verifier", lambda: CueTableVerifier(None, None, None))
    empty = {s.cue: csv_table(Path("/nonexistent"), s.cue, lambda d: d) for s in wiring.SOURCES}
    monkeypatch.setattr(wiring, "build_tables", lambda: empty)
    assert cmd_global_cues(Namespace(action="verify", cue=["brent"], start=None, end=None)) == 1
    assert "brent: the table has no rows, nothing verified" in capsys.readouterr().out
    capsys.readouterr()
    assert cmd_global_cues(Namespace(action="fill", cue=None, start=date(2026, 10, 2), end=date(2026, 10, 1))) == 1
    assert capsys.readouterr().out.startswith("--from 2026-10-02 is after --to 2026-10-01")
