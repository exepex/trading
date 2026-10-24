"""Story G6 freeze, criterion 3: v4's Black-76 runs at the protocol's 6.5% (section 1.4), never at `config.yaml`'s
`risk_free_rate`, which other stories read and may move; no byte-checked v4 file reads that setting."""

import re
from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import byte_checked
from fno.v4_pack.model import PACK_RISK_FREE_RATE
from fno.v4_pack.wiring import build_iv30_rule

ROOT = Path(__file__).resolve().parents[2]
CONFIG_RATE = re.compile(r"""\[\s*["']risk_free_rate["']\s*\]|get\(\s*["']risk_free_rate["']""")


def test_the_packs_iv30_rule_runs_at_the_protocols_rate():
    assert PACK_RISK_FREE_RATE == 0.065
    assert build_iv30_rule().rate == 0.065


def test_no_byte_checked_v4_file_reads_the_configured_rate():
    readers = [p for p in byte_checked(ROOT) if p.endswith(".py") and CONFIG_RATE.search((ROOT / p).read_text())]
    assert readers == []


def test_the_pattern_finds_a_config_read_and_ignores_a_comment():
    assert CONFIG_RATE.search('LiveAtmIvMinusRealised(None, cfg["risk_free_rate"], Black76())')
    assert CONFIG_RATE.search("rate = config.get('risk_free_rate')")
    assert not CONFIG_RATE.search("# never `config.yaml`'s `risk_free_rate`")
