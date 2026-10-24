"""Story G10 part 2, criterion 3 (judge 274): the forecaster decides whether a record names the pack. A pack reader
names exactly the released pack; every other forecaster names none."""

import pytest

from fno.constants import (
    BOOK2_HYBRID,
    BOOK3_AI,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_OPTION_IMPLIED_PROB,
    V4_BASELINE_PREMIUM_ADJUSTED,
    V4_BASELINE_RAW_IMPLIED,
)
from fno.forecast_v4.terms import V4_LATEST_FIRE
from fno.forecast_v4_rules.constants import V4_RULE_V4_EWMA_CHI2, V4_RULE_V5_EWMA_LOGNORMAL
from fno.v4_pack.guard import PACK_READERS, PackBindingRefused, check_pack_binding

DAY, RELEASED, OTHER = "2026-10-22", "a" * 64, "b" * 64


def test_the_pack_readers_are_the_ai_books_and_g7b_completions_pack_rows():
    """G7b completion: the pack-derived baselines and the V4 and V5 rules read the pack; base rates do not."""
    g7b = {V4_BASELINE_RAW_IMPLIED, V4_BASELINE_PREMIUM_ADJUSTED, V4_BASELINE_OPTION_IMPLIED_PROB, V4_RULE_V4_EWMA_CHI2,
           V4_RULE_V5_EWMA_LOGNORMAL}  # fmt: skip
    assert {BOOK2_HYBRID, BOOK3_AI} | g7b == PACK_READERS and V4_BASELINE_BASE_RATE not in PACK_READERS


@pytest.mark.parametrize("book", sorted(PACK_READERS))
def test_a_pack_reader_names_exactly_the_released_pack(book):
    check_pack_binding(book, DAY, RELEASED, RELEASED)
    for named in ("", OTHER):
        with pytest.raises(PackBindingRefused):
            check_pack_binding(book, DAY, named, RELEASED)


@pytest.mark.parametrize("book", sorted(PACK_READERS))
def test_a_pack_reader_has_no_record_on_a_day_without_a_pack(book):
    for named in ("", OTHER):
        with pytest.raises(PackBindingRefused, match="system_late"):
            check_pack_binding(book, DAY, named, "")


@pytest.mark.parametrize("forecaster", ["v6_ewma_t4", "base_rate", "weather_vix_v1", "weather_checklist_v0"])
def test_a_forecaster_that_commits_before_the_pack_names_none(forecaster):
    check_pack_binding(forecaster, DAY, "", RELEASED)
    check_pack_binding(forecaster, DAY, "", "")
    with pytest.raises(PackBindingRefused):
        check_pack_binding(forecaster, DAY, RELEASED, RELEASED)


def test_the_ai_books_latest_start_is_1455():
    assert V4_LATEST_FIRE.isoformat() == "14:55:00"
