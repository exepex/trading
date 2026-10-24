"""Story G6 freeze, criterion 3 (judge 597 SF1-SF2): v4's Black-76 runs at the protocol's 6.5% (section 1.4) from
`fno/forecast_v4/pricing.py`, never `config.yaml`'s `risk_free_rate`; the pack's IV30 method hashes the rate; and no
v4 module reads the configured rate (G7b's two readers moved to `pricing.py` in 432071d63, 24 Oct)."""

from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import CONFIG_RATE, rate_readers
from fno.forecast_v4.pricing import V4_RISK_FREE_RATE
from fno.v4_pack.wiring import IV30_METHOD_FILES, build_iv30_rule

ROOT = Path(__file__).resolve().parents[2]
PENDING_G7B: set[str] = set()  # G7b's back-fill and terms read `pricing.V4_RISK_FREE_RATE` since 432071d63


def test_the_rate_is_the_protocols_and_the_packs_iv30_rule_runs_at_it():
    assert V4_RISK_FREE_RATE == 0.065 and build_iv30_rule().rate == 0.065


def test_every_pack_names_the_rate_through_its_iv30_method():
    assert "forecast_v4/pricing.py" in IV30_METHOD_FILES


def test_no_v4_module_reads_the_configured_rate():
    """The freeze tool refuses while any reader is left; this test fails when one is added anywhere."""
    assert set(rate_readers(ROOT)) == PENDING_G7B


def test_the_pattern_finds_a_config_read_and_a_build_atm_iv30_call_and_ignores_a_comment():
    assert CONFIG_RATE.search('LiveAtmIvMinusRealised(None, cfg["risk_free_rate"], Black76())')
    assert CONFIG_RATE.search("rate = config.get('risk_free_rate')")
    assert CONFIG_RATE.search("estimator = build_atm_iv30(cfg)")
    assert not CONFIG_RATE.search("# never `config.yaml`'s `risk_free_rate`; never `build_atm_iv30`")
