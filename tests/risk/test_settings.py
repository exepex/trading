"""Story C2: every limit comes from config.yaml `risk` (an allowed key), checked at start-up; the replay scenarios
match the panel's NIFTY 50 and India VIX closes."""

import copy
import csv

import pytest

from fno.config import ALLOWED_APP_KEYS, ROOT, load_app_config
from fno.constants import RISK_PROFILE_MANUAL
from fno.risk.profile_settings import profile_settings
from fno.risk.settings import RiskSettingsError, risk_settings

CONFIG = load_app_config()
CLOSES = ROOT / "research" / "data" / "nifty-panel" / "warmup_closes.csv"


def _with(path: tuple[str, ...], value):
    cfg = copy.deepcopy(CONFIG)
    block = cfg
    for key in path[:-1]:
        block = block[key]
    if value is None:
        del block[path[-1]]
    else:
        block[path[-1]] = value
    return cfg


def _manual(cfg):
    return profile_settings(cfg, RISK_PROFILE_MANUAL)


def test_risk_is_an_allowed_key_and_the_repository_settings_hold_the_owners_limits():
    """C2's original limits now live in the Manual profile, unchanged (the books' are story C5's)."""
    assert "risk" in ALLOWED_APP_KEYS
    s, m = risk_settings(CONFIG, ROOT), _manual(CONFIG)
    assert (m.max_loss_per_trade_rs, m.max_open_trades, m.drawdown_brake_rs, m.max_stress_loss_rs) == (
        10000,
        3,
        30000,
        30000,
    )
    assert s.margins_table == "margins/margins" and m.margin_age_days == 7  # Drive's data area (O9b step 2)
    assert s.stressed_margin.method == "multiplier" and s.stressed_margin.max_age_days == 30


def test_the_design_scenarios_are_all_configured():
    moves = {(sc.nifty_move_pct, sc.iv_factor) for sc in risk_settings(CONFIG, ROOT).scenarios}
    for expected in [(-8, 1), (-5, 1), (5, 1), (8, 1), (0, 2), (0, 0.5), (-8, 2), (5, 0.5)]:
        assert expected in moves
    assert all(sc.days == 1 for sc in risk_settings(CONFIG, ROOT).scenarios)


@pytest.mark.parametrize(
    "path",
    [
        ("risk",),
        ("risk", "scenarios"),
        ("risk", "stress_line"),
        ("risk", "margins"),
        ("risk", "stressed_margin"),
    ],
)
def test_a_missing_shared_setting_is_an_error_never_a_default(path):
    with pytest.raises(RiskSettingsError, match=path[-1]):
        risk_settings(_with(path, None), ROOT)


@pytest.mark.parametrize(
    "key",
    ["max_loss_per_trade_rs", "max_open_trades", "drawdown_brake_rs", "max_stress_loss_rs", "exposure"],
)
def test_a_missing_manual_setting_is_an_error_never_a_default(key):
    with pytest.raises(RiskSettingsError, match=key):
        _manual(_with(("risk", "profiles", "manual", key), None))


def test_a_missing_nested_exposure_limit_is_an_error():
    with pytest.raises(RiskSettingsError, match="max_move_loss_rs"):
        _manual(_with(("risk", "profiles", "manual", "exposure", "max_move_loss_rs"), None))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("risk", "profiles", "manual", "max_open_trades"), 2.5),
        (("risk", "profiles", "manual", "max_loss_per_trade_rs"), -1),
        (("risk", "profiles", "manual", "drawdown_brake_rs"), "x"),
        (("risk", "profiles", "manual", "max_open_trades"), True),
    ],
)
def test_an_unusable_profile_setting_is_an_error(path, value):
    with pytest.raises(RiskSettingsError):
        _manual(_with(path, value))


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("risk", "stressed_margin", "method"), "guess"),
        (("risk", "stressed_margin", "multiplier"), 0.9),
        (("risk", "scenarios"), []),
    ],
)
def test_an_unusable_shared_setting_is_an_error(path, value):
    with pytest.raises(RiskSettingsError):
        risk_settings(_with(path, value), ROOT)


def _closes() -> list[dict[str, str]]:
    with open(CLOSES, encoding="utf-8") as fh:
        return [row for row in csv.DictReader(fh) if row["session"] != "muhurat"]


def _move(rows, day: str) -> tuple[float, float]:
    """NIFTY move in % and the India VIX ratio, from the previous session's close to that day's close."""
    i = next(i for i, row in enumerate(rows) if row["date"] == day)
    before, after = rows[i - 1], rows[i]
    nifty = (float(after["underlying"]) / float(before["underlying"]) - 1) * 100
    return nifty, float(after["vix"]) / float(before["vix"])


def test_replay_scenarios_match_the_panels_nifty_and_vix_closes():
    rows = _closes()
    replays = {sc.name: sc for sc in risk_settings(CONFIG, ROOT).scenarios if sc.name.startswith("replay_")}
    assert set(replays) == {"replay_2020-03-23", "replay_2024-06-04", "replay_2026-02-01", "replay_2026-02-03"}
    for name, scenario in replays.items():
        nifty, vix = _move(rows, name.removeprefix("replay_"))
        assert scenario.nifty_move_pct == pytest.approx(nifty, abs=5e-5), name
        assert scenario.iv_factor == pytest.approx(vix, abs=5e-5), name


def test_the_february_2026_replays_are_its_largest_fall_and_largest_move():
    rows = _closes()
    feb = {row["date"]: _move(rows, row["date"])[0] for row in rows if row["date"].startswith("2026-02")}
    assert min(feb, key=feb.get) == "2026-02-01"  # Budget day, -1.96%
    assert max(feb, key=lambda d: abs(feb[d])) == "2026-02-03"  # +2.55%
