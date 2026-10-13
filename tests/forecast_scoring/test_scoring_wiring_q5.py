"""Judge 64 (e): live question 5 goes through G4's real composition root (`score_forecasts`) and is resolved against
the forecast's own 15:00 pack IV30, not the panel's. Planted disagreement: the next-20-day RV is 4.62 points, the pack
says 5.0 (outcome yes) and the panel says 4.0 (outcome no); swapping the live resolver to the panel fails this test.
Only the heavy inputs are replaced (freeze checks, the panel history, the closes file and the calendar)."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from fno.constants import BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV
from fno.forecast.backfill import BACKFILL_FILE
from fno.forecast.capture import LIVE_FOLDER
from fno.forecast.iv30 import AtmIv30
from fno.forecast.record_files import records_csv_v2
from fno.forecast.schema import RECORD_COLUMNS, ForecastRecord
from fno.forecast.schema_v2 import ForecastRecordV2
from fno.forecast_scoring import wiring
from fno.forecast_scoring.score_inputs import CLOSE_PROXY, LIVE
from fno.forecast_scoring.score_sources import Receipt
from fno.freeze_sections import FORECAST_SCORES
from fno.models import IST
from fno.research_data.panel_reader import SessionClose
from tests.forecast_scoring.scoring_fixtures import CALENDAR, FIRST, closes, horizon_day

AS_OF = horizon_day(FIRST, 20)
PANEL_1530 = AtmIv30(4.0, False, (date(2025, 1, 30),))
PACK = {"iv30": {"points": 5.0, "status": "interpolated", "expiries": ["2025-01-30", "2025-02-27"]}}


class _Receipts:
    def __init__(self, receipts):
        self.receipts = receipts

    def receipt(self, day):
        return self.receipts.get(day)


class _PanelHistory:
    """The panel's view: close-proxy IV30 of 4.0 points on every day it covers (through the as-of day)."""

    panel = SimpleNamespace(sessions=(SessionClose(AS_OF, "regular", 1.0, 1.0),))

    @staticmethod
    def iv30(day):
        return PANEL_1530

    @staticmethod
    def horizon_day(day, sessions):
        return horizon_day(day, sessions)


def _repository(root) -> Receipt:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / BACKFILL_FILE).parent.mkdir(parents=True)
    (root / BACKFILL_FILE).write_bytes(gzip.compress((",".join(RECORD_COLUMNS) + "\n").encode()))
    cutoff = datetime(2025, 1, 1, 15, 0, tzinfo=IST)
    base = ForecastRecord(BOOK1_RULES, FIRST, cutoff, FORECAST_Q5_RV_BELOW_IV, 0.7, "book1/v1", "a" * 64)
    text = records_csv_v2([ForecastRecordV2(base, LIVE, "interpolated", datetime(2025, 1, 1, 15, 5, tzinfo=IST))])
    pack = json.dumps(PACK, sort_keys=True).encode()
    folder = root / LIVE_FOLDER / "2025"
    folder.mkdir(parents=True)
    (folder / "2025-01-01_forecasts.csv").write_text(text, encoding="utf-8")
    (folder / "2025-01-01_pack.json").write_bytes(pack)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "day"],
                   cwd=root, check=True)  # fmt: skip
    return Receipt(hashlib.sha256(pack).hexdigest(), hashlib.sha256(text.encode()).hexdigest())


def _closes_file(path):
    rows = "".join(f"{d},regular,{n!r},{v!r},f,{'0' * 64}\n" for d, (n, v) in sorted(closes(AS_OF).rows.items()))
    path.write_text("date,session,underlying,vix,index_file,index_sha256\n" + rows, encoding="utf-8")


def test_the_composition_root_scores_live_q5_against_the_pack(tmp_path, monkeypatch):
    receipt = _repository(tmp_path)
    _closes_file(tmp_path / "closes.csv")
    frozen = SimpleNamespace(protocol_commit="0" * 40)
    monkeypatch.setattr(wiring, "require_frozen_before", lambda *a, **k: frozen)
    monkeypatch.setattr(wiring, "require_version_frozen", lambda *a, **k: frozen)
    monkeypatch.setattr(wiring, "build_forecast_history", lambda cfg, years: _PanelHistory())
    monkeypatch.setattr(wiring, "CLOSES_FILE", tmp_path / "closes.csv")
    monkeypatch.setattr(wiring, "build_session_calendar", lambda: CALENDAR)
    document = wiring.score_forecasts({}, AS_OF, _Receipts({FIRST: receipt}), root=tmp_path)
    live = next(m for m in document["modes"] if m["mode"] == LIVE)
    q5 = next(s for s in live["scores"] if (s["forecaster"], s["question"]) == (BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV))
    assert q5["counts"]["resolved"] == 1
    assert q5["primary"]["mean_brier"] == pytest.approx((0.7 - 1) ** 2)  # yes: 4.62 < 5.0, the 15:00 pack
    assert CLOSE_PROXY not in {m["mode"] for m in document["modes"]}  # nothing pooled with history


def test_scoring_refuses_when_its_own_v3_section_does_not_hold(tmp_path, monkeypatch):
    from fno.forecast.freeze import NotFrozen

    receipt = _repository(tmp_path)
    _closes_file(tmp_path / "closes.csv")
    frozen = SimpleNamespace(protocol_commit="0" * 40)

    asked = []

    def q5_changed(root, commit, section, git=None):
        asked.append(section)
        raise NotFrozen("forecast-scores's frozen files changed: fno/forecast_scoring/q5_thresholds.py")

    monkeypatch.setattr(wiring, "require_frozen_before", lambda *a, **k: frozen)
    monkeypatch.setattr(wiring, "require_version_frozen", lambda *a, **k: frozen)
    monkeypatch.setattr(wiring, "require_section_frozen", q5_changed)
    monkeypatch.setattr(wiring, "build_forecast_history", lambda cfg, years: _PanelHistory())
    monkeypatch.setattr(wiring, "CLOSES_FILE", tmp_path / "closes.csv")
    monkeypatch.setattr(wiring, "build_session_calendar", lambda: CALENDAR)
    with pytest.raises(NotFrozen, match="q5_thresholds"):
        wiring.score_forecasts({}, AS_OF, _Receipts({FIRST: receipt}), root=tmp_path)
    assert asked == [FORECAST_SCORES]  # its own section, never the panel job's (judge 64 addendum 2)
