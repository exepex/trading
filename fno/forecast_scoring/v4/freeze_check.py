"""Protocol v4's freeze check (protocol section 10; the freeze plan, response 287): which files the freeze record
`research/forecasts/FREEZE_v4.md` byte-checks, the table it carries, and every way the repository has moved since.
One place for the list, so the record's table and the check cannot disagree."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ...weather.wiring import METHOD_FILES as M1_METHOD_FILES

BYTE_CHECKED_GLOBS = (
    "research/forecasts/PROTOCOL_v4.md",
    "research/forecasts/PROTOCOL_v4_calibration.md",
    "fno/forecast_v4/*.py",  # every rule of the protocol
    "tools/v4_*.py",  # the calibration tools
    "research/forecasts/v4_*.json",  # their committed tables
    "research/forecasts/v4_*.md",
    "tests/fixtures/forecast_v4/v4_golden.json",
    "fno/forecast_v4_rules/*.py",  # G7: baselines, rules, outcomes' series, records
    "fno/forecast_scoring/v4/*.py",  # G8: scoring, comparisons, the looks, this check
    "fno/forecast_scoring/scores.py",  # G4's log-score clip and calibration bins in v4's reported scores (judge 177)
    "fno/intraday/realised_vol.py",  # A16's V1 arithmetic and void rule (judge 177)
    "fno/intraday/session_rv.py",
    "fno/intraday/status.py",
    "fno/intraday/slots.py",
)
RECORDED_NOT_CHECKED = (  # shared and changed by other stories; their behaviour is locked by v4's tests
    "fno/constants.py",
    "fno/desk/settlement.py",
    "fno/research_data/calendar.py",
    "fno/research_engine/implied_vol.py",
    "fno/intraday/rv_table.py",
    "fno/forecast/iv30.py",
)
ROW = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", re.MULTILINE)


def byte_checked(root: Path) -> list[str]:
    """Every byte-checked path that exists today, M1's method files (V6's rules slot, decision 70) included."""
    found = {p.relative_to(root).as_posix() for pattern in BYTE_CHECKED_GLOBS for p in root.glob(pattern)}
    found |= {f"fno/{name}" for name in M1_METHOD_FILES if (root / "fno" / name).is_file()}
    return sorted(p for p in found if "__pycache__" not in p)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(root: Path) -> str:
    """The record's table: one row per byte-checked file with its SHA-256."""
    rows = [f"| `{path}` | `{sha256(root / path)}` |" for path in byte_checked(root)]
    return "\n".join(["| File | SHA-256 |", "|---|---|", *rows])


def recorded() -> str:
    """The record's list of files recorded but not byte-checked."""
    return "\n".join(f"- `{path}`" for path in RECORDED_NOT_CHECKED)


def problems(root: Path, record: str) -> list[str]:
    """Every difference between the record's table and the repository: a file changed or gone, and a file now in a
    byte-checked folder that the record does not list (a new rule added after the freeze). Empty: v4 is intact."""
    pinned = dict(ROW.findall(record))
    found = []
    for path, digest in sorted(pinned.items()):
        if not (root / path).is_file():
            found.append(f"{path}: gone since the freeze")
        elif sha256(root / path) != digest:
            found.append(f"{path}: changed since the freeze (a change is a new version, never an edit)")
    found += [f"{path}: added after the freeze" for path in byte_checked(root) if path not in pinned]
    return found
