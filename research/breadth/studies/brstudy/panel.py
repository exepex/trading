"""The study panel: one row per (session, underlying), `extract.py`'s columns.

Legacy files (spot = the near-month future) up to 2023-12-31; UDiFF files (spot = `UndrlygPric`) from 2024-01-01.
Columns: `extract.py`'s plus `next_spot`, the same near-month contract's close on the next session (legacy rows; empty
on UDiFF rows, whose outcome uses the next row's spot). `overlap` writes both formats' rows for the 128 sessions where
both exist (study 1's comparison)."""

import csv
from pathlib import Path

from . import legacy
from .sizing_tools import extract

UDIFF_FROM, OVERLAP_TO = "2024-01-01", "2024-07-05"
COLUMNS = (*extract.COLUMNS, "next_spot", "source")
LEGACY, UDIFF = "legacy", "udiff"


def _futures(text: str) -> dict[str, str]:
    return dict(part.split("=") for part in text.split("|") if part)


def link_next(rows: list[dict]) -> list[dict]:
    """Fills `next_spot` on legacy rows: the next session's close of the row's own near-month contract."""
    by_day: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_day.setdefault(r["day"], {})[r["underlying"]] = r
    days = sorted(by_day)
    for day, nxt in zip(days, days[1:], strict=False):
        for u, r in by_day[day].items():
            later = by_day[nxt].get(u)
            r["next_spot"] = _futures(later["futures"]).get(r["proxy_expiry"], "") if later else ""
    return [{**{k: r.get(k, "") for k in COLUMNS}, "source": LEGACY} for r in rows]


def _write(out: Path, rows) -> None:
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _legacy_rows(folder: Path, keep) -> list[dict]:
    rows = []
    for path in sorted(folder.glob("*.zip")):
        if keep(path.stem):
            rows += legacy.day_rows(path.stem, legacy.bhavcopy_rows(path))
    return link_next(rows)


def _udiff_rows(folder: Path, keep):
    for path in sorted(folder.glob("*.zip")):
        if keep(path.stem):
            yield from ({**r, "source": UDIFF} for r in extract.day_rows(path.stem, extract.bhavcopy_rows(path)))


def build(legacy_folder: Path, udiff_folder: Path, out: Path) -> None:
    old = _legacy_rows(legacy_folder, lambda d: d < UDIFF_FROM)
    new = _udiff_rows(udiff_folder, lambda d: d >= UDIFF_FROM)
    _write(out, [*old, *new])


def overlap(legacy_folder: Path, udiff_folder: Path, out_legacy: Path, out_udiff: Path) -> None:
    def keep(d):
        return UDIFF_FROM <= d <= OVERLAP_TO

    _write(out_legacy, _legacy_rows(legacy_folder, keep))
    _write(out_udiff, _udiff_rows(udiff_folder, keep))
