"""Story G6: the protocol text and `fno/forecast_v4/terms.py` state the same registered numbers and names, so the
document the judge and ChatGPT review is the rule the code runs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fno.constants import V4_QUESTIONS, V4_SLOTS
from fno.forecast_v4 import terms

TEXT = (Path(__file__).resolve().parents[2] / "research/forecasts/PROTOCOL_v4.md").read_text(encoding="utf-8")


def test_the_protocol_is_a_draft_until_its_freeze_record_exists():
    assert "**Status: DRAFT, not frozen.**" in TEXT
    assert not (Path(__file__).resolve().parents[2] / "research/forecasts/FREEZE_v4.md").exists()


@pytest.mark.parametrize("name", [*V4_QUESTIONS, *V4_SLOTS])
def test_every_question_and_slot_name_is_in_the_text(name):
    assert f"`{name}`" in TEXT


def test_registered_numbers_match_the_code():
    assert terms.RESAMPLES == 10_000 and "B = 10,000" in TEXT
    assert str(terms.BOOTSTRAP_SEED) in TEXT
    assert (terms.QLIKE_MIN_EFFECT, terms.BRIER_MIN_EFFECT) == (0.03, 0.02)
    assert "**at least 0.03**" in TEXT and "**at least 0.02**" in TEXT
    assert terms.LOOK_ERROR_RATE == {terms.LOOK_STOP_REVIEW: 0.02, terms.LOOK_SETTLE_DATE: 0.03}
    assert "family-wise **0.02**" in TEXT and "at\n   **0.03**" in TEXT
    assert terms.FAMILY_SIZE == 15 and "The confirmatory family (15 members, fixed now)" in TEXT
    assert terms.POWER_REPORT_AT == 60 and terms.USEFUL_TIME_YEARS == 2 and terms.BIG_MOVE == 0.02
    assert (terms.MISS_CAP, terms.BIG_DAY_MISS_CAP) == (0.10, 0.10)
    assert "missed more than **10%**" in TEXT and "more than **10%** of the baseline-observable 2% days" in TEXT
    assert "with **fewer than 10**" in TEXT


def test_block_lengths_in_the_table_match_the_code():
    rows = {line.split("|")[2].strip(" `"): line.split("|")[5].strip() for line in TEXT.splitlines() if "| `v" in line}
    assert {q: int(L) for q, L in rows.items()} == terms.BLOCK_LENGTH


def test_the_disclosed_base_rates_are_in_the_text():
    for figure in (
        "**2,409 regular close-to-close log returns**",
        "**100 of 2,409 = 4.15%**",
        "**331 of 2,405 = 13.76%**",
    ):
        assert figure in TEXT


def test_the_calibration_part_is_referenced_draft_and_frozen_with_the_protocol():
    calibration = (Path(__file__).resolve().parents[2] / "research/forecasts/PROTOCOL_v4_calibration.md").read_text(
        encoding="utf-8"
    )
    assert "**DRAFT, not\nfrozen**" in calibration or "DRAFT, not frozen" in calibration.replace("\n", " ")
    assert "`PROTOCOL_v4_calibration.md`" in TEXT and "PROTOCOL_v4_calibration.md` (part of this protocol" in TEXT
    assert "V7 is descriptive-only" in TEXT and "## 3. V7's own VIX null" in calibration


def test_revision_7_states_the_regime_caveat_for_every_member_and_test_a():
    calibration = (Path(__file__).resolve().parents[2] / "research/forecasts/PROTOCOL_v4_calibration.md").read_text(
        encoding="utf-8"
    )
    assert "**every member's claims and futility, and so the whole of Test A**" in TEXT
    assert (
        "for every member's claims AND futility" in calibration
        and "## 4. Every member inside one regime" in calibration
    )
    assert "`regime.py`" in TEXT and "`regime.window_regime`" in TEXT
    for option in ("1. **Accept**", "2. **Exclude crash windows**", "3. **V6b descriptive**"):
        assert option in TEXT
    assert "**Every member also needs at least 5 2% days in the scored window**" in TEXT
    assert "the 5-day gate covers every member" in calibration


def test_the_days_clock_and_x_in_the_text_match_the_code():
    """Story G10: section 1.6's times, X and its provenance are the numbers `terms.py` runs."""
    rows = (
        f"| {terms.V4_CAPTURE_START:%H:%M:%S} | The pack's capture starts",
        f"| {terms.V4_PACK_WINDOW_END:%H:%M:%S} | **The pack's cutoff:**",
        f"| {terms.V4_DEADLINE:%H:%M:%S} | **One deadline:**",
        f"| {terms.V4_COMMON_SNAPSHOT:%H:%M} | **Common snapshot**",
    )  # each row of 1.6's table pinned to its own constant (judge 411: a moved deadline must fail)
    assert all(row in TEXT for row in rows), [row for row in rows if row not in TEXT]
    assert "observed by 14:40:00 IST on `d`,\ncaptured from 14:30:00" in TEXT and "after 15:10:00" in TEXT
    assert f"**X = {terms.MOVED_AFTER_CUTOFF_X!r}**" in TEXT
    frozen = json.loads(
        (Path(__file__).resolve().parents[2] / "research/forecasts/v4_moved_after_cutoff.json").read_text()
    )
    assert (frozen["quantile"], frozen["x"]) == (0.95, terms.MOVED_AFTER_CUTOFF_X)  # judge 411 note 1
    assert "nearest rank" in frozen["convention"] and "the nearest-rank 95th percentile (the `ceil(0.95 n)`-th" in TEXT
    assert f"**{terms.MOVED_AFTER_CUTOFF_SAMPLE:,}**" in TEXT and terms.MOVED_AFTER_CUTOFF_SOURCE in TEXT
    assert "the cutoff is 15:00:00 IST on `d`" not in TEXT and "15:00 pack" not in TEXT


def test_the_day_labels_in_the_text_are_a_and_system_late_only():
    assert "`A`, every required field observed by 14:40:00" in TEXT and "`system_late`, no complete pack" in TEXT
    assert "was dropped on 16 Oct" in TEXT
