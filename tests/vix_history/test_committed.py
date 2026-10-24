"""Story A15 on the moved data (O9b's pilot: the table and checks in Drive with receipts, read here from the verified
cache after `python -m fno data-cache sync data/vix`): the table runs from NSE's first served day, every row names a
month file whose SHA-256 equals its manifest row, the checks in Drive are what the code writes from the table, and the
overlap with the index-close closes has no real difference (only rounding and one listed special session)."""

import csv
from datetime import date

import pytest

from fno.storage import wiring as storage
from fno.storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots
from fno.storage.report_files import CsvReportFile
from fno.vix_history import wiring
from fno.vix_history.check_files import CHECK_FILES, OVERLAP_FILE
from fno.vix_history.source import NseVixHistorySource as Source
from fno.vix_history.source import month_start
from tests.data_cache import cached_series

pytestmark = pytest.mark.data


@pytest.fixture(scope="module")
def rows():
    return cached_series(ReceiptedRowLog, wiring.DRIVE_TABLE).rows()


def _check(name: str) -> bytes:
    stem = name.rsplit(".", 1)[0]
    return cached_series(ReceiptedSnapshots, wiring.DRIVE_CHECKS.format(stem=stem)).latest_bytes() or b""


def test_the_table_runs_from_nses_first_served_day_with_no_day_twice(rows):
    days = [r["date"] for r in rows]
    assert days[0] == "2010-07-19" and days == sorted(set(days))
    assert len(days) >= 4019  # 19 Jul 2010 to 30 Sep 2026 at the first fill


def test_every_row_names_its_month_file_and_the_manifests_sha256(rows):
    manifest = {f.day: f.sha256 for f in storage.build_manifest_folder().read(Source)}
    for r in rows:
        month = month_start(date.fromisoformat(r["date"]))
        assert r["source_path"] == Source.path_for(month)
        assert r["source_sha256"] == manifest[month], r["date"]


def test_the_checks_in_drive_are_what_the_code_writes_from_the_table(rows, tmp_path):
    wiring.build_vix_checks({name: CsvReportFile(tmp_path / name) for name in CHECK_FILES}).write(rows)
    for name in CHECK_FILES:
        assert (tmp_path / name).read_bytes() == _check(name), name


def test_the_overlap_with_the_index_close_closes_has_no_real_difference():
    found = list(csv.DictReader(_check(OVERLAP_FILE).decode("utf-8").splitlines()))
    assert {r["kind"] for r in found} <= {"rounded", "only_in_index_close"}
    assert [r["date"] for r in found if r["kind"] == "only_in_index_close"] == ["2024-03-02"]  # special session
