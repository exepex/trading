"""Protocol v3 (ChatGPT review 30 item 7, response 69): a live question-5 forecast is resolved against the 15:00 IV30
locked in its own hashed pack, never against the panel's later close-proxy IV30; history keeps the close-proxy IV30.
The planted disagreement: the fixture's next-20-day RV is 4.62 points, the 15:00 pack says 5.0 (outcome yes) and the
15:30 panel says 4.0 (outcome no)."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime

import pytest

from fno.constants import BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV
from fno.forecast.iv30 import AtmIv30
from fno.forecast.record_files import records_csv_v2
from fno.forecast.schema import ForecastRecord
from fno.forecast.schema_v2 import ForecastRecordV2
from fno.forecast_scoring.resolution import RESOLVED, VOID, OfficialOutcomes
from fno.forecast_scoring.score_inputs import CLOSE_PROXY, LIVE
from fno.forecast_scoring.score_sources import Receipt, live_forecasts
from fno.forecast_scoring.scoring import ForecastScorer
from fno.models import IST
from tests.forecast_scoring.scoring_fixtures import CALENDAR, FIRST, closes, forecast, horizon_day

TARGET = horizon_day(FIRST, 20)
PANEL_1530 = AtmIv30(4.0, False, (date(2025, 1, 30),))  # the panel's close-proxy IV30 of the day
PACK_1500 = {"points": 5.0, "status": "interpolated", "expiries": ["2025-01-30", "2025-02-27"]}


def _resolver(live_iv30) -> OfficialOutcomes:
    return OfficialOutcomes(closes(TARGET), CALENDAR, TARGET, lambda d: (True, PANEL_1530), horizon_day, live_iv30)


def test_the_resolver_uses_the_pack_for_live_and_the_panel_for_history():
    resolver = _resolver(lambda d: AtmIv30(5.0, False, (date(2025, 1, 30),)))
    assert resolver.targets.next_rv(FIRST) == pytest.approx(4.6196, abs=1e-4)
    assert resolver.resolve(FORECAST_Q5_RV_BELOW_IV, FIRST, LIVE) == (RESOLVED, True, None)
    assert resolver.resolve(FORECAST_Q5_RV_BELOW_IV, FIRST, CLOSE_PROXY) == (RESOLVED, False, None)


def test_a_flagged_or_missing_pack_iv30_makes_live_q5_void_whatever_the_panel_says():
    flagged = _resolver(lambda d: AtmIv30(5.0, True, (date(2025, 1, 30),)))
    assert flagged.resolve(FORECAST_Q5_RV_BELOW_IV, FIRST, LIVE).status == VOID
    assert _resolver(lambda d: None).resolve(FORECAST_Q5_RV_BELOW_IV, FIRST, LIVE).status == VOID


class _Receipts:
    def __init__(self, receipts):
        self.receipts = receipts

    def receipt(self, day):
        return self.receipts.get(day)


def _live_day(folder, pack_iv30) -> Receipt:
    cutoff = datetime(2025, 1, 1, 15, 0, tzinfo=IST)
    base = ForecastRecord(BOOK1_RULES, FIRST, cutoff, FORECAST_Q5_RV_BELOW_IV, 0.7, "book1/v1", "a" * 64)
    text = records_csv_v2([ForecastRecordV2(base, LIVE, "interpolated", datetime(2025, 1, 1, 15, 5, tzinfo=IST))])
    pack = json.dumps({"iv30": pack_iv30}, sort_keys=True).encode()
    (folder / "2025").mkdir(parents=True, exist_ok=True)
    (folder / "2025" / "2025-01-01_forecasts.csv").write_text(text, encoding="utf-8")
    (folder / "2025" / "2025-01-01_pack.json").write_bytes(pack)
    return Receipt(hashlib.sha256(pack).hexdigest(), hashlib.sha256(text.encode()).hexdigest())


def test_the_scorer_reads_the_threshold_from_the_verified_pack(tmp_path):
    live = live_forecasts(tmp_path, _Receipts({FIRST: _live_day(tmp_path, PACK_1500)}))
    assert live.iv30[FIRST] == AtmIv30(5.0, False, (date(2025, 1, 30), date(2025, 2, 27)))
    resolver = _resolver(lambda day: live.iv30.get(day))
    history = forecast(BOOK1_RULES, FIRST, FORECAST_Q5_RV_BELOW_IV, 0.7)
    by_mode = {m.mode: m for m in ForecastScorer(resolver).score(live.forecasts + [history])}
    live_brier = by_mode[LIVE].scores[(BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV)].primary.mean_brier
    history_brier = by_mode[CLOSE_PROXY].scores[(BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV)].primary.mean_brier
    assert live_brier == pytest.approx((0.7 - 1) ** 2)  # outcome yes: 4.62 < 5.0 (15:00 pack)
    assert history_brier == pytest.approx(0.7**2)  # outcome no: 4.62 > 4.0 (close proxy)
