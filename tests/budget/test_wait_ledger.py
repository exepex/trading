"""Story BG1-w criterion 4: the usage ledger's `wait_minutes` column. Blank means no wait measured apart; a value is a
number of minutes >= 0, checked on reading like `minutes`. The committed ledger gained the column with every earlier
value unchanged (rows are written once)."""

import csv
import io
import subprocess

import pytest

from fno.budget.usage_ledger import COLUMNS, LEDGER_FILE, UsageLedger
from fno.config import ROOT

BEFORE_THE_COLUMN = "d062fe347"  # main just before BG1-w: the ledger without `wait_minutes`
ROW = {"date": "2026-10-14", "purpose": "books_and_roles", "book": "book2_hybrid", "role_or_bundle": "",
       "session_id": "session_01BOOKxyz", "model": "", "minutes": "3.50", "wait_minutes": "26.17", "turns": "1",
       "input_tokens": "", "output_tokens": "", "cache_read_tokens": "", "cache_write_tokens": "",
       "tokens_basis": "not available", "source": "x", "complete_before": "2026-10-15"}  # fmt: skip


def ledger_with(tmp_path, **changes):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerow(ROW | changes)
    (tmp_path / LEDGER_FILE).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / LEDGER_FILE).write_text(out.getvalue(), encoding="utf-8")
    return UsageLedger(tmp_path)


def test_the_wait_column_follows_minutes():
    assert COLUMNS[COLUMNS.index("minutes") + 1] == "wait_minutes"


@pytest.mark.parametrize("wait", ["26.17", "0.00", ""])  # good, boundary, empty
def test_a_wait_of_zero_or_more_or_blank_is_read(tmp_path, wait):
    assert ledger_with(tmp_path, wait_minutes=wait).rows()[0]["wait_minutes"] == wait


@pytest.mark.parametrize("wait", ["-1", "-0.01", "nan", "inf", "soon"])
def test_a_negative_or_non_number_wait_is_refused(tmp_path, wait):
    with pytest.raises(ValueError, match="wait_minutes"):
        ledger_with(tmp_path, wait_minutes=wait).rows()


def test_the_committed_ledger_gained_the_column_and_changed_no_earlier_value():
    old = subprocess.run(["git", "-C", str(ROOT), "show", f"{BEFORE_THE_COLUMN}:{LEDGER_FILE}"], check=True,
                         capture_output=True, text=True).stdout  # fmt: skip
    earlier = list(csv.DictReader(io.StringIO(old)))
    now = UsageLedger(ROOT).rows()
    assert earlier and [row | {"wait_minutes": ""} for row in earlier] == now[: len(earlier)]
