"""Story A15: the table is append-only (a day present is never rewritten, a hole never filled from behind), comes
only from the first archived file, and recomputing it from the archive gives the same rows."""

import hashlib
from datetime import date, datetime

import pytest

from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from fno.storage.row_log import CsvRowLog
from fno.vix_history.month_file import NseVixJsonReader, VixDay
from fno.vix_history.source import NseVixHistorySource as Source
from fno.vix_history.table import VixDailyTable, VixRow, VixTableConflict
from fno.vix_history.table_builder import VixTableBuilder
from fno.vix_history.verify import VixTableVerifier
from tests.vix_history.nse_vix import august_2010, july_2010

JULY, AUGUST, SEPTEMBER = date(2010, 7, 1), date(2010, 8, 1), date(2010, 9, 1)
SEEN = datetime(2026, 10, 15, 5, 30, tzinfo=IST)


def row(day, close, sha="s"):
    return VixRow(VixDay(day, 1.0, 2.0, 0.5, close), "p", sha, SEEN)


def archive_with(tmp_path, files):
    raw = LocalFolderStore(tmp_path / "raw")
    for month, data in files.items():
        raw.put(Source.path_for(month), data)
    return raw


def manifest_of(raw, months=(JULY, AUGUST, SEPTEMBER)):
    found = {m: raw.get(Source.path_for(m)) for m in months}
    return {m: hashlib.sha256(data).hexdigest() for m, data in found.items() if data is not None}


def builder(raw, table, clock=lambda: SEEN, manifest=None):
    rows = manifest if manifest is not None else manifest_of(raw)
    return VixTableBuilder(raw, Source.path_for, NseVixJsonReader(), table, clock, lambda: rows)


def test_appending_keeps_earlier_bytes_and_skips_a_day_already_held(tmp_path):
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    assert table.append([row(date(2010, 7, 19), 20.71)]) == 1
    before = table.log.path.read_bytes()
    assert table.append([row(date(2010, 7, 19), 20.71), row(date(2010, 7, 20), 20.38)]) == 1
    assert table.log.path.read_bytes().startswith(before)
    assert [r["close"] for r in table.rows()] == ["20.71", "20.38"]


def test_a_day_present_is_never_rewritten(tmp_path):
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    table.append([row(date(2010, 7, 19), 20.71)])
    before = table.log.path.read_bytes()
    with pytest.raises(VixTableConflict, match="2010-07-19: the table already holds other values"):
        table.append([row(date(2010, 7, 19), 20.72)])
    assert table.log.path.read_bytes() == before


def test_a_hole_is_never_filled_from_behind(tmp_path):
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    table.append([row(date(2010, 7, 19), 20.71), row(date(2010, 7, 21), 20.0)])
    with pytest.raises(VixTableConflict, match="a hole is never filled"):
        table.append([row(date(2010, 7, 20), 20.38)])


def test_the_table_is_built_from_the_archived_files_with_their_sha_and_first_seen_time(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010(), AUGUST: august_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    result = builder(raw, table).extend([JULY, AUGUST])
    assert result.added == 3 and not result.stopped_at
    first = table.rows()[0]
    assert first == {
        "date": "2010-07-19",
        "open": "19.7",
        "high": "20.87",
        "low": "19.36",
        "close": "20.71",
        "source_path": Source.path_for(JULY),
        "source_sha256": hashlib.sha256(july_2010()).hexdigest(),
        "first_seen_at": SEEN.isoformat(),
    }


def test_a_month_missing_from_the_archive_stops_the_table_there_and_is_named(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010(), SEPTEMBER: august_2010().replace(b"AUG", b"SEP")})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    result = builder(raw, table).extend([JULY, AUGUST, SEPTEMBER])
    assert result.stopped_at == "2010-08: not in the archive"
    assert table.last_day() == date(2010, 7, 20)  # September waits: no hole is left to fill from behind
    assert "table STOPPED: 2010-08: not in the archive" in result.lines(table)


def test_a_second_run_adds_nothing_and_changes_no_byte(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    builder(raw, table).extend([JULY])
    before = table.log.path.read_bytes()
    later = datetime(2026, 11, 1, tzinfo=IST)
    assert builder(raw, table, clock=lambda: later).extend([JULY]).added == 0
    assert table.log.path.read_bytes() == before  # first_seen_at stays the first time


def test_recomputing_from_the_archive_gives_the_table_and_finds_a_planted_change(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010(), AUGUST: august_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    builder(raw, table).extend([JULY, AUGUST])
    manifest = {JULY: hashlib.sha256(july_2010()).hexdigest(), AUGUST: hashlib.sha256(august_2010()).hexdigest()}
    verifier = VixTableVerifier(raw, Source.path_for, NseVixJsonReader(), manifest)
    assert verifier.problems(table.rows()) == []
    planted = table.rows()
    planted[1]["close"] = "20.39"
    assert verifier.problems(planted) == [
        f"2010-07-20: table {tuple(planted[1].values())[:7]}, archived file "
        f"{('2010-07-20', '20.71', '20.71', '19.61', '20.38', Source.path_for(JULY), manifest[JULY])}"
    ]
    assert verifier.problems(table.rows()[:1]) != []  # a day the table lacks is named too
    wrong = VixTableVerifier(raw, Source.path_for, NseVixJsonReader(), {**manifest, JULY: "0" * 64})
    assert "2010-07: SHA-256 differs from the manifest" in wrong.problems(table.rows())


def test_verify_names_every_day_of_a_month_the_table_lacks_and_a_table_cut_short(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010(), AUGUST: august_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    builder(raw, table).extend([JULY, AUGUST])
    manifest = {JULY: hashlib.sha256(july_2010()).hexdigest(), AUGUST: hashlib.sha256(august_2010()).hexdigest()}
    verifier = VixTableVerifier(raw, Source.path_for, NseVixJsonReader(), manifest)
    rows = table.rows()
    without_july = [r for r in rows if not r["date"].startswith("2010-07")]
    assert [p.split(":")[0] for p in verifier.problems(without_july)] == ["2010-07-19", "2010-07-20"]
    assert [p.split(":")[0] for p in verifier.problems(rows[:2])] == ["2010-08-02"]  # cut short at the end
    assert len(verifier.problems([])) == 3  # empty table: every archived day is named


def test_verify_names_a_month_the_manifest_does_not_hold(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    builder(raw, table).extend([JULY])
    verifier = VixTableVerifier(raw, Source.path_for, NseVixJsonReader(), {})
    assert verifier.problems(table.rows())[0] == "2010-07: no manifest row for the archived file"


def test_a_month_whose_bytes_differ_from_its_manifest_row_stops_the_table(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    wrong = builder(raw, table, manifest={JULY: "0" * 64}).extend([JULY])
    assert wrong.stopped_at == "2010-07: archived file's SHA-256 differs from the manifest" and table.rows() == []
    missing = builder(raw, table, manifest={}).extend([JULY])
    assert missing.stopped_at == "2010-07: archived file has no manifest row" and table.rows() == []


def test_an_empty_table_file_gets_its_header_and_a_file_without_a_final_newline_is_refused(tmp_path):
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    table.log.path.write_text("")
    table.append([row(date(2010, 7, 19), 20.71)])
    assert table.rows()[0]["date"] == "2010-07-19"
    table.log.path.write_text(table.log.path.read_text().rstrip("\n"))
    before = table.log.path.read_bytes()
    with pytest.raises(VixTableConflict, match="does not end with a new line"):
        table.append([row(date(2010, 7, 20), 20.38)])
    assert table.log.path.read_bytes() == before


def test_verify_names_a_day_held_twice_and_rows_out_of_order(tmp_path):
    raw = archive_with(tmp_path, {JULY: july_2010()})
    table = VixDailyTable(CsvRowLog(tmp_path / "vix.csv"))
    builder(raw, table).extend([JULY])
    verifier = VixTableVerifier(raw, Source.path_for, NseVixJsonReader(), manifest_of(raw, (JULY,)))
    first, second = table.rows()
    assert "2010-07-19: the table holds this day twice" in verifier.problems([first, first, second])
    assert "the table's days are not in date order" in verifier.problems([second, first])
