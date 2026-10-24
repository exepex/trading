"""Story BG1-w (owner 24 Oct 2026, "Waiting minutes - Option A"): an AI book run counts its working minutes (brief to
seal) against BG1's cap; the wait from the seal to the end is kept apart and never capped. Criteria 1-3, 5 and 6."""

import json
from datetime import date
from decimal import Decimal

import pytest

from fno.ai.paths import timing_path
from fno.ai.usage_record import BookUsageRecorder
from fno.budget import constants
from fno.budget.cap import CapSettings, Coverage, cap_reading
from fno.budget.constants import BUDGET_OK, BUDGET_UNKNOWN, NO_SEAL_RULE, NO_SEAL_UNKNOWN, NO_SEAL_UPPER_BOUND
from fno.budget.report import meter_lines
from fno.budget.self_timed import NEVER_SEALED, SOURCE, SPLIT_SOURCE, UPPER_BOUND_SOURCE, SelfTimedUsageReader
from fno.budget.usage_ledger import Attribution, UsageLedger
from fno.budget.usage_reader import ExportRefused
from fno.budget.wiring import build_month_meter
from tests.budget.test_meter import TODAY, config

SESSION = "session_01BOOKxyz"
RUN = {"session_id": SESSION, "model": "", "started_at": "2026-10-14T14:41:00+05:30",
       "ended_at": "2026-10-14T15:10:40+05:30", "sealed_at": "2026-10-14T14:44:30+05:30",
       "reveal_calls": 3}  # fmt: skip
WHOLE_RUN = 29.67  # 14:41:00 to 15:10:40


def reader(tmp_path, no_seal=None, **changes):
    path = tmp_path / "run.timing.json"
    path.write_text(json.dumps({k: v for k, v in (RUN | changes).items() if v != "drop"}), encoding="utf-8")
    return SelfTimedUsageReader(path, no_seal)


def usage(tmp_path, no_seal=None, **changes):
    (day,) = reader(tmp_path, no_seal, **changes).days()
    return day.minutes, day.wait_minutes, day.source


# Criterion 1: working minutes, start to seal; the wait, seal to end, apart
def test_a_sealed_run_counts_start_to_seal_and_keeps_the_wait_apart(tmp_path):
    assert usage(tmp_path) == (3.50, 26.17, SPLIT_SOURCE)


@pytest.mark.parametrize(("sealed", "split"), [("2026-10-14T14:41:00+05:30", (0.0, WHOLE_RUN)),
                                               ("2026-10-14T15:10:40+05:30", (WHOLE_RUN, 0.0)),
                                               ("2026-10-14T09:14:30Z", (3.50, 26.17))])  # fmt: skip
def test_a_seal_at_either_end_is_a_measured_zero_and_any_zone_reads_in_ist(tmp_path, sealed, split):
    assert usage(tmp_path, sealed_at=sealed)[:2] == split


@pytest.mark.parametrize(("sealed", "match"), [("2026-10-14T14:40:59+05:30", "is not between"),
                                               ("2026-10-14T15:10:41+05:30", "is not between"),
                                               ("2026-10-14T14:44:30", "no time zone"),
                                               ("soon", "not an ISO time"), (1234, "not an ISO time")])  # fmt: skip
def test_a_seal_outside_the_run_or_not_a_zoned_time_is_refused_under_either_rule(tmp_path, sealed, match):
    for rule in (NO_SEAL_UPPER_BOUND, NO_SEAL_UNKNOWN):
        with pytest.raises(ExportRefused, match=match):
            reader(tmp_path, rule, sealed_at=sealed).days()


# Criterion 2: a run that never sealed, under each rule of the switch (judge 587.1's condition)
@pytest.mark.parametrize("sealed", [None, ""])
def test_the_upper_bound_rule_counts_a_never_sealed_run_start_to_end_labelled(tmp_path, sealed):
    assert usage(tmp_path, NO_SEAL_UPPER_BOUND, sealed_at=sealed) == (WHOLE_RUN, None, UPPER_BOUND_SOURCE)


@pytest.mark.parametrize("sealed", [None, ""])
def test_the_unknown_rule_refuses_a_never_sealed_run_never_zero_never_the_whole_run(tmp_path, sealed):
    with pytest.raises(ExportRefused, match=NEVER_SEALED.split(" (")[0]):
        reader(tmp_path, NO_SEAL_UNKNOWN, sealed_at=sealed).days()


def test_the_switch_defaults_to_the_upper_bound_until_the_owner_answers(tmp_path, monkeypatch):
    assert NO_SEAL_RULE == NO_SEAL_UPPER_BOUND and usage(tmp_path, sealed_at=None)[2] == UPPER_BOUND_SOURCE
    monkeypatch.setattr(constants, "NO_SEAL_RULE", NO_SEAL_UNKNOWN)  # the one line the owner's answer may change
    with pytest.raises(ExportRefused, match="never sealed"):
        reader(tmp_path, sealed_at=None).days()
    with pytest.raises(ValueError, match="no-seal rule"):
        reader(tmp_path, "no_seal_zero")


def fired_book(root, sealed):
    """A fired book2_hybrid session on 14 Oct with its published timing file (sealed or not), as G11 writes them."""
    log = root / "research/forecasts/ai_v1/2026/2026-10-14_fired.json"
    log.parent.mkdir(parents=True)
    log.write_text(json.dumps({"book2_hybrid": {"fired": True, "session": "https://claude.ai/code/cse_01BOOKxyz"}}))
    path = root / timing_path(date(2026, 10, 14), "book2_hybrid")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(RUN | {"sealed_at": RUN["sealed_at"] if sealed else None}), encoding="utf-8")


@pytest.mark.parametrize(("rule", "captured", "level"), [(NO_SEAL_UPPER_BOUND, True, BUDGET_OK),
                                                         (NO_SEAL_UNKNOWN, False, BUDGET_UNKNOWN)])  # fmt: skip
def test_a_never_sealed_run_is_captured_or_leaves_the_month_unknown_by_the_rule(tmp_path, monkeypatch, rule, captured,
                                                                                level):  # fmt: skip
    """End to end through G11's recorder (unchanged) and BG1's meter: the upper bound keeps the level known; the unknown
    rule leaves the session not captured, so a month under the alert line reads unknown (the cost judge 587 named)."""
    monkeypatch.setattr(constants, "NO_SEAL_RULE", rule)
    fired_book(tmp_path, sealed=False)
    lines = BookUsageRecorder(tmp_path, UsageLedger(tmp_path)).record(TODAY)
    assert ("refused: working minutes unknown" in lines[0]) is not captured
    meter = build_month_meter("2026-10", TODAY, tmp_path, config(plan_minutes_per_month=1000))
    assert (len(meter.missing_captures) == 0) is captured and meter.cap.level == level


def test_a_fired_run_with_no_timing_file_is_not_captured_under_either_rule(tmp_path, monkeypatch):
    for rule in (NO_SEAL_UPPER_BOUND, NO_SEAL_UNKNOWN):
        monkeypatch.setattr(constants, "NO_SEAL_RULE", rule)
        fired_book(tmp_path / rule, sealed=True)
        timing_file = tmp_path / rule / timing_path(date(2026, 10, 14), "book2_hybrid")
        timing_file.unlink()
        assert BookUsageRecorder(tmp_path / rule, UsageLedger(tmp_path / rule)).record(TODAY) == []
        meter = build_month_meter("2026-10", TODAY, tmp_path / rule, config(plan_minutes_per_month=1000))
        assert len(meter.missing_captures) == 1 and meter.cap.level == BUDGET_UNKNOWN


# Criterion 3: a record without the key is read as before
@pytest.mark.parametrize("rule", [NO_SEAL_UPPER_BOUND, NO_SEAL_UNKNOWN])
def test_a_record_without_a_seal_key_is_start_to_end_with_no_wait(tmp_path, rule):
    assert usage(tmp_path, rule, sealed_at="drop", reveal_calls="drop") == (WHOLE_RUN, None, SOURCE)


# Criterion 5: never capped, neither in the books' minutes nor in the measured basis
def ledger_rows(tmp_path, **changes):
    run = reader(tmp_path, **changes)
    UsageLedger(tmp_path).record(run.days(), Attribution("books_and_roles", "book2_hybrid"), date(2026, 10, 15))
    return UsageLedger(tmp_path).rows()


def test_the_cap_and_the_measured_basis_count_working_minutes_only(tmp_path):
    rows = ledger_rows(tmp_path)
    assert (rows[0]["minutes"], rows[0]["wait_minutes"]) == ("3.50", "26.17")  # C8 sums `minutes` (G11's stop)
    settings = CapSettings(Decimal(50), Decimal(80), Decimal(100), None)
    reading = cap_reading(rows, settings, "2026-10", Coverage())
    assert (reading.books_and_roles_minutes, reading.basis_minutes, reading.cap_minutes) == (3.5, 3.5, 1.75)


# Criterion 6: the meter prints the wait on its own line, outside the cap
def meter_text(tmp_path, rows):
    meter = build_month_meter("2026-10", TODAY, tmp_path, config(plan_minutes_per_month=1000))
    assert meter.usage_rows == rows
    return "\n".join(meter_lines(meter))


def test_the_meter_shows_the_wait_apart_and_none_when_no_row_has_one(tmp_path):
    assert "AI books' reveal wait (not capped): none recorded" in meter_text(tmp_path, [])
    ledger_rows(tmp_path)
    rows = ledger_rows(tmp_path, session_id="session_01BOOKabc", sealed_at="2026-10-14T15:10:40+05:30")
    text = meter_text(tmp_path, rows)  # two runs: 26.17 and a measured 0.00 wait
    assert "AI books' reveal wait (not capped): 26.17 minutes over 2 run(s)" in text
    assert "books and roles 33.17 of 500.00 minutes" in text  # 3.50 + 29.67: never a wait


def test_one_run_with_a_zero_wait_counts_as_one_run(tmp_path):
    rows = ledger_rows(tmp_path, sealed_at="2026-10-14T15:10:40+05:30")
    assert "AI books' reveal wait (not capped): 0.00 minutes over 1 run(s)" in meter_text(tmp_path, rows)


def test_the_two_parts_add_up_to_the_whole_run_and_the_record_line_names_the_wait(tmp_path):
    run = reader(tmp_path, started_at="2026-10-14T14:41:00+05:30", sealed_at="2026-10-14T14:41:20+05:30",
                 ended_at="2026-10-14T14:41:40+05:30")  # fmt: skip
    (day,) = run.days()
    assert (day.minutes, day.wait_minutes) == (0.33, 0.34)  # 20 s each, 0.67 minutes in all
    lines = UsageLedger(tmp_path).record(run.days(), Attribution("books_and_roles", "book2_hybrid"), date(2026, 10, 15))
    assert "recorded 0.33 minutes (and a wait of 0.34 minutes apart, not capped), 1 turns" in lines[0]


def test_the_meter_counts_the_never_sealed_upper_bounds(tmp_path):
    rows = ledger_rows(tmp_path, sealed_at=None)
    text = meter_text(tmp_path, rows)
    assert "none recorded" in text and "1 run(s) never sealed, counted start to end (no_seal_upper_bound" in text
