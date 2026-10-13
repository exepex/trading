"""Protocol v2's live pack (ChatGPT review 29, response 63): the per-field 15:00:00 cutoff, India VIX by NSE's own
timestamp, IV30 from live mids with G1's interpolation and flag, and the field-level provenance hash. Inputs are the
v2 golden cases' A4 snapshots (`research/forecasts/v2/golden/`), separate from `golden_iv30_rv20.csv`."""

import csv
import io
import json
from datetime import date

import pytest

from fno.config import ROOT
from fno.forecast.live_pack import CUTOFF, LIVE_MODE, LivePackBuilder, SnapshotFiles
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.research_engine.implied_vol import Black76
from fno.research_engine.live_features import LiveAtmIvMinusRealised
from tools.forecast_live_golden import main as check_golden

GOLDEN = ROOT / "research" / "forecasts" / "v2" / "golden"
DAY, SNAPSHOT_ID = date(2026, 10, 13), "nifty_20261013_145600"
OCT, NOV, DEC = date(2026, 10, 27), date(2026, 11, 23), date(2026, 12, 29)
COVERAGE = {"source": "fixture", "through": "2026-10-12", "sha256": "0" * 64}


def _files(case: str) -> SnapshotFiles:
    folder = GOLDEN / case / "quotes"
    read = lambda name: (folder / QuoteSnapshotRecorder.path(DAY, name, DATASET)).read_bytes()  # noqa: E731
    return SnapshotFiles(SNAPSHOT_ID, DATASET, read(f"{SNAPSHOT_ID}.csv"), read(f"{SNAPSHOT_ID}.meta.json"))


def _build(files: SnapshotFiles, coverage: dict = COVERAGE):
    rule = LiveAtmIvMinusRealised(CUTOFF, 0.065, Black76())
    return LivePackBuilder(rule).build(DAY, files, coverage, "calendar-fixture")


def _edit_rows(files: SnapshotFiles, edit) -> SnapshotFiles:
    rows = list(csv.DictReader(io.StringIO(files.csv_bytes.decode())))
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(edit(rows))
    return SnapshotFiles(files.snapshot_id, files.dataset, out.getvalue().encode(), files.meta_bytes)


def test_the_live_golden_cases_reproduce_byte_for_byte():
    assert check_golden([]) == 0


def test_case_a_interpolates_iv30_from_the_two_captured_expiries():
    pack = _build(_files("case_a"))
    # Hand value: ATM 22,400 at 14% (14 days) and 15% (41 days); total variance at 30 days:
    # (0.14^2*14*(41-30) + 0.15^2*41*(30-14)) / ((41-14)*30) = 0.021949 -> sqrt = 14.8151 points.
    assert pack.iv30.points == pytest.approx(14.8151, abs=1e-4)
    assert pack.iv30_status == "interpolated" and pack.iv30.expiries == (OCT, NOV)
    assert pack.value("india_vix") == 15.1 and pack.value("nifty_spot") == 22380.0
    assert pack.value(f"atm_iv_{DEC.isoformat()}") is None  # A4 captures two monthly expiries only
    assert pack.problems == []


def test_case_b_leaves_out_the_late_put_and_the_late_vix():
    pack = _build(_files("case_b"))
    assert pack.value(f"atm_iv_{NOV.isoformat()}") is None  # its put arrived at 15:00:01
    assert pack.iv30.points == pytest.approx(14.0, abs=1e-6) and pack.iv30_status == "flagged"
    assert pack.iv30.expiries == (OCT,)
    assert pack.value("india_vix") is None and pack.problems == ["no India VIX observed by 15:00"]


def test_vix_without_an_nse_timestamp_is_missing():
    files = _files("case_a")
    meta = json.loads(files.meta_bytes) | {"india_vix_time": ""}
    pack = _build(SnapshotFiles(files.snapshot_id, files.dataset, files.csv_bytes, json.dumps(meta).encode()))
    assert pack.value("india_vix") is None and "no India VIX observed by 15:00" in pack.problems


def test_futures_read_after_the_cutoff_give_no_futures_and_no_iv30():
    late = lambda rows: [r | {"request_sent_at": "2026-10-13T15:00:05+05:30"} for r in rows]  # noqa: E731
    pack = _build(_edit_rows(_files("case_a"), late))
    assert "no NIFTY futures observed by 15:00" in pack.problems
    assert "no India VIX observed by 15:00" in pack.problems  # VIX shares the same retrieval bound
    assert pack.value(f"future_{OCT.isoformat()}") is None and pack.iv30 is None and pack.iv30_status == "none"


def test_a_row_received_after_the_cutoff_changes_the_hash_but_no_value():
    base = _files("case_a")

    def add_late(rows):
        extra = rows[0] | {"response_received_at": "2026-10-13T15:00:01+05:30", "spot": "99999.00", "bid": "1"}
        return rows + [extra]

    clean, with_late = _build(base), _build(_edit_rows(base, add_late))
    assert [f for f in with_late.fields] == [f for f in clean.fields]
    assert with_late.iv30 == clean.iv30
    assert with_late.sha256 != clean.sha256  # the raw file hash is part of the provenance


def test_the_pack_hash_covers_closes_calendar_and_every_field():
    files = _files("case_a")
    pack = _build(files)
    body = json.loads(pack.canonical())
    assert body["mode"] == LIVE_MODE and body["cutoff"] == "2026-10-13T15:00:00+05:30"
    assert body["snapshot"]["snapshot_id"] == SNAPSHOT_ID and len(body["snapshot"]["csv_sha256"]) == 64
    assert {f["name"] for f in body["fields"]} >= {"nifty_spot", "india_vix", f"future_{OCT.isoformat()}"}
    assert all(f["source"] for f in body["fields"])
    assert _build(files, COVERAGE | {"through": "2026-10-09"}).sha256 != pack.sha256
    rule = LiveAtmIvMinusRealised(CUTOFF, 0.065, Black76())
    assert LivePackBuilder(rule).build(DAY, files, COVERAGE, "another-calendar").sha256 != pack.sha256
