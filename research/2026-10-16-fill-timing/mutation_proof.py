"""Mutation proof of the FT1 tests: plants each bug below in a copy-free way (edit, test, restore) and checks the
synthetic tests fail. `python mutation_proof.py` from anywhere; restores every file even when a run fails."""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE / "ft1study"
ROOT = HERE.parents[1]
M = [
    (
        "observe.py",
        "c=position_value(entry.legs, filled) - position_value(entry.legs, decided)",
        "c=position_value(entry.legs, decided) - position_value(entry.legs, filled)",
        "sign error",
    ),
    (
        "observe.py",
        "        if any(bar.stale for bar in bars):\n            return None, STALE\n",
        "",
        "stale substitution",
    ),
    ("days.py", "MIN_SESSIONS_TO_EXPIRY = 7", "MIN_SESSIONS_TO_EXPIRY = 6", "expiry-week entry"),
    ("times.py", "LAST_SAME_DAY_MARK = time(15, 25)", "LAST_SAME_DAY_MARK = time(15, 45)", "wrong R mapping"),
    ("times.py", "CARD_DELAY = timedelta(minutes=8)", "CARD_DELAY = timedelta(minutes=0)", "no card delay"),
    ("figures.py", "return sum(o.c > threshold * o.risk", "return sum(o.c >= threshold * o.risk", "threshold >="),
    ("cells.py", "LEFT_OUT_SHARE_CAP = 0.10", "LEFT_OUT_SHARE_CAP = 0.20", "cap 20%"),
    (
        "flips.py",
        "won, still = at_decision > 0, at_fill > 0",
        "won, still = at_decision >= 0, at_fill >= 0",
        "zero is a win",
    ),
    (
        "flips.py",
        "(SIDE_BUY, SIDE_SELL) if leg.bought else (SIDE_SELL, SIDE_BUY)",
        "(SIDE_SELL, SIDE_BUY) if leg.bought else (SIDE_BUY, SIDE_SELL)",
        "charge sides",
    ),
    ("bootstrap.py", 'f"{SEED}:{name}"', 'f"{SEED}"', "seed ignores name"),
    ("figures.py", '"below 0.5%" if o.gap < 0.005', '"below 0.5%" if o.gap <= 0.005', "gap boundary"),
    ("figures.py", "MIN_DAYS = 30", "MIN_DAYS = 20", "too-few 20"),
    (
        "observe.py",
        "if entry.family in STRUCTURES_BOUGHT_ONLY else float(entry.width)",
        "if False else float(entry.width)",
        "risk scale",
    ),
    ("timepart.py", "MINUTES_A_YEAR = 365 * 1440", "MINUTES_A_YEAR = 252 * 1440", "year length"),
    (
        "days.py",
        "        if self.calendar.session_kind(following) != REGULAR:\n            return NEXT_NOT_REGULAR, None\n",
        "",
        "next-session rule",
    ),
    (
        "cells.py",
        "    values = [max(a.c, 0.0) - max(b.c, 0.0) for a, b in days]",
        "    values = [a.c - b.c for a, b in days]",
        "paired not bad-side",
    ),
    ("plan.py", "MAX_WINDOW_DAYS = 90", "MAX_WINDOW_DAYS = 120", "window 120"),
    (
        "fetch.py",
        "MARKET_FROM, MARKET_TO = time(9, 0), time(15, 45)",
        "MARKET_FROM, MARKET_TO = time(9, 0), time(15, 30)",
        "market hours",
    ),
]
caught = 0
for f, old, new, name in M:
    p = S / f
    src = p.read_text()
    assert old in src, name
    p.write_text(src.replace(old, new, 1))
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-x", str(ROOT / "tests" / "research_ft1")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
    finally:
        p.write_text(src)
    ok = r.returncode != 0
    caught += ok
    print(("CAUGHT " if ok else "MISSED ") + name)
print(f"{caught} of {len(M)}")
