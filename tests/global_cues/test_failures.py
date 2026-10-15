"""Story A17: every failure is named and leaves the table untouched; empty and malformed inputs are refused; the
command stops with one line and exit 1 on a Drive or setup failure."""

from argparse import Namespace
from datetime import date, datetime

import pytest

from fno.global_cues import wiring
from fno.global_cues.as_of import value_for
from fno.global_cues.cli import cmd_global_cues
from fno.global_cues.collector import CueCollector
from fno.global_cues.other_sources import FbilUsdInrSource, RbiUsdInrSource
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.table import CueTable, TableFileBroken
from fno.global_cues.treasury_source import TreasuryTenYearSource
from fno.global_cues.verify import CueTableVerifier
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore, RawFileConflict
from tests.global_cues.fakes import RBI, FakeSource, fake_file

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
        (TreasuryTenYearSource(), b'Date,"10 Yr"\n', "no Date and 10 Yr columns"),
        (TreasuryTenYearSource(), b'Date,"10 Yr"\n10/14/2026,\n', "no values"),
        (RbiUsdInrSource(), RBI.split(b"<tr><td height")[0], "no values"),
        (FbilUsdInrSource(), b"[]", "no values"),
        (FbilUsdInrSource(), b'[{"subProdName": "INR / 1 EUR", "rate": 1}]', "no values"),
    ],
)
def test_an_empty_answer_is_refused_never_taken_as_no_change(source, data, reason):
    with pytest.raises(ValueError, match=reason):
        source.parse(data)


def test_an_empty_table_file_gets_its_header_and_one_without_a_final_newline_is_refused(tmp_path):
    table = CueTable(tmp_path, "fake", lambda d: d)
    table.path.write_text("")
    result = CueCollector(None, LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log"), lambda: SEEN)
    values = result.collect(FakeSource({"a.csv": GOOD}), date(2026, 1, 1), date(2026, 12, 31)).values
    table.merge(values[:1], SEEN)
    assert table.rows()[0]["value_date"] == "2026-10-13"
    table.path.write_text(table.path.read_text().rstrip("\n"))
    before = table.path.read_bytes()
    with pytest.raises(TableFileBroken):
        table.merge(values, SEEN)
    assert table.path.read_bytes() == before


def test_verify_names_a_date_held_twice_rows_out_of_order_and_an_unreadable_copy(tmp_path):
    store, log = LocalFolderStore(tmp_path / "raw"), SnapshotLog(tmp_path / "log")
    source = FakeSource({"a.csv": GOOD})
    values = CueCollector(None, store, log, lambda: SEEN).collect(source, date(2026, 1, 1), date(2026, 12, 31)).values
    table = CueTable(tmp_path / "tables", "fake", lambda d: d)
    table.merge(values, SEEN)
    first, second = table.rows()
    verifier = CueTableVerifier(store, log)
    assert "fake 2026-10-13: the table holds this date twice" in verifier.problems(source, [first, first, second])
    assert "fake: the table's dates are not in order" in verifier.problems(source, [second, first])
    path = next(iter(log.paths_by_sha256("fake").values()))
    (tmp_path / "raw" / path).write_bytes(b"<html>damaged</html>")
    assert "missing from the archive or not the logged bytes" in verifier.problems(source, [first])[0]


def test_no_rows_gives_no_value():
    assert value_for([], date(2026, 10, 15), live_only=False) is None


def test_a_drive_or_setup_failure_stops_with_a_named_line_and_exit_1(monkeypatch, capsys):
    def no_drive():
        raise RuntimeError("set FNO_GDRIVE_FOLDER_ID to archive the global cues in Drive")

    monkeypatch.setattr(wiring, "build_job", no_drive)
    assert cmd_global_cues(Namespace(action="fill", cue=None, start=None, end=None)) == 1
    assert capsys.readouterr().out.startswith("STOPPED (RuntimeError): set FNO_GDRIVE_FOLDER_ID")
