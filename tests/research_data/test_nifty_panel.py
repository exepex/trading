"""Story A3: the NIFTY option-chain panel's options table, its research-ready gate and determinism, on small real
subsets of NSE files (panel_fixtures.py)."""

import gzip
import hashlib
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

import pytest
from panel_fixtures import (
    CALENDAR,
    DAYS,
    FIXTURES,
    LEGACY_GAP,
    FixtureCalendar,
    build,
    inputs,
    nifty_rows_in,
    panel_rows,
    raw,
)

from fno.constants import ENV_GDRIVE_SERVICE_ACCOUNT_JSON
from fno.research_data.nifty_panel import PanelBuildError, build_nifty_panel
from fno.research_data.panel_rows import OPTION_COLUMNS, cents, whole
from fno.research_data.panel_store import MANIFEST_FILE, CsvGzPanelFolder
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from fno.storage.wiring import RAW_AREA


@pytest.mark.parametrize("day", DAYS, ids=str)
def test_each_day_has_every_nifty_option_of_its_file_with_both_files_fingerprinted(tmp_path, day):
    source, source_format, session = DAYS[day]
    manifest = build(tmp_path, day).manifest
    fo_name, index_name = source.filename_for(day), NseIndexCloseSource.filename_for(day)
    rows = [r for r in panel_rows(tmp_path, day.year) if r["date"] == day.isoformat()]
    assert len(rows) == len(nifty_rows_in(source.dataset, day, fo_name)) == manifest["days"][str(day)]["rows"]
    assert manifest["days"][str(day)] == {
        "session": session,  # special and muhurat sessions are real sessions, read from NSE's calendar
        "status": "ok",
        "source_format": source_format,
        "fo_file": fo_name,
        "fo_sha256": hashlib.sha256(raw(source.dataset, day, fo_name)).hexdigest(),
        "index_file": index_name,
        "index_sha256": hashlib.sha256(raw(NseIndexCloseSource.dataset, day, index_name)).hexdigest(),
        "rows": len(rows),
        "futures_rows": len(nifty_rows_in(source.dataset, day, fo_name, futures=True)),
    }
    assert {r["source_format"] for r in rows} == {source_format}


def test_rows_copy_the_raw_values_with_the_index_close_and_vix_of_the_day(tmp_path):
    build(tmp_path, date(2019, 10, 27))
    rows = panel_rows(tmp_path, 2019)
    assert tuple(rows[0]) == OPTION_COLUMNS
    assert rows[1] == {  # raw: OPTIDX,NIFTY,31-Oct-2019,9250,CE,0,0,0,1604.1,2382.85,0,0,0,0,27-OCT-2019
        "date": "2019-10-27", "expiry": "2019-10-31", "strike": "9250.00", "type": "CE", "close": "1604.10",
        "settle": "2382.85", "volume": "0", "open_interest": "0", "underlying": "11627.15", "vix": "15.59",
        "source_format": "legacy", "session": "muhurat",
    }  # fmt: skip
    assert {(r["underlying"], r["vix"]) for r in rows} == {("11627.15", "15.59")}  # Nifty 50 and India VIX closes


def test_current_format_wins_on_a_day_with_both_and_the_old_one_is_the_fallback(tmp_path):
    day = date(2024, 1, 2)
    assert build(tmp_path / "both", day).manifest["days"][str(day)]["source_format"] == "udiff"
    no_udiff = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, no_udiff)
    (no_udiff / RAW_AREA / NseDailyFoSource.path_for(day)).unlink()
    entry = build(tmp_path / "fallback", day, folder=no_udiff).manifest["days"][str(day)]
    assert (entry["source_format"], entry["fo_file"]) == ("legacy", "fo02JAN2024bhav.csv.zip")


def test_rows_are_sorted_and_contracts_unique(tmp_path):
    build(tmp_path, date(2024, 3, 2))  # the raw file lists 2024-04-25 before 2024-03-14
    keys = [(r["date"], r["expiry"], float(r["strike"]), r["type"]) for r in panel_rows(tmp_path, 2024)]
    assert keys == sorted(keys) and len(keys) == len(set(keys)) == 4


def test_same_raw_files_give_byte_identical_outputs(tmp_path):
    calendar = FixtureCalendar({day: kind for day, (_, _, kind) in DAYS.items()})
    first = build(tmp_path / "a", date(2019, 1, 1), date(2024, 12, 31), calendar=calendar)
    build(tmp_path / "b", date(2019, 1, 1), date(2024, 12, 31), calendar=calendar)
    names = sorted(p.name for p in (tmp_path / "a").iterdir())
    years = ("2019", "2020", "2024")
    assert names == sorted(["manifest.json", *(f"{t}_{y}.csv.gz" for t in ("options", "futures") for y in years)])
    for name in names:
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes(), name
    for name, file in first.manifest["files"].items():  # no build time or file name inside the gzip header either
        assert (tmp_path / "a" / name).read_bytes()[3:8] == bytes(5), "gzip flags and timestamp must be zero"
        data = (tmp_path / "a" / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == file["sha256"]
        assert hashlib.sha256(gzip.decompress(data)).hexdigest() == file["csv_sha256"]


def test_a_session_without_a_file_but_with_a_sourced_exception_is_left_out_and_listed(tmp_path):
    entry = build(tmp_path, LEGACY_GAP).manifest["days"][str(LEGACY_GAP)]
    assert entry["status"] == "no file" and "404" in entry["exception"]
    assert not list(tmp_path.glob("options_*.csv.gz"))


def test_a_session_without_a_file_or_exception_fails_the_build_naming_it_and_writes_nothing(tmp_path):
    (tmp_path / "out").mkdir()
    previous = '{"start": "2021-03-30", "end": "2021-03-30"}\n'  # a panel of the same range
    (tmp_path / "out" / MANIFEST_FILE).write_text(previous)
    with pytest.raises(PanelBuildError) as failure:
        build(tmp_path / "out", LEGACY_GAP, exceptions={})
    assert failure.value.problems == [
        "2021-03-30: no file: no file and no sourced exception in ['nse/derivatives/fo-bhavcopy-legacy']"
    ]
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [MANIFEST_FILE]
    assert (tmp_path / "out" / MANIFEST_FILE).read_text() == previous


def without_index(tmp_path: Path, day: date, keep_lines: int | None) -> Path:
    folder = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, folder)
    index = folder / RAW_AREA / NseIndexCloseSource.path_for(day)
    if keep_lines is None:
        index.unlink()
    else:
        index.write_text("".join(index.read_text().splitlines(keepends=True)[:keep_lines]))
    return folder


def test_no_index_file_fails_and_never_leaves_underlying_empty(tmp_path):
    day = date(2019, 1, 2)
    with pytest.raises(PanelBuildError) as failure:
        build(tmp_path / "out", day, folder=without_index(tmp_path, day, None))
    assert failure.value.problems[0].startswith("2019-01-02: no index close: no file and no sourced exception")
    assert not (tmp_path / "out").exists()


def test_an_index_file_without_india_vix_fails(tmp_path):
    day = date(2020, 2, 1)  # header, Nifty 50, Nifty Bank; India VIX dropped
    with pytest.raises(PanelBuildError, match=r"2020-02-01: .*no closing value for \['India VIX'\]"):
        build(tmp_path / "out", day, folder=without_index(tmp_path, day, 3))


def test_a_duplicate_contract_fails_the_build(tmp_path):
    day = date(2019, 1, 2)
    folder = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, folder)
    path = folder / RAW_AREA / NseLegacyFoSource.path_for(day)
    with zipfile.ZipFile(path) as z:
        name, text = z.namelist()[0], z.read(z.namelist()[0]).decode()
    lines = text.splitlines(keepends=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, "".join([*lines, lines[1]]))
    with pytest.raises(PanelBuildError, match="2019-01-02: BadFile: duplicate contract 2019-01-02 2019-01-31 "):
        build(tmp_path / "out", day, folder=folder)


def test_values_are_copied_never_rounded():
    assert cents("1604.1") == "1604.10" and cents("9250") == "9250.00" and whole("4287267") == "4287267"
    with pytest.raises(ValueError):
        cents("14.2425")
    with pytest.raises(ValueError):
        whole("12.5")


def test_only_sessions_are_asked_for_and_nothing_is_written_to_drive(tmp_path):
    asked: list[str] = []
    fo, index = inputs(asked=asked)
    sink = CsvGzPanelFolder(tmp_path)
    build_nifty_panel(fo, index, date(2019, 10, 26), date(2019, 10, 28), calendar=CALENDAR, exceptions={}, sink=sink)
    # Sat 26 Oct closed, Sun 27 muhurat, Mon 28 Oct a holiday (Diwali Balipratipada): only the 27th is asked for
    assert {p.rsplit("/", 1)[-1] for p in asked} == {"fo27OCT2019bhav.csv.zip", "ind_close_all_27102019.csv"}


def test_the_command_builds_from_a_local_raw_folder_without_drive(tmp_path, monkeypatch, capsys):
    from fno import cli
    from fno.storage import wiring

    monkeypatch.delenv(ENV_GDRIVE_SERVICE_ACCOUNT_JSON, raising=False)
    monkeypatch.setattr(wiring, "PANEL_FOLDER", tmp_path)
    args = ["nifty-panel", "--from", "2020-02-01", "--to", "2020-02-02", "--raw-folder", str(FIXTURES)]
    assert cli.main(args) == 0
    assert "sessions: 1 ok" in capsys.readouterr().out
    assert json.loads((tmp_path / MANIFEST_FILE).read_text())["days"]["2020-02-01"]["session"] == "special"


def test_an_empty_range_is_refused_before_anything_is_replaced(tmp_path):
    with pytest.raises(ValueError, match="empty range"):
        build(tmp_path, date(2020, 2, 2), date(2020, 2, 1))
    assert not tmp_path.joinpath(MANIFEST_FILE).exists()
