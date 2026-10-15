"""Story A4b: G4's live replay reads a later commit's Groww quote files from Drive, checked against the committed
sidecars, and a commit from before A4b from its own files; never a quiet switch to NSE's snapshot."""

import hashlib
import json
import shutil
from datetime import date, datetime

import pytest

from fno.config import ROOT
from fno.forecast_scoring.wiring import recompute_live_day
from fno.models import IST
from fno.quotes.drive_only_store import RawQuoteHashMismatch, RawQuoteMissing
from fno.storage import quote_wiring
from tests.quotes.drive_fakes import FakeDrive

DAY, GENERATED = date(2026, 10, 13), datetime(2026, 10, 13, 15, 5, tzinfo=IST)
GOLDEN = ROOT / "research" / "forecasts" / "v2" / "golden" / "case_a" / "quotes"
FOLDER = "groww/derivatives/quote-snapshots/2026/10"
QUOTES, SIDECAR = f"{FOLDER}/nifty_20261013_145600.csv", f"{FOLDER}/nifty_20261013_145600.meta.json"


def _inputs(root, with_quote_file: bool):
    """Golden case A's inputs, with the quote file's real hash added to its sidecar as csv_sha256 (the hand-built golden
    sidecar has no csv_sha256 key), laid out as a commit before A4b (quote file present) or after it (sidecar only)."""
    quotes = root / "research" / "data" / "quotes"
    shutil.copytree(GOLDEN, quotes)
    meta = json.loads((quotes / SIDECAR).read_text())
    meta["csv_sha256"] = hashlib.sha256((quotes / QUOTES).read_bytes()).hexdigest()
    (quotes / SIDECAR).write_text(json.dumps(meta))
    if not with_quote_file:
        (quotes / QUOTES).unlink()
    for name in ("nifty-panel", "calendar"):
        (root / "research" / "data" / name).symlink_to(ROOT / "research" / "data" / name)
    shutil.copy(ROOT / "config.yaml", root / "config.yaml")
    return root


@pytest.fixture(scope="module")
def before(tmp_path_factory):
    """The replay of a commit from before A4b (its quote file present), computed once: two tests compare against it."""
    return recompute_live_day(_inputs(tmp_path_factory.mktemp("before"), True), DAY, GENERATED)


@pytest.fixture
def drive(monkeypatch):
    drive = FakeDrive()
    drive.files[f"raw/{QUOTES}"] = (GOLDEN / QUOTES).read_bytes()
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: drive)
    return drive


def test_a_commit_after_a4b_replays_from_drive_as_one_before_it_from_its_files(tmp_path, drive, before):
    after = recompute_live_day(_inputs(tmp_path / "after", False), DAY, GENERATED)
    assert after == before and json.loads(after["pack.json"])["snapshot"]["dataset"].startswith("groww/")


def test_a_changed_or_missing_drive_copy_stops_the_replay(tmp_path, drive):
    inputs = _inputs(tmp_path, False)
    drive.files[f"raw/{QUOTES}"] += b"\n"
    with pytest.raises(RawQuoteHashMismatch):
        recompute_live_day(inputs, DAY, GENERATED)
    drive.files.clear()
    with pytest.raises(RawQuoteMissing):
        recompute_live_day(inputs, DAY, GENERATED)


def test_a_mixed_export_reads_each_day_s_file_from_where_it_is(tmp_path, drive, before):
    """Judge 111 addendum 2: an export holding an older day's quote file (pre-A4b) and only the sidecar of the replayed
    day reads the replayed day from Drive, not "no Groww snapshot" (which would switch quietly to NSE's)."""
    mixed = _inputs(tmp_path / "mixed", False)
    older = mixed / "research" / "data" / "quotes" / FOLDER / "nifty_20261012_145500.csv"
    older.write_bytes(b"snapshot_id,bid\nnifty_20261012_145500,1\n")  # a pre-A4b day still in the tree
    assert recompute_live_day(mixed, DAY, GENERATED) == before


def test_the_export_s_own_file_is_used_without_drive(tmp_path, monkeypatch):
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: pytest.fail("Drive must not be used"))
    inputs = _inputs(tmp_path, True)
    assert json.loads(recompute_live_day(inputs, DAY, GENERATED)["pack.json"])["snapshot"]["dataset"].startswith(
        "groww/"
    )
