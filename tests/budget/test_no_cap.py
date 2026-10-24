"""Story BG1-u (owner, 24 Oct 2026: "No monthly budget cap for AI. Keep it unlimited."): under `budget.cap: none` BG1
records and reports minutes, and nothing alerts or stops; `share` keeps the 15 Oct cap for a later decision."""

from datetime import datetime
from decimal import Decimal

import pytest

from fno.budget.cap import NO_CAP, CapSettings, Coverage, cap_reading
from fno.budget.constants import BUDGET_ALERT, BUDGET_NO_CAP, BUDGET_STOP
from fno.budget.report import meter_lines
from fno.budget.signal import NO_CAP_ALERT, send_alert, signal_data, write_signal
from fno.budget.wiring import build_month_meter
from fno.config import ROOT, load_app_config
from fno.learning.report import PostMortemRecords, Report
from fno.learning.writer import PostMortemRoutine, SignalFile
from fno.models import IST
from tests.budget.test_meter import TODAY
from tests.learning.test_report_writer_publish import LINES, SATURDAY, Trigger

SHARE = {"books_and_roles_share_pct": 50, "alert_pct": 80, "stop_pct": 100}
GAPS = Coverage(book_missing=3, development_gap="no roster", routine_gap="0 of 23 runs")


def settings(cap):
    return CapSettings.from_config(SHARE | {"cap": cap})


def rows(minutes):
    return [{"purpose": "books_and_roles", "minutes": str(minutes)}, {"purpose": "development", "minutes": "0"}]


# Criterion 1: the switch
def test_the_configured_switch_is_none_and_share_keeps_the_cap():
    assert (
        load_app_config()["budget"]["cap"] == "none" and not CapSettings.from_config(load_app_config()["budget"]).capped
    )
    assert settings("share").capped


@pytest.mark.parametrize("cap", ["unlimited", "", None, "None", "missing"])
def test_a_missing_or_unknown_cap_value_is_refused_as_a_value_error(cap):
    budget = SHARE if cap == "missing" else SHARE | {"cap": cap}
    with pytest.raises(ValueError, match="budget.cap must be one of none, share"):
        CapSettings.from_config(budget)


def config_with(**budget):
    cfg = load_app_config()
    cfg["budget"] = {k: v for k, v in (cfg["budget"] | budget).items() if v != "drop"}
    return cfg


@pytest.mark.parametrize("cap", ["drop", "unlimited"])
def test_both_callers_meet_a_value_error_never_another_crash(cap):
    """G11's v4 fire (`MeterBudgetStop`, fails open only on ValueError, OSError or KeyError) and role_value's weekly
    cost (`allocation_of`, its command refuses a ValueError in one line) both read `build_month_meter`."""
    with pytest.raises(ValueError, match="budget.cap"):
        build_month_meter("2026-10", TODAY, ROOT, config_with(cap=cap))
    meter = build_month_meter("2026-10", TODAY, ROOT, config_with(cap="none"))
    assert meter.allocation.allocated_rs  # role_value's weekly cost reads this under `none` without a crash


# Criterion 2: the level under `none`
@pytest.mark.parametrize(("minutes", "coverage"), [(34.46, Coverage()), (100_000, GAPS), (0, GAPS)])
def test_under_none_the_level_is_no_cap_whatever_the_minutes_or_the_gaps(minutes, coverage):
    reading = cap_reading(rows(minutes), settings("none"), "2026-10", coverage)
    assert (reading.level, reading.cap_minutes, reading.pct_of_cap, reading.note) == (BUDGET_NO_CAP, None, None, NO_CAP)
    assert (reading.books_and_roles_minutes, reading.basis_minutes) == (minutes, minutes)


def test_under_none_an_empty_month_is_no_cap_never_unknown():
    assert cap_reading([], settings("none"), "2026-10", GAPS).level == BUDGET_NO_CAP


# Criteria 3 and 5: nothing alerts or stops, at any minutes
class Sender:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


@pytest.mark.parametrize("minutes", [0, 34.46, 100_000])
def test_under_none_the_signal_never_stops_or_alerts(minutes):
    reading = cap_reading(rows(minutes), settings("none"), "2026-10", GAPS)
    data = signal_data("2026-10", reading, 3, datetime(2026, 10, 24, 20, 0, tzinfo=IST))
    sender = Sender()
    assert reading.level != BUDGET_STOP and data["stop_ai_roles"] is False and data["alert_text"] == ""
    assert send_alert(sender, data) == NO_CAP_ALERT and sender.sent == []


def test_the_post_mortem_writer_fires_on_a_no_cap_signal(tmp_path):
    reading = cap_reading(rows(100_000), settings("none"), "2026-10", GAPS)
    write_signal(tmp_path, signal_data("2026-10", reading, 0, datetime(2026, 10, 24, 20, 0, tzinfo=IST)))
    records = PostMortemRecords(tmp_path)
    records.write(SATURDAY, Report(LINES, {}))
    trigger = Trigger()
    routine = PostMortemRoutine(trigger, records, SignalFile(tmp_path), lambda: datetime(2026, 10, 17, 10, 42,
                                                                                         tzinfo=IST))  # fmt: skip
    assert routine.fire(SATURDAY).endswith("routine fired") and trigger.fired


# Criterion 4: the meter
def test_the_meter_prints_minutes_and_one_no_cap_line(tmp_path):
    text = "\n".join(meter_lines(build_month_meter("2026-10", TODAY, ROOT, config_with(cap="none"))))
    cap_part = text[text.index("  AI cap:") :]
    assert cap_part.startswith("  AI cap: none (owner, 24 Oct 2026: unlimited); books and roles ")
    assert "%" not in cap_part and "level" not in cap_part and "measured books_and_roles:" in text
    assert "AI books' reveal wait (not capped)" in text
    empty = "\n".join(
        meter_lines(build_month_meter("2026-10", TODAY, tmp_path, config_with(cap="none", plan_cost=None)))
    )
    assert "AI cap: none (owner, 24 Oct 2026: unlimited); books and roles 0.00 minutes this month" in empty


# Criterion 6: nothing deleted, `share` still alerts and stops
@pytest.mark.parametrize(("minutes", "level"), [(40, BUDGET_ALERT), (50, BUDGET_STOP)])
def test_share_still_reaches_alert_and_stop(minutes, level):
    usage = rows(minutes) + [{"purpose": "development", "minutes": str(100 - minutes)}]
    reading = cap_reading(usage, settings("share"), "2026-10", Coverage())
    assert reading.level == level and reading.cap_minutes == 50.0
    assert signal_data("2026-10", reading, 0, datetime(2026, 10, 24, tzinfo=IST))["stop_ai_roles"] is (
        level == BUDGET_STOP
    )


def test_the_share_settings_stay_in_config_for_a_later_decision():
    budget = load_app_config()["budget"]
    assert [budget[k] for k in ("books_and_roles_share_pct", "alert_pct", "stop_pct")] == [50, 80, 100]
    assert settings("share").share_pct == Decimal(50)
