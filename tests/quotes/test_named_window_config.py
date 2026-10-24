"""Story A4e: the named window's settings, refusals before any request, the command and its composition root."""

from argparse import Namespace
from datetime import time

import pytest
import yaml

from fno.config import ConfigError, load_app_config
from fno.quotes.capture_log import TimedLevels, TimedProvider
from fno.quotes.cli import _record_window
from fno.quotes.recorder import DATASET
from fno.quotes.window import named_window
from fno.quotes.window_wiring import build_window_quote_recorder
from tests.quotes.test_recorder_calendar import Alerts

GOOD = {"start": "14:30", "end": "14:40", "max_early_wait_minutes": 30}


def _cfg(entry):
    return {"quotes": {"windows": {"v4": entry}}}


def test_the_repository_config_holds_v4_at_1430_to_1440_with_a_30_minute_wait():
    window = named_window(load_app_config(), "v4")
    assert (window.start, window.end, window.max_early_wait_seconds) == (time(14, 30), time(14, 40), 1800)
    assert window.dataset(DATASET) == "groww/derivatives/quote-snapshots-v4"


@pytest.mark.parametrize(
    "cfg, words",
    [
        ({}, "no window named 'v4'"),
        ({"quotes": None}, "no window named 'v4'"),
        ({"quotes": {"windows": ["v4"]}}, "no window named 'v4'"),
        (_cfg({"start": "14:30", "end": "14:40"}), "needs exactly the keys"),
        (_cfg(GOOD | {"extra": 1}), "needs exactly the keys"),
        (_cfg(GOOD | {"start": "2:30pm"}), "is not a time"),
        (_cfg(GOOD | {"start": yaml.safe_load("14:30")}), "is not a time"),  # unquoted YAML 14:30 is the number 870
        (_cfg(GOOD | {"end": "14:30"}), "is not before end"),
        (_cfg(GOOD | {"max_early_wait_minutes": -1}), "whole number"),
        (_cfg(GOOD | {"max_early_wait_minutes": True}), "whole number"),
    ],
)
def test_a_missing_or_bad_window_is_refused_with_its_key(cfg, words):
    with pytest.raises(ConfigError, match=words):
        named_window(cfg, "v4")


def _args(tmp_path, entry=GOOD, source="configured", window="v4"):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(_cfg(entry)))
    return Namespace(config=str(path), source=source, window=window, outside_window=False)


def test_the_command_stops_before_any_request_on_a_bad_window_or_with_nse(tmp_path, capsys, monkeypatch):
    def no_build(*args):
        raise AssertionError("nothing may be built or asked")

    monkeypatch.setattr("fno.quotes.window_wiring.build_window_quote_recorder", no_build)
    assert _record_window(_args(tmp_path, window="v5"), Alerts(), "cal") == 1
    assert _record_window(_args(tmp_path, source="nse"), Alerts(), "cal") == 1
    out = capsys.readouterr().out
    assert out.count("nothing asked") == 2 and "no window named 'v5'" in out and "not --source nse" in out


def test_the_composition_root_builds_the_v4_capture_timed_stopped_and_in_its_own_dataset():
    recorder = build_window_quote_recorder(load_app_config(), "v4")
    assert recorder.dataset == "groww/derivatives/quote-snapshots-v4" and recorder.window.name == "v4"
    assert recorder.slot.stop_requests_at == time(14, 40) and recorder.slot.underlying == "NIFTY"
    assert isinstance(recorder.provider, TimedProvider) and isinstance(recorder.levels, TimedLevels)
    assert recorder.log is not None and recorder.store.prefix == "groww/derivatives/quote-snapshots-v4/"
