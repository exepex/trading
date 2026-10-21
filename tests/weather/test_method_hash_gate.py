"""M1's records carry the tree's method hash (the v4 freeze plan, response 287, line 10 of response 250): M1's
METHOD_FILES include `fno/forecast_v4/terms.py`, so an edit there moved the hash of every committed record while
their values stayed the same. This gate fails the suite on a stale back-fill, as G7's does, so the freeze commit can
never pin records made on other code. It reads back-fill rows only: a live record is made once, on its own day, with
the code of that day, and is never regenerated (live from 22 Oct 2026, response 299 item 15)."""

import csv
import json
from pathlib import Path

from fno.forecast_v4_rules.records import BACKFILL
from fno.weather.wiring import method_sha256

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "research" / "forecasts" / "v4"


def test_every_committed_weather_record_carries_this_trees_method_hash():
    expected = method_sha256(ROOT / "fno")
    days = [json.loads(p.read_text(encoding="utf-8")) for p in (V4 / "weather").glob("*/*.json")]
    backfill = [day for day in days if day["label"] == BACKFILL]
    assert len(backfill) > 2_400
    assert {day["method_sha256"] for day in backfill} == {expected}
    for folder in ("weather_vix_v1", "weather_checklist_v0"):
        for file in (V4 / folder).glob("*.csv"):
            rows = [r for r in csv.DictReader(file.open(encoding="utf-8")) if r["label"] == BACKFILL]
            assert rows and {r["method_sha256"] for r in rows} == {expected}, file
