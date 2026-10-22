"""O9b step 1b through A17's composition root: the public cue files move into Drive with receipts and read back equal;
`build_tables` then reads the public tables from Drive (a fill's new rows are a new part, never a repository file);
the checks are written as Drive snapshots; a file that grew after its move is caught up. Made-up values throughout."""

from __future__ import annotations

import itertools
from datetime import date, datetime

import pytest

from fno.global_cues import wiring
from fno.global_cues.collection import SourcedValue
from fno.global_cues.source import CueValue
from fno.models import IST
from fno.storage import data_wiring
from fno.storage.raw_store import LocalFolderStore

HEADER = "value_date,value,source_sha256,first_seen_at,provenance\n"
ROW = "2026-10-{day},{value},{sha},2026-10-{day}T06:00:00+05:30,live\n"
PUBLIC = ("us10y", "brent", "usdinr_rbi")


def table(*days) -> str:
    return HEADER + "".join(ROW.format(day=d, value=f"{d}.5", sha="a" * 64) for d in days)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A checkout with the public cue files, Drive as a local folder, receipts and cache under the checkout."""
    drive, cues = LocalFolderStore(tmp_path / "drive"), tmp_path / "research" / "data" / "global-cues"
    for cue in PUBLIC:
        (cues / f"{cue}.csv").parent.mkdir(parents=True, exist_ok=True)
        (cues / f"{cue}.csv").write_text(table(13, 14))
    (cues / "checks").mkdir()
    (cues / "checks" / "gaps.csv").write_text("cue,date,kind\n")
    (cues / "checks" / "overlap_usdinr.csv").write_text("date,kind\n")
    (cues / "revisions.csv").write_text("cue,value_date,kind,table_value,new_value,source_sha256,seen_at\n")
    (cues / "us_trading_dates.csv").write_text("date,in_sp500,in_nasdaq100\n2026-10-13,1,1\n")
    monkeypatch.setattr(data_wiring, "build_owner_drive", lambda env: drive)
    monkeypatch.setattr(data_wiring, "REPOSITORY", tmp_path)
    runs = itertools.count(1)  # one run id per series, later each time, as separate runs' are
    monkeypatch.setattr(data_wiring, "new_run_id", lambda: f"20261022T{next(runs):06d}Z-aaaaaa")
    monkeypatch.setattr(wiring, "CUES_FOLDER", cues)
    monkeypatch.setattr(wiring, "CHECKS_FOLDER", cues / "checks")
    monkeypatch.setattr(wiring, "TRADING_DATES_FILE", cues / "us_trading_dates.csv")
    return tmp_path


def test_the_files_move_and_the_tables_are_then_read_from_drive(repo):
    lines = wiring.move_public_cues_to_drive()
    assert len(lines) == 7 and all(": moved to Drive and read back equal" in line for line in lines)
    assert lines[3].startswith("revisions.csv:") and lines[4].startswith("us_trading_dates.csv:")
    assert lines[5].startswith("checks/gaps.csv:") and lines[6].startswith("checks/overlap_usdinr.csv:")
    receipts = sorted(p.relative_to(repo / "receipts").as_posix() for p in (repo / "receipts").rglob("*.sha256"))
    assert [r.split("/")[2] for r in receipts] == [
        "brent",
        "checks",
        "checks",
        "revisions",
        "us10y",
        "us_trading_dates",
        "usdinr_rbi",
    ]
    assert all(line.split(": ")[1].startswith("already in Drive") for line in wiring.move_public_cues_to_drive())
    (repo / "research" / "data" / "global-cues" / "brent.csv").unlink()  # readers no longer read the repository
    assert [r["value"] for r in wiring.build_tables(include_private=False)["brent"].rows()] == ["13.5", "14.5"]


def test_a_fill_appends_a_part_and_a_grown_file_is_caught_up_before_the_merge(repo):
    wiring.move_public_cues_to_drive()
    (repo / "research" / "data" / "global-cues" / "us10y.csv").write_text(table(13, 14, 15))  # the old job ran
    caught = wiring.move_public_cues_to_drive()[0]
    assert caught.startswith("us10y.csv: Drive held") and "caught up and read back equal" in caught
    cue = wiring.build_tables(include_private=False)["us10y"]
    seen = datetime(2026, 10, 16, 6, 0, tzinfo=IST)
    assert cue.merge([SourcedValue(CueValue(date(2026, 10, 16), 4.25), "b" * 64)], seen).added == 1
    assert [r["value_date"] for r in cue.rows()] == ["2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16"]
    assert len(list((repo / "receipts" / "data" / "global-cues" / "us10y").glob("*.sha256"))) == 3


def test_the_checks_are_written_as_drive_snapshots(repo):
    wiring.move_public_cues_to_drive()
    tables = wiring.build_tables(include_private=False)
    lines = wiring._checks(tables).write()
    assert lines[-2].startswith("gaps: ")
    for check in ("gaps", "overlap_usdinr"):  # the moved file and this run's snapshot, each
        assert len(list((repo / "receipts" / "data" / "global-cues" / "checks" / check).glob("*.sha256"))) == 2
