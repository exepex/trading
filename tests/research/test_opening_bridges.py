"""The opening-loss summary of the 12 Oct backtest evidence (ChatGPT review 4, section 2)."""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "research" / "2026-10-12-backtest" / "replay.py"
spec = importlib.util.spec_from_file_location("replay_2026_10_12", SCRIPT)
replay = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = replay  # dataclasses look their module up here
spec.loader.exec_module(replay)

COMPLETE = {
    "incomplete": 0,
    "before_the_previous_close": -10.0,
    "overnight_option_value_change": -50.0,
    "open_to_exit": -30.0,
    "charges": -5.0,
    "net": -95.0,
}
INCOMPLETE = {"incomplete": 1, "reason": "no 09:15 candle in the exit session", "net": -70.0}


@pytest.mark.parametrize("order", [("E001", "E002"), ("E002", "E001")])
def test_incomplete_bridges_are_listed_never_counted_as_zero(order):
    by_id = {"E001": COMPLETE, "E002": INCOMPLETE}
    summary = replay.summarise_bridges([by_id[i] for i in order], list(order))
    assert summary["matched"] == 2 and summary["complete"] == 1 and summary["incomplete"] == 1
    assert summary["incomplete_entries"] == [{"id": "E002", "reason": INCOMPLETE["reason"], "net": -70.0}]
    assert summary["parts_over_complete_bridges_only"]["overnight_option_value_change"] == -50.0
    assert summary["net_of_complete_bridges"] == -95.0 and summary["net_of_all_matched"] == -165.0


def test_an_empty_group_is_reported_as_empty():
    summary = replay.summarise_bridges([], [])
    assert summary["matched"] == 0 and summary["parts_over_complete_bridges_only"]["charges"] == 0
