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


def test_the_freeze_plan_rules_are_written_as_the_code_runs_them():
    """Response 287's remaining text (piece 1b): misses from a registered slot's `effective_start` after the freeze
    (`scoring._miss_start`, `SlotFile`), item E's share cut (`confirmatory.crash_dominated`) and intraday HAR over
    usable sessions only."""
    flat = " ".join(TEXT.split())
    assert "counted for each **registered** slot from its `effective_start`" in flat
    assert "a session after the freeze and no later than the slot's first eligible session" in flat
    assert 'An **unregistered** slot is "not started": p = 1, never judged.' in flat
    assert "is not judgeable either, for every member** (`confirmatory.crash_dominated`" in flat
    assert "**Decided: option 2, the share cut**" in flat
    assert "a void session is skipped, never a reason for the day's value to be missing" in flat


def test_the_share_cut_numbers_in_the_text_follow_the_code():
    """Judge 430 note 1: the text's "10%" and "n = 130" are the code's `CRASH_SHARE` and the first n whose cut admits
    13 2% days, so a change to either is caught."""
    from fno.forecast_v4.confirmatory import CRASH_SHARE, crash_dominated

    flat = " ".join(TEXT.split())
    assert f"more than {round(CRASH_SHARE * 100)}% of its scored outcomes is not judgeable" in flat
    first_n_for_13 = next(n for n in range(13, 1000) if not crash_dominated(13, n))
    assert crash_dominated(13, 125) and not crash_dominated(12, 125)
    assert (
        f"at n = 125 a judgeable window holds at most 12 such days, so the 13+ band starts at n = {first_n_for_13}"
        in flat
    )


def test_section_11_d_states_the_measured_noise_not_the_assumed_one():
    """Response 299 item 9 (owner, 21 Oct 2026): judge 128's measured r replaces "only V6b can be claimed, slowly"."""
    flat = " ".join(TEXT.split())
    assert "only V6b can be claimed, slowly, and see E" not in flat
    assert "V6b needs about 14-22 years even if its full back-filled skill is real" in flat
    assert "no v4 member is provable in useful time" in flat
    assert "V2's 8-22 years above are at the assumed r = 3-5, so with real noise it needs longer" in flat  # 436
    assert "The table's result is advice to the owner, never an automatic step" in flat


def test_the_day_clock_s_release_and_label_rules_match_the_code():
    """G10 completion, criterion 5: the release-by time and the label words the release run and G8 use."""
    from fno.forecast_scoring.v4.days import PENDING
    from fno.v4_pack.release_run import RELEASED_LATE, V4_RELEASE_BY

    text = TEXT.replace("\n  ", " ")
    assert f"by {V4_RELEASE_BY:%H:%M}:00" in text and "after 14:45:00 makes the day `system_late`" in text
    assert RELEASED_LATE.split(":")[0] in text and f"is {PENDING}, never scored" in text
    assert "or no release record at all" in text and "from the pack's live date (`daily.live_from.v4_pack`)" in text
    before = "a day before that date has no label (no pack could exist, so it is no system failure; its rows stay in)"
    assert before in text
