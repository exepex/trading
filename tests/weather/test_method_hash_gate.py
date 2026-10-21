"""M1's records carry the tree's method hash (the v4 freeze plan, response 287, line 10 of response 250): M1's
METHOD_FILES include `fno/forecast_v4/terms.py`, so an edit there moved the hash of every committed record while
their values stayed the same. This gate fails the suite on a stale back-fill, as G7's does, so the freeze commit can
never pin records made on other code."""

import csv
import json
from pathlib import Path

from fno.weather.wiring import method_sha256

ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "research" / "forecasts" / "v4"


def test_every_committed_weather_record_carries_this_trees_method_hash():
    expected = method_sha256(ROOT / "fno")
    days = list((V4 / "weather").glob("*/*.json"))
    assert len(days) > 2_400
    assert {json.loads(p.read_text(encoding="utf-8"))["method_sha256"] for p in days} == {expected}
    for folder in ("weather_vix_v1", "weather_checklist_v0"):
        for file in (V4 / folder).glob("*.csv"):
            rows = list(csv.DictReader(file.open(encoding="utf-8")))
            assert rows and {r["method_sha256"] for r in rows} == {expected}, file
