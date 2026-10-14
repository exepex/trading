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
