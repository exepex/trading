"""Story C2d test helper: a stress factor file with one row, the way A14c's job writes it (the factor in force on a
decision day is the latest row dated strictly before it)."""

import tempfile
from datetime import date
from pathlib import Path

from fno.constants import STRESS_FACTOR_COLUMNS

_DIR = Path(tempfile.mkdtemp(prefix="stress-factor-"))
HEADER = ",".join(STRESS_FACTOR_COLUMNS) + "\n"


def factor_file(factor: float, as_of: date, status: str = "applied") -> Path:
    path = _DIR / f"k{factor:g}_{as_of}_{status}.csv"
    if not path.exists():
        path.write_text(HEADER + f"{as_of},{factor:g},{factor:g},{factor:g},{status},test,{as_of},\n", encoding="utf-8")
    return path
