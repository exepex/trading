"""Story F9a fixtures, on S3's (`tests/scoreboard/matched_builders.py`): paired rows, role sets, shadow runs and F8
usage rows. Charges are Rs 20 an order and the lot is 75, so every one-lot net can be checked by hand."""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path

from fno.constants import BOOK2_HYBRID
from fno.playbook.decision_store import record_file
from fno.role_value.records import SHADOW_FOLDER
from fno.role_value.role_set import RoleSet
from fno.role_value.rows import COLUMNS, PairedRow, PairedRowFile

BOOK = BOOK2_HYBRID
ROLES = RoleSet.of(BOOK, "1", {"macro": ["macro_economist"], "positioning": ["positioning_analyst"],
                               "vol": ["volatility_trader", "options_strategist"]})  # fmt: skip


def row(day: date, unit: str, *, status: str = "scored", consulted: tuple[str, ...] = ("macro", "positioning", "vol"),
        pack: str = "p", shadow_pack: str | None = None, snap: str | None = None, shadow_snap: str | None = None,
        version: str = "1") -> PairedRow:  # fmt: skip
    snap = snap or f"snap-{day.isoformat()}"
    return PairedRow(day, BOOK, version, unit, consulted, f"{day.isoformat()}-{BOOK}", f"shadow-{day.isoformat()}",
                     pack, shadow_pack or pack, snap, shadow_snap or snap, status)  # fmt: skip


def write_rows(root: Path, rows: list[PairedRow]) -> None:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for r in rows:
        writer.writerow({**{c: getattr(r, c) for c in COLUMNS if c not in ("day", "consulted_units")},
                         "day": r.day.isoformat(), "consulted_units": ";".join(r.consulted_units)})  # fmt: skip
    path = PairedRowFile(root).path(BOOK)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.getvalue())


def write_shadow(root: Path, day: date, *records: dict) -> None:
    folder = root / "journal" / BOOK / SHADOW_FOLDER / day.isoformat() / f"shadow-{day.isoformat()}"
    folder.mkdir(parents=True, exist_ok=True)
    for body in records:
        (folder / record_file(body["opportunity_id"])).write_text(json.dumps(body, sort_keys=True))


def write_role_units(root: Path) -> None:
    path = root / "agents" / "role_units.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{BOOK}:\n  '1':\n    macro: [macro_economist]\n    positioning: [positioning_analyst]\n"
                    "    vol: [volatility_trader, options_strategist]\n")  # fmt: skip


def usage(day: date, minutes: str, book: str = BOOK, purpose: str = "books_and_roles") -> dict:
    return {"date": day.isoformat(), "purpose": purpose, "book": book, "role_or_bundle": "", "minutes": minutes}
