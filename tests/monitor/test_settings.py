"""LM1's thresholds come from `config.yaml` `monitor` only, checked at start; the execution snapshot is the desk
timetable's, never typed."""

from __future__ import annotations

from datetime import time

import pytest

from fno.config import load_app_config
from fno.intraday.status import GOOD, INCOMPLETE
from fno.monitor.settings import MonitorSettings, MonitorSettingsError
from fno.monitor.wiring import build_position_monitor, monitor_settings

from .fixtures import SECTION, settings


def test_the_repository_config_builds_the_monitor_with_the_timetable_snapshot():
    cfg = load_app_config()
    built = build_position_monitor(cfg)
    assert built.settings.execution_snapshot == time.fromisoformat(cfg["desk"]["timetable"]["execution_snapshot"])
    assert monitor_settings(cfg).version


@pytest.mark.parametrize(("key", "value"), [
    ("loss_used_warning", 0.9), ("loss_used_danger", 1.2), ("short_strike_near_pct", 0), ("big_move_pct", "1.5"),
    ("big_move_step_pct", -1), ("stale_after_minutes", 0), ("check_incomplete_marks", "yes"),
    ("expiry_warn_sessions", -1), ("danger_summary_after", 2.5), ("summary_every_minutes", True), ("version", ""),
])  # fmt: skip
def test_a_bad_value_stops_at_start(key, value):
    with pytest.raises(MonitorSettingsError, match="monitor setting"):
        settings(**{key: value})


def test_a_missing_or_unknown_key_stops_at_start():
    without = {k: v for k, v in SECTION.items() if k != "big_move_pct"}
    with pytest.raises(MonitorSettingsError, match="missing"):
        MonitorSettings.from_config(without, time(15, 15))
    with pytest.raises(MonitorSettingsError, match="unknown"):
        settings(vix_jump_pct=10)


def test_incomplete_marks_are_usable_only_when_set():
    assert settings().usable_statuses == (GOOD, INCOMPLETE)
    assert settings(check_incomplete_marks=False).usable_statuses == (GOOD,)
