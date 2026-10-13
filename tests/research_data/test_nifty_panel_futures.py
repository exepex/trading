"""Story A3 after judge 14: the NIFTY futures table, the session column on every row, and a build that never shrinks
the panel (small real subsets of NSE files, panel_fixtures.py)."""

import shutil
import zipfile
from datetime import date

import pytest
from panel_fixtures import DAYS, FIXTURES, FixtureCalendar, build, nifty_rows_in, panel_rows

from fno.research_data.nifty_panel import PanelBuildError
from fno.research_data.panel_rows import FUTURE_COLUMNS
from fno.research_data.panel_store import MANIFEST_FILE, PanelRangeError
from fno.storage.raw_source import NseLegacyFoSource
from fno.storage.wiring import RAW_AREA

ALL_DAYS = FixtureCalendar({day: kind for day, (_, _, kind) in DAYS.items()})


@pytest.mark.parametrize("day", DAYS, ids=str)
def test_each_day_has_every_nifty_future_of_its_file_and_every_row_its_session_kind(tmp_path, day):
    source, source_format, session = DAYS[day]
    manifest = build(tmp_path, day).manifest
    futures = panel_rows(tmp_path, day.year, "futures")
    raw_futures = nifty_rows_in(source.dataset, day, source.filename_for(day), futures=True)
    assert len(futures) == len(raw_futures) == manifest["days"][str(day)]["futures_rows"] >= 1
    assert {(r["source_format"], r["session"]) for r in futures} == {(source_format, session)}
    assert {r["session"] for r in panel_rows(tmp_path, day.year)} == {session}  # options too: muhurat closes are marked


def test_future_rows_copy_the_raw_values(tmp_path):
    build(tmp_path, date(2019, 10, 27))
    rows = panel_rows(tmp_path, 2019, "futures")
    assert tuple(rows[0]) == FUTURE_COLUMNS
    assert rows == [  # raw: FUTIDX,NIFTY,31-Oct-2019,0,XX,11675,11675,11614.05,11625,11625,19042,166084.27,13917825,...
        {"date": "2019-10-27", "expiry": "2019-10-31", "close": "11625.00", "settle": "11625.00", "volume": "19042",
         "open_interest": "13917825", "underlying": "11627.15", "source_format": "legacy", "session": "muhurat"},
    ]  # fmt: skip
    build(tmp_path / "udiff", date(2024, 3, 2))  # raw: IDF,NIFTY,2024-04-25 ... ClsPric 22640.60
    (future,) = panel_rows(tmp_path / "udiff", 2024, "futures")
    assert (future["expiry"], future["close"], future["session"]) == ("2024-04-25", "22640.60", "special")


def rewrite_legacy_file(tmp_path, day, change):
    folder = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, folder)
    path = folder / RAW_AREA / NseLegacyFoSource.path_for(day)
    with zipfile.ZipFile(path) as z:
        name, lines = z.namelist()[0], z.read(z.namelist()[0]).decode().splitlines(keepends=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, "".join(change(lines)))
    return folder


def test_a_day_without_nifty_futures_fails_the_build(tmp_path):
    day = date(2019, 1, 2)
    folder = rewrite_legacy_file(tmp_path, day, lambda lines: [x for x in lines if not x.startswith("FUTIDX,NIFTY,")])
    with pytest.raises(PanelBuildError, match="2019-01-02: fo02JAN2019bhav.csv.zip has no NIFTY futures rows"):
        build(tmp_path / "out", day, folder=folder)


def test_a_duplicate_future_fails_the_build(tmp_path):
    day = date(2019, 1, 2)
    folder = rewrite_legacy_file(tmp_path, day, lambda lines: [*lines, *[x for x in lines if x.startswith("FUTIDX,")]])
    with pytest.raises(PanelBuildError, match="2019-01-02: BadFile: duplicate contract 2019-01-02 2019-01-31"):
        build(tmp_path / "out", day, folder=folder)


def test_a_build_that_would_drop_days_is_refused_and_changes_nothing(tmp_path):
    build(tmp_path, date(2019, 1, 1), date(2024, 12, 31), calendar=ALL_DAYS)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    for start, end in ((date(2024, 1, 1), date(2024, 12, 31)), (date(2019, 1, 1), date(2024, 6, 30))):
        with pytest.raises(PanelRangeError, match="the panel holds 2019-01-01 to 2024-12-31"):
            build(tmp_path, start, end, calendar=ALL_DAYS)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_a_build_may_extend_the_panel_and_keeps_every_year(tmp_path):
    build(tmp_path, date(2019, 1, 1), date(2020, 12, 31), calendar=ALL_DAYS)
    manifest = build(tmp_path, date(2019, 1, 1), date(2024, 12, 31), calendar=ALL_DAYS).manifest
    assert sorted(manifest["days"]) == sorted(map(str, DAYS))
    assert sorted(p.name for p in tmp_path.glob("options_*")) == [f"options_{y}.csv.gz" for y in (2019, 2020, 2024)]
    assert (tmp_path / MANIFEST_FILE).is_file()


def test_the_command_refuses_a_narrower_range(tmp_path, monkeypatch, capsys):
    from fno import cli
    from fno.storage import wiring

    monkeypatch.setattr(wiring, "PANEL_FOLDER", tmp_path)
    (tmp_path / MANIFEST_FILE).write_text('{"start": "2019-01-01", "end": "2026-10-12"}\n')
    assert cli.main(["nifty-panel", "--from", "2026-01-01", "--to", "2026-10-12", "--raw-folder", str(FIXTURES)]) == 1
    assert "would drop days" in capsys.readouterr().out
