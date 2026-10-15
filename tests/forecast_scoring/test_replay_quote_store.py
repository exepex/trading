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


@pytest.fixture
def drive(monkeypatch):
    drive = FakeDrive()
    drive.files[f"raw/{QUOTES}"] = (GOLDEN / QUOTES).read_bytes()
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: drive)
    return drive


def test_a_commit_after_a4b_replays_from_drive_as_one_before_it_from_its_files(tmp_path, drive):
    before = recompute_live_day(_inputs(tmp_path / "before", True), DAY, GENERATED)
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
