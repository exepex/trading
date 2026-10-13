"""Story G1: the forecast record schema, and the frozen comparison family (criterion 4)."""

from datetime import UTC, date, datetime

import pytest

from fno.config import ROOT
from fno.constants import (
    BOOK1_RULES,
    BOOK2_HYBRID,
    BOOK3_AI,
    FORECAST_Q1_UP_20D,
    FORECAST_Q5_RV_BELOW_IV,
    FORECAST_QUESTIONS,
)
from fno.forecast.comparisons import BOOTSTRAP_SEED, RESAMPLES, primary_family, secondary_comparisons
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


def test_the_primary_family_is_10_tests_book2_and_book3_against_book1():
    family = primary_family()
    assert len(family) == 10 and [c.k for c in family] == list(range(1, 11)) and all(c.primary for c in family)
    assert [(c.first, c.second) for c in family[:2]] == [(BOOK2_HYBRID, BOOK1_RULES), (BOOK3_AI, BOOK1_RULES)]
    assert [c.question for c in family[::2]] == list(FORECAST_QUESTIONS)


def test_secondary_comparisons_are_descriptive_and_never_in_the_primary_family():
    secondary = secondary_comparisons()
    assert len(secondary) == 5 * 7 and not any(c.primary for c in secondary)
    assert [c.k for c in secondary] == list(range(11, 46))
    q5 = [c for c in secondary if c.question == FORECAST_Q5_RV_BELOW_IV]
    assert (BOOK2_HYBRID, BOOK3_AI) in {(c.first, c.second) for c in q5}
    assert {c.second for c in q5} - {BOOK3_AI} == {"baseline_b_base_rate", "baseline_c_model"}
    primary = {(c.question, c.first, c.second) for c in primary_family()}
    assert not primary & {(c.question, c.first, c.second) for c in secondary}


def test_the_protocol_names_the_exact_multiplicity_procedure():
    text = (ROOT / "research" / "forecasts" / "PROTOCOL.md").read_text(encoding="utf-8")
    phrases = (
        "10 tests", "Holm's step-down", "5%", "block length L = 20", f"B = {RESAMPLES:,}",
        f"SeedSequence([{BOOTSTRAP_SEED},", "never called confirmatory", "first review, not a deadline",
    )  # fmt: skip
    for phrase in phrases:
        assert phrase in text, phrase
