"""Story C5b criteria 1-2 in C4, with C4's own reading of `docs/DESK_DECISIONS.md`: the same rules as C2, failing
closed as a malformed restart row does."""

import re
from datetime import date, datetime

import pytest

from fno.books.paths import book_folder
from fno.checks.validity_account import AccountProblem, LedgerAccounts
from fno.checks.validity_decisions import decision_rows
from fno.composition import open_account_writer
from fno.config import ROOT
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, DESK_DECISIONS_FILE, OWNER_OVERRIDES_FILE
from fno.models import IST
from tests.risk.builders import DECISIONS_HEADER

CUTOFF = datetime(2026, 10, 20, 15, 0, tzinfo=IST)
GOOD = '| 12 Oct 2026 | **Restart Book 1** (owner: "restart Book 1, I reviewed the loss") | Book 1 |'
BOOK_10 = '| 12 Oct 2026 | **Restart Book 10** (owner: "restart Book 10") | Book 10 |'
SECOND_BOLD = '| 12 Oct 2026 | **Restart** then **Restart Book 1** (owner: "restart Book 1") | Book 1 |'
COLUMNS = "date,action,reason,entered_by,decision\n"


def _facts(root, rows, restarts, book=BOOK1_RULES):
    with open_account_writer(book, root) as writer:
        writer.start(date(2026, 10, 1))
    (root / DESK_DECISIONS_FILE).parent.mkdir(parents=True, exist_ok=True)
    (root / DESK_DECISIONS_FILE).write_text(DECISIONS_HEADER + "\n".join(rows) + "\n")
    path = book_folder(root, book) / OWNER_OVERRIDES_FILE
    path.write_text(COLUMNS + "".join(f"{d},restart_brake,reviewed,owner,{t}\n" for d, t in restarts))
    return LedgerAccounts(root).facts(book, CUTOFF)


def test_c4_accepts_a_restart_citing_one_owner_row_for_its_book(tmp_path):
    assert _facts(tmp_path, [GOOD], [("2026-10-12", "Restart Book 1")]).restarts == (date(2026, 10, 12),)


@pytest.mark.parametrize(
    ("rows", "restarts", "book"),
    [
        ([GOOD], [("2026-10-12", "")], BOOK1_RULES),
        ([GOOD], [("2026-10-12", "Restart Book 9")], BOOK1_RULES),
        ([GOOD, GOOD.replace("12 Oct", "13 Oct")], [("2026-10-14", "Restart Book 1")], BOOK1_RULES),
        (['| 12 Oct 2026 | **Restart Book 1** (orchestrator decision) | Book 1 |'], [("2026-10-12", "Restart Book 1")],
         BOOK1_RULES),
        ([GOOD], [("2026-10-12", "Restart Book 1")], BOOK2_HYBRID),
        ([BOOK_10], [("2026-10-12", "Restart Book 10")], BOOK1_RULES),
        ([SECOND_BOLD], [("2026-10-12", "Restart Book 1")], BOOK1_RULES),
        ([GOOD], [("2026-10-12", "Restart Book 1")], "shadow:fly-v1"),
        ([GOOD], [("2026-10-11", "Restart Book 1")], BOOK1_RULES),
        ([GOOD], [("2026-10-12", "Restart Book 1"), ("2026-10-15", "Restart Book 1")], BOOK1_RULES),
    ],
)  # fmt: skip
def test_c4_refuses_every_other_restart(tmp_path, rows, restarts, book):
    with pytest.raises(AccountProblem):
        _facts(tmp_path, rows, restarts, book)


def test_c4_reads_the_committed_decisions_file_with_each_rows_first_bold_title():
    text = (ROOT / DESK_DECISIONS_FILE).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if re.match(r"\| \d{1,2} [A-Z][a-z]{2} \d{4} \|", line)]
    expected = [cell.split("**")[1] if "**" in cell else None for cell in (line.split("|")[2] for line in lines)]
    assert [title for _, title, _ in decision_rows(ROOT / DESK_DECISIONS_FILE)] == expected and len(expected) >= 152
