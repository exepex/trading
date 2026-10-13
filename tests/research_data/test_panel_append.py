"""Story A13: a day appended to the NIFTY panel equals A3's build of that day, old bytes and manifest entries never
change, and a rewrite, a reorder or an interrupted append is refused. Real 2024 subsets of NSE files
(panel_fixtures.py)."""

import gzip
import json
from datetime import date

import pytest
from panel_fixtures import FixtureCalendar, build, inputs

from fno.research_data.nifty_panel import NiftyPanelBuilder
from fno.research_data.panel_append import AppendRefused, PanelAppender
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_data.panel_rows import FUTURES, OPTIONS
from fno.research_data.panel_store import MANIFEST_FILE, PanelDay
from fno.storage.wiring import build_file_exceptions

FIRST, SECOND = date(2024, 1, 2), date(2024, 3, 2)  # a regular UDiFF day and a Saturday special session
CALENDAR = FixtureCalendar({FIRST: "regular", SECOND: "special"})
STAMP = {"appended_at": "2024-03-02T21:41:00+05:30", "calendar_sha256": "fixture"}


def _built(day: date) -> list[PanelDay]:
    fo, index = inputs()
    return list(NiftyPanelBuilder(fo, index, CALENDAR, build_file_exceptions()).days(day, day))


def _manifest(folder) -> dict:
    return json.loads((folder / MANIFEST_FILE).read_text())


@pytest.fixture
def grown(tmp_path):
    """A3's panel of the first day, then the second day appended; and A3's build of both days at once."""
    appended, whole = tmp_path / "appended", tmp_path / "whole"
    build(appended, FIRST, calendar=CALENDAR)
    before = {name: (appended / name).read_bytes() for name in ("options_2024.csv.gz", "futures_2024.csv.gz")}
    old_manifest = _manifest(appended)
    assert PanelAppender(appended).append(_built(SECOND), STAMP) == 1
    build(whole, FIRST, SECOND, calendar=CALENDAR)
    return appended, whole, before, old_manifest


def test_an_appended_day_equals_a3s_build_row_for_row(grown):
    appended, whole, _, _ = grown
    for name in ("options_2024.csv.gz", "futures_2024.csv.gz"):
        assert gzip.decompress((appended / name).read_bytes()) == gzip.decompress((whole / name).read_bytes())
    new, rebuilt = _manifest(appended), _manifest(whole)
    assert new["days"][str(SECOND)] == rebuilt["days"][str(SECOND)] | STAMP
    assert new["end"] == rebuilt["end"] == str(SECOND)
    for name, recorded in new["files"].items():
        assert (recorded["csv_sha256"], recorded["rows"]) == (
            rebuilt["files"][name]["csv_sha256"],
            rebuilt["files"][name]["rows"],
        )


def test_old_bytes_are_a_prefix_and_old_entries_are_unchanged(grown):
    appended, _, before, old_manifest = grown
    for name, old in before.items():
        assert (appended / name).read_bytes().startswith(old)
    new = _manifest(appended)
    assert new["days"][str(FIRST)] == old_manifest["days"][str(FIRST)]
    assert {k: new[k] for k in ("start", "columns", "calendar_sha256")} == {
        k: old_manifest[k] for k in ("start", "columns", "calendar_sha256")
    }


def test_the_reader_returns_the_appended_day(grown):
    appended, whole, _, _ = grown
    assert read_nifty_panel(appended).options[SECOND] == read_nifty_panel(whole).options[SECOND]
    assert [s.day for s in read_nifty_panel(appended).sessions][-2:] == [FIRST, SECOND]


def test_a_day_already_present_or_out_of_order_is_refused_and_nothing_is_written(grown):
    appended, _, _, _ = grown
    files = {p.name: p.read_bytes() for p in appended.iterdir()}
    for days in (_built(SECOND), _built(FIRST)):
        with pytest.raises(AppendRefused, match="never rewritten"):
            PanelAppender(appended).append(days, STAMP)
    assert {p.name: p.read_bytes() for p in appended.iterdir()} == files


def test_files_that_no_longer_match_the_manifest_are_refused(tmp_path):
    build(tmp_path, FIRST, calendar=CALENDAR)
    (tmp_path / "options_2024.csv.gz").write_bytes((tmp_path / "options_2024.csv.gz").read_bytes() + b"x")
    with pytest.raises(AppendRefused, match="interrupted append"):
        PanelAppender(tmp_path).append(_built(SECOND), STAMP)


def test_a_new_year_starts_its_own_file_with_a3s_header(grown):
    appended, _, _, _ = grown
    day = date(2025, 1, 1)
    option = ("2025-01-01", "2025-01-30", "23000.00", "CE", "10.00", "10.00", "5", "50", "23500.00", "14.00",
              "udiff", "regular")  # fmt: skip
    future = ("2025-01-01", "2025-01-30", "23550.00", "23550.00", "9", "90", "23500.00", "udiff", "regular")
    entry = {"session": "regular", "status": "ok", "rows": 1, "futures_rows": 1}
    PanelAppender(appended).append([PanelDay(day, entry, {OPTIONS: [option], FUTURES: [future]})], STAMP)
    panel = read_nifty_panel(appended)
    assert panel.options[day][0].strike == 23000.0 and panel.future_on(day, date(2025, 1, 30)).close == 23550.0
    assert _manifest(appended)["files"]["options_2025.csv.gz"]["rows"] == 1


def test_a_panel_with_other_columns_is_refused(tmp_path):
    build(tmp_path, FIRST, calendar=CALENDAR)
    manifest = _manifest(tmp_path)
    manifest["columns"][OPTIONS] = manifest["columns"][OPTIONS][:-1]
    (tmp_path / MANIFEST_FILE).write_text(json.dumps(manifest))
    with pytest.raises(AppendRefused, match="columns"):
        PanelAppender(tmp_path).append(_built(SECOND), STAMP)
