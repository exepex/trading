"""Story G6: the protocol text and `fno/forecast_v4/terms.py` state the same registered numbers and names, so the
document the judge and ChatGPT review is the rule the code runs."""

from __future__ import annotations

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


def test_the_days_clock_in_the_text_matches_terms():
    """Story G10 criterion 1: section 1.6's times and X are the code's, so the text and `terms.py` cannot drift."""
    section = TEXT[TEXT.index("### 1.6 The day's clock") : TEXT.index("## 2. The session set")]
    rows = {line.split("|")[1].strip() for line in section.splitlines() if line.startswith("| ")}
    for clock in (terms.V4_CAPTURE_START, terms.V4_PACK_WINDOW_END, terms.V4_DEADLINE):
        assert f"{clock:%H:%M}:00" in rows  # the clock table's own row, not a mention elsewhere
    assert f"{terms.V4_COMMON_SNAPSHOT:%H:%M}" in rows
    assert f"**X = {terms.MOVED_AFTER_CUTOFF_X!r}**" in section
    assert f"**{terms.MOVED_AFTER_CUTOFF_SAMPLE:,}**" in section and terms.MOVED_AFTER_CUTOFF_SOURCE in section
    assert "the cutoff is **every field observed by 14:40:00 IST" in " ".join(TEXT.split())


def test_the_day_labels_in_the_text_are_the_codes_and_a2_is_gone():
    """The orchestrator's ruling of 16 Oct: A and system_late only; the draft's A2 fallback can never make a pack."""
    from fno.constants import V4_DAY_A, V4_DAY_SYSTEM_LATE
    from fno.forecast_scoring.v4.days import LABELS
    from fno.v4_pack.codec import PACK_LABELS

    assert LABELS == (V4_DAY_A, V4_DAY_SYSTEM_LATE) and PACK_LABELS == (V4_DAY_A,)
    assert f"`{V4_DAY_A}`, the 14:30 capture" in " ".join(TEXT.split()) and f"`{V4_DAY_SYSTEM_LATE}`" in TEXT
    assert "`A2`" not in TEXT.replace("replacing the draft's `A2`", "")
