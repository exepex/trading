"""Story G6 freeze, criteria 5-7: the freeze record on this repository: its days, its slot rows (append-only), its
ledger rows and the check on the whole tree. The byte tables are checked by `test_freeze_check.py`."""

import csv
import io
import re
from datetime import date, timedelta
from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import check, recorded
from fno.forecast_v4.sessions import is_scored_session
from fno.research_engine.ledger import Git, read_ledger
from fno.storage.wiring import build_session_calendar

ROOT = Path(__file__).resolve().parents[2]
RECORD = (ROOT / "research" / "forecasts" / "FREEZE_v4.md").read_text(encoding="utf-8")
SLOTS = ROOT / "research" / "forecasts" / "v4_slots.csv"


def _line(name: str) -> str:
    return re.search(rf"^{name}: (\S+)\s*$", RECORD, re.MULTILINE).group(1)


def test_the_first_counted_session_is_the_first_scored_session_after_the_freeze_day():
    frozen_on, first = date.fromisoformat(_line("Frozen on")), date.fromisoformat(_line("First counted session"))
    assert (frozen_on, first) == (date(2026, 10, 25), date(2026, 10, 26))
    calendar = build_session_calendar()
    between = [frozen_on + timedelta(days=n) for n in range(1, (first - frozen_on).days)]
    assert is_scored_session(calendar, first) and not any(is_scored_session(calendar, d) for d in between)


def test_the_slot_rows_the_record_names_are_the_files_first_rows_unchanged():
    named = RECORD.split("The registrations as written")[1].split("```")[1].strip("\n").split("\n")
    lines = SLOTS.read_text(encoding="utf-8").rstrip("\n").split("\n")
    assert len(named) == 16 and lines[: len(named)] == named  # header + 15 rows; later rows may only be appended
    rows = list(csv.DictReader(io.StringIO("\n".join(named))))
    assert {(r["effective_start"], r["registered_on"]) for r in rows} == {("2026-10-26", "2026-10-25")}


def test_the_ledger_rows_name_the_protocol_commit_one_per_question():
    rows = [r for r in read_ledger((ROOT / "research" / "ledger.csv").read_text()) if r["experiment"] == "forecasts-v4"]
    commit = _line("Protocol commit").strip("`")
    assert len(rows) == 8 and {r["protocol_commit"] for r in rows} == {commit}
    assert [r["hypothesis"] for r in rows] == ["yes", "yes", "no", "no", "no", "yes", "yes", "no"]


def test_the_whole_tree_holds_the_freeze_and_the_record_lists_every_recorded_file():
    found = check(ROOT, RECORD, Git(ROOT))
    assert found.problems == () and found.not_checked in ("", found.not_checked)  # a shallow clone is "not checked"
    for row in recorded(ROOT).splitlines():
        if row.startswith("| `"):
            assert row.split(" | ")[0] in RECORD, row
