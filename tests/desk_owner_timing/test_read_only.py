"""E8 acceptance 12: the owner-timing package's import closure reaches no broker order, position, margin or funds
call (A16b's test pattern). Its funds checks are the desk's own C2 and C4 checks on paper accounts."""

from __future__ import annotations

import re
from pathlib import Path

import fno
from fno.desk import owner_timing
from tests.intraday_backfill.test_read_only import _closure

BROKER_CALL = re.compile(
    r"\b(place|modify|cancel)_\w*order|get_positions|get_holdings|_margin_details|get_\w*funds", re.I
)


def test_the_package_reaches_no_broker_call():
    package = Path(owner_timing.__file__).parent
    closure = set().union(*(_closure(path) for path in package.glob("*.py")))
    assert {"mark_snapshots.py", "groww.py", "entries.py"} <= {p.name for p in closure}
    hits = {p.relative_to(Path(fno.__file__).parent).as_posix(): BROKER_CALL.findall(p.read_text()) for p in closure}
    assert not {path: found for path, found in hits.items() if found}
