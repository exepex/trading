"""Story A15 on the committed files: the table runs from NSE's first served day, every row names a month file whose
SHA-256 equals its manifest row, the committed checks are what the code writes from the committed table, and the
overlap with the index-close closes has no real difference (only rounding and one listed special session)."""

import csv
import filecmp
from datetime import date

from fno.storage import wiring as storage
from fno.vix_history import wiring
from fno.vix_history.check_files import GAPS_FILE, LEVELS_FILE, OVERLAP_FILE
from fno.vix_history.source import NseVixHistorySource as Source
from fno.vix_history.source import month_start

ROWS = wiring.build_vix_table().rows()


def test_the_table_runs_from_nses_first_served_day_with_no_day_twice():
    days = [r["date"] for r in ROWS]
    assert days[0] == "2010-07-19" and days == sorted(set(days))
    assert len(days) >= 4019  # 19 Jul 2010 to 30 Sep 2026 at the first fill


def test_every_row_names_its_month_file_and_the_manifests_sha256():
    manifest = {f.day: f.sha256 for f in storage.build_manifest_folder().read(Source)}
    for r in ROWS:
        month = month_start(date.fromisoformat(r["date"]))
        assert r["source_path"] == Source.path_for(month)
        assert r["source_sha256"] == manifest[month], r["date"]


def test_the_committed_checks_are_what_the_code_writes_from_the_committed_table(tmp_path):
    wiring.build_vix_checks(tmp_path).write(ROWS)
    for name in (GAPS_FILE, LEVELS_FILE, OVERLAP_FILE):
        assert filecmp.cmp(tmp_path / name, wiring.CHECKS_FOLDER / name, shallow=False), name


def test_the_overlap_with_the_index_close_closes_has_no_real_difference():
    rows = list(csv.DictReader((wiring.CHECKS_FOLDER / OVERLAP_FILE).read_text(encoding="utf-8").splitlines()))
    assert {r["kind"] for r in rows} <= {"rounded", "only_in_index_close"}
    assert [r["date"] for r in rows if r["kind"] == "only_in_index_close"] == ["2024-03-02"]  # special session
