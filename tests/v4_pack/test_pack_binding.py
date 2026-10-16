"""Story G10 part 2, criterion 3 (judge 274): the forecaster decides whether a record names the pack. A pack reader
names exactly the released pack; every other forecaster names none."""

import pytest

from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.forecast_v4.terms import V4_LATEST_FIRE
from fno.v4_pack.guard import PACK_READERS, PackBindingRefused, check_pack_binding

DAY, RELEASED, OTHER = "2026-10-22", "a" * 64, "b" * 64


def test_the_pack_readers_are_the_ai_books():
    assert {BOOK2_HYBRID, BOOK3_AI} == PACK_READERS


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
