"""Story G1: the forecast record schema, and the frozen comparison family (criterion 4)."""

from datetime import UTC, date, datetime

import pytest

from fno.config import ROOT
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, FORECAST_Q1_UP_20D, FORECAST_Q5_RV_BELOW_IV
from fno.forecast.comparisons import BOOTSTRAP_SEED, RESAMPLES, comparison_family
from fno.forecast.schema import RECORD_COLUMNS, ForecastRecord, ForecastRecordError
from fno.models import IST

DAY = date(2026, 10, 13)
CUTOFF = datetime(2026, 10, 13, 15, 0, tzinfo=IST)
SHA = "a" * 64


def _record(**changes) -> ForecastRecord:
    fields = dict(book=BOOK1_RULES, date=DAY, cutoff=CUTOFF, question=FORECAST_Q1_UP_20D, probability=0.55,
                  method_or_version="book1/v1", pack_sha256=SHA)  # fmt: skip
    return ForecastRecord(**(fields | changes))


def test_a_record_round_trips_through_its_row():
    record = _record()
    assert tuple(record.row()) == RECORD_COLUMNS
    assert ForecastRecord.from_row(record.row()) == record


def test_no_forecast_is_recorded_as_empty_never_imputed():
    record = _record(probability=None)
    assert record.row()["probability"] == ""
    assert ForecastRecord.from_row(record.row()).probability is None


@pytest.mark.parametrize(
    "changes",
    [
        {"book": "book4"},
        {"question": "q6"},
        {"probability": 1.01},
        {"probability": -0.01},
        {"probability": float("nan")},
        {"probability": True},
        {"cutoff": datetime(2026, 10, 13, 15, 0)},  # no time zone
        {"cutoff": datetime(2026, 10, 12, 15, 0, tzinfo=IST)},  # another day
        {"cutoff": datetime(2026, 10, 13, 20, 0, tzinfo=UTC)},  # 14 Oct in IST
        {"method_or_version": ""},
        {"method_or_version": "a,b"},
        {"pack_sha256": "A" * 64},
        {"pack_sha256": "a" * 63},
    ],
)
def test_a_record_breaking_the_schema_is_refused(changes):
    with pytest.raises(ForecastRecordError):
        _record(**changes)


def test_a_cutoff_in_another_zone_on_the_same_ist_day_is_accepted():
    assert _record(cutoff=CUTOFF.astimezone(UTC)).cutoff == CUTOFF
    assert _record(probability=0.0).probability == 0.0 and _record(probability=1.0).probability == 1.0


def test_unreadable_rows_are_refused():
    row = _record().row() | {"probability": "high"}
    with pytest.raises(ForecastRecordError):
        ForecastRecord.from_row(row)
    with pytest.raises(ForecastRecordError):
        ForecastRecord.from_row({k: v for k, v in _record().row().items() if k != "pack_sha256"})


def test_the_family_is_45_comparisons_in_the_protocols_order():
    family = comparison_family()
    assert len(family) == 45 and [c.k for c in family] == list(range(1, 46))
    first_nine = [(c.first, c.second) for c in family[:9]]
    assert first_nine == [
        (BOOK1_RULES, BOOK2_HYBRID), (BOOK1_RULES, BOOK3_AI), (BOOK2_HYBRID, BOOK3_AI),
        (BOOK1_RULES, "baseline_a_risk_neutral"), (BOOK2_HYBRID, "baseline_a_risk_neutral"),
        (BOOK3_AI, "baseline_a_risk_neutral"), (BOOK1_RULES, "baseline_b_base_rate"),
        (BOOK2_HYBRID, "baseline_b_base_rate"), (BOOK3_AI, "baseline_b_base_rate"),
    ]  # fmt: skip
    q5 = [c for c in family if c.question == FORECAST_Q5_RV_BELOW_IV]
    assert {c.second for c in q5} == {BOOK2_HYBRID, BOOK3_AI, "baseline_b_base_rate", "baseline_c_model"}
    assert len({(c.question, c.first, c.second) for c in family}) == 45


def test_the_protocol_names_the_exact_multiplicity_procedure():
    text = (ROOT / "research" / "forecasts" / "PROTOCOL.md").read_text(encoding="utf-8")
    for phrase in ("45 comparisons", "Holm's step-down", "5%", "block length L = 20", f"B = {RESAMPLES:,}",
                   f"SeedSequence([{BOOTSTRAP_SEED},", "Only Brier is tested"):  # fmt: skip
        assert phrase in text, phrase
