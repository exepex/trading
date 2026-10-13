"""Story G4: comparisons, the report's standing (criterion 4), the confirmatory gate and the forecast sources."""

from __future__ import annotations

import gzip
import hashlib
from datetime import date, datetime

import pytest

from fno.constants import (
    BASELINE_BASE_RATE,
    BASELINE_RISK_NEUTRAL,
    BOOK1_RULES,
    FORECAST_Q1_UP_20D,
    FORECAST_Q5_RV_BELOW_IV,
)
from fno.forecast.iv30 import AtmIv30
from fno.forecast.record_files import records_csv, records_csv_v2, records_gzip
from fno.forecast.schema import ForecastRecord
from fno.forecast.schema_v2 import ForecastRecordV2
from fno.forecast_scoring.score_inputs import CLOSE_PROXY, LIVE
from fno.forecast_scoring.score_report import STANDING, ReportContext, report_document, report_json, weekly_summary
from fno.forecast_scoring.score_sources import Receipt, backfill_forecasts, live_forecasts
from fno.forecast_scoring.scores import brier
from fno.forecast_scoring.scoring import ForecastScorer
from fno.forecast_scoring.wiring import confirmatory_allowed
from fno.models import IST
from tests.forecast_scoring.scoring_fixtures import DAYS, daily_forecasts, forecast, outcomes

SCORED_DAYS = DAYS[:60]
AS_OF = date(2025, 6, 30)


def scored(items, resolver=None):
    (mode,) = ForecastScorer({CLOSE_PROXY: resolver or outcomes(AS_OF)}).score(items)
    return mode


def test_book1_against_the_base_rate_is_the_mean_daily_brier_difference_in_date_order():
    mode = scored(daily_forecasts(SCORED_DAYS, 0.6, 0.5))
    c = next(r for r in mode.secondary if (r.comparison.question, r.comparison.first, r.comparison.second)
             == (FORECAST_Q1_UP_20D, BOOK1_RULES, BASELINE_BASE_RATE))  # fmt: skip
    resolver = outcomes(AS_OF)
    by_hand = [brier(0.6, o) - brier(0.5, o) for d in SCORED_DAYS
               if (o := resolver.resolve(FORECAST_Q1_UP_20D, d).outcome) is not None]  # fmt: skip
    assert c.result.n == len(by_hand) == 60 and c.result.mean_difference == pytest.approx(sum(by_hand) / 60)
    assert c.result.tested and c.result.interval[0] <= c.result.mean_difference <= c.result.interval[1]


def test_the_primary_family_waits_for_books_2_and_3_and_its_holm_result_is_withheld():
    mode = scored(daily_forecasts(SCORED_DAYS, 0.6, 0.5))
    assert len(mode.primary) == 10 and all(not c.result.tested and c.result.p_value == 1.0 for c in mode.primary)
    document = report_document(ReportContext(AS_OF, {}, False, 0, ()), [mode])
    assert all(c["holm_significant"] is None for c in document["modes"][0]["primary"])
    assert document["confirmatory_allowed"] is False and "six months" in document["confirmatory_note"]


def test_every_report_says_forecasts_are_secondary_to_net_profit():
    document = report_document(ReportContext(AS_OF, {}, False, 0, ()), [scored(daily_forecasts(SCORED_DAYS, 0.6, 0.5))])
    assert document["standing"] == STANDING and "secondary to net profit" in STANDING
    lines = weekly_summary(document)
    assert "secondary to net profit" in lines[0] and lines[-1].startswith("Too early to tell")
    assert any("60 days, Brier difference" in line for line in lines)
    assert report_json(document) == report_json(document)  # deterministic text


def test_risk_neutral_split_and_question_5_flagged_sensitivity():
    flagged_iv30 = outcomes(AS_OF, iv30=lambda d: (True, AtmIv30(40.0, True, (date(2025, 6, 26),))))
    items = [forecast(BASELINE_RISK_NEUTRAL, d, FORECAST_Q1_UP_20D, 0.55, "flagged" if i % 2 else "interpolated")
             for i, d in enumerate(SCORED_DAYS[:10])]  # fmt: skip
    items += [forecast(BOOK1_RULES, d, FORECAST_Q5_RV_BELOW_IV, 0.7, "flagged") for d in SCORED_DAYS[:10]]
    mode = scored(items, flagged_iv30)
    rn = mode.scores[(BASELINE_RISK_NEUTRAL, FORECAST_Q1_UP_20D)].sensitivities
    assert (rn["iv30_flagged"].scored, rn["iv30_unflagged"].scored) == (5, 5)
    q5 = mode.scores[(BOOK1_RULES, FORECAST_Q5_RV_BELOW_IV)]
    assert q5.counts["void"] == 10 and q5.primary.scored == 0 and q5.sensitivities["q5_flagged_iv30"].scored == 10
    assert mode.q5_flag_rate == 1.0


def test_confirmatory_claims_only_after_six_months_of_common_start_trading():
    assert not confirmatory_allowed(date(2030, 1, 1), common_start=None)  # no common start: never
    assert not confirmatory_allowed(date(2027, 4, 13)) and confirmatory_allowed(date(2027, 4, 14))  # from 14 Oct 2026
    assert not confirmatory_allowed(date(2027, 4, 14), common_start=date(2026, 10, 15))
    assert confirmatory_allowed(date(2027, 4, 15), common_start=date(2026, 10, 15))


def record(day: date, book=BASELINE_BASE_RATE, p=0.5, label="baseline_b_base_rate/v1/close-proxy/iv30:interpolated"):
    cutoff = datetime(day.year, day.month, day.day, 15, 30, tzinfo=IST)
    return ForecastRecord(book, day, cutoff, FORECAST_Q1_UP_20D, p, label, "a" * 64)


def test_the_backfill_reader_skips_earlier_rows_without_parsing_them():
    """A 2023 row that is not even a valid record is dropped by its date text, so it is never parsed."""
    header, rest = records_csv([record(date(2024, 1, 1)), record(date(2024, 1, 2))]).split("\n", 1)
    planted = header + "\nbaseline_b_base_rate,2023-12-29,not,a,valid,row\n" + rest
    kept = backfill_forecasts(gzip.compress(planted.encode()), date(2024, 1, 1))
    assert [f.day for f in kept] == [date(2024, 1, 1), date(2024, 1, 2)]
    assert {f.iv30_status for f in kept} == {"interpolated"}
    assert backfill_forecasts(records_gzip([record(date(2024, 1, 1))]), date(2024, 1, 2)) == []


class FixedReceipts:
    def __init__(self, receipts):
        self.receipts = receipts

    def receipt(self, day):
        return self.receipts.get(day)


def write_live_day(folder, day, generated):
    rec = ForecastRecordV2(record(day, BOOK1_RULES, 0.6, "book1/v1"), LIVE, "interpolated", generated)
    text, pack = records_csv_v2([rec]), b'{"pack": 1}'
    (folder / f"{day:%Y}").mkdir(parents=True, exist_ok=True)
    (folder / f"{day:%Y}" / f"{day}_forecasts.csv").write_text(text, encoding="utf-8")
    (folder / f"{day:%Y}" / f"{day}_pack.json").write_bytes(pack)
    return Receipt(hashlib.sha256(pack).hexdigest(), hashlib.sha256(text.encode()).hexdigest())


def test_live_days_are_scored_only_when_their_files_match_the_receipt(tmp_path):
    good, bad, late = date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16)
    receipts = {good: write_live_day(tmp_path, good, datetime(2026, 10, 14, 15, 12, tzinfo=IST))}
    write_live_day(tmp_path, bad, datetime(2026, 10, 15, 15, 12, tzinfo=IST))
    receipts[bad] = Receipt("0" * 64, "0" * 64)
    receipts[late] = write_live_day(tmp_path, late, datetime(2026, 10, 16, 15, 16, tzinfo=IST))
    out = live_forecasts(tmp_path, FixedReceipts(receipts))
    assert [f.day for f in out.forecasts] == [good] and out.unverified == ["2026-10-15"] and out.late == 1
    assert live_forecasts(tmp_path, FixedReceipts({})).unverified == ["2026-10-14", "2026-10-15", "2026-10-16"]
