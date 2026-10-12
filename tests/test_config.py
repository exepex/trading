"""Clean-slate criterion 5: the app's settings hold only allowed keys; frozen research inputs still read as written."""

import pytest

from fno.config import ALLOWED_APP_KEYS, ROOT, ConfigError, load_app_config, load_config

# Every top-level key of the removed old desk's config.yaml.
REMOVED_KEYS = ("profile", "profiles", "account", "position_rules", "holding", "go_live_criteria", "performance_kill",
                "daily_limits", "expiry", "strategies", "signals", "liquidity", "exits", "live")  # fmt: skip
FROZEN_BACKTEST_INPUT = ROOT / "research" / "2026-10-12-backtest" / "inputs" / "config.yaml"


def test_the_repository_settings_hold_only_allowed_keys():
    assert set(load_app_config()) <= ALLOWED_APP_KEYS


@pytest.mark.parametrize("key", REMOVED_KEYS)
def test_each_removed_key_is_an_error(tmp_path, key):
    path = tmp_path / "config.yaml"
    path.write_text(f"provider: nse\n{key}: {{}}\n")
    with pytest.raises(ConfigError, match=key):
        load_app_config(path)


def test_an_override_cannot_add_a_removed_key():
    with pytest.raises(ConfigError, match="profile"):
        load_app_config(overrides={"profile": "live"})


def test_frozen_research_inputs_read_unchanged_with_their_old_keys():
    """Research studies read their own frozen settings copy; its charges are the values the study used."""
    frozen = load_config(FROZEN_BACKTEST_INPUT)
    assert "live" in frozen and frozen["charges"]["brokerage_per_order"] == 20.0
