"""Story A22 is read-only: no file of the package names a trading call, and Groww is held only through A16's
`ReadOnlyGroww`, built in the composition root."""

from __future__ import annotations

import re
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2] / "fno" / "preopen"
TRADING_CALL = re.compile(r"\.(place|modify|cancel)_\w*\(")


def test_no_file_names_a_trading_call():
    assert not [p.name for p in PACKAGE.glob("*.py") if TRADING_CALL.search(p.read_text())]


def test_groww_is_built_only_in_the_wiring_and_only_behind_the_read_only_allow_list():
    holders = [p.name for p in PACKAGE.glob("*.py") if "GrowwProvider" in p.read_text()]
    assert holders == ["wiring.py"]
    assert "ReadOnlyGroww(lambda: provider.api)" in (PACKAGE / "wiring.py").read_text()
