"""Story C5b criteria 1-3 in C2: a brake restart lifts the brake only when it cites one owner row of
`docs/DESK_DECISIONS.md` that quotes the owner, names the book and is dated on or before the restart; every other case
fails closed with its reason. The committed decisions file parses."""

import re
from collections import Counter
from datetime import date

import pytest

from fno.config import ROOT
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, DESK_DECISIONS_FILE
from fno.risk.decision_rows import read_decision_rows
from fno.risk.inputs import RiskInputError
from fno.risk.overrides import OVERRIDE_COLUMNS, brake_restarts, overrides_file

from .builders import DECISIONS_HEADER

DAY = date(2026, 10, 20)
GOOD = '| 12 Oct 2026 | **Restart Book 1** (owner: "restart Book 1, I reviewed the loss") | Book 1 |'
BOOK_10 = '| 12 Oct 2026 | **Restart Book 10** (owner: "restart Book 10") | Book 10 |'
SECOND_BOLD = '| 12 Oct 2026 | **Restart** then **Restart Book 1** (owner: "restart Book 1") | Book 1 |'


def _plant(root, decision_rows, restarts, book=BOOK1_RULES):
    path = root / DESK_DECISIONS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DECISIONS_HEADER + "\n".join(decision_rows) + "\n")
    file = overrides_file(root, book)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        ",".join(OVERRIDE_COLUMNS) + "\n" + "".join(f"{d},restart_brake,reviewed,owner,{t}\n" for d, t in restarts)
    )
    return brake_restarts(root, book, DAY)


def test_a_restart_citing_one_owner_row_for_its_book_lifts_the_brake(tmp_path):
    assert _plant(tmp_path, [GOOD], [("2026-10-12", "Restart Book 1")]) == (date(2026, 10, 12),)


@pytest.mark.parametrize(
    ("rows", "restarts", "book", "problem"),
    [
        ([GOOD], [("2026-10-12", "")], BOOK1_RULES, "cites no decision"),
        ([GOOD], [("2026-10-12", "Restart Book 9")], BOOK1_RULES, "title of 0 rows"),
        ([GOOD, GOOD.replace("12 Oct", "13 Oct")], [("2026-10-14", "Restart Book 1")], BOOK1_RULES, "title of 2 rows"),
        (['| 12 Oct 2026 | **Restart Book 1** (orchestrator decision) | Book 1 |'], [("2026-10-12", "Restart Book 1")],
         BOOK1_RULES, "does not quote the owner"),
        ([GOOD], [("2026-10-12", "Restart Book 1")], BOOK2_HYBRID, "does not name Book 2"),
        ([BOOK_10], [("2026-10-12", "Restart Book 10")], BOOK1_RULES, "does not name Book 1"),
        ([SECOND_BOLD], [("2026-10-12", "Restart Book 1")], BOOK1_RULES, "title of 0 rows"),
        ([GOOD], [("2026-10-12", "Restart Book 1")], "shadow:fly-v1", "not named in the owner's decisions"),
        ([GOOD], [("2026-10-11", "Restart Book 1")], BOOK1_RULES, "dated after the restart"),
        ([GOOD], [("2026-10-12", "Restart Book 1"), ("2026-10-15", "Restart Book 1")], BOOK1_RULES,
         "more than one restart"),
    ],
)  # fmt: skip
def test_every_other_restart_fails_closed_with_its_reason(tmp_path, rows, restarts, book, problem):
    with pytest.raises(RiskInputError, match=problem):
        _plant(tmp_path, rows, restarts, book)


def test_the_committed_decisions_file_parses_every_row_with_its_first_bold_title():
    """Counted a second way (split on "**"); judge 134 measured 152 rows, 17 without a title and "approved" as the title
    of 4 rows on 15 Oct 2026. Those are floors: the owner keeps adding rows, so exact numbers would break the suite."""
    text = (ROOT / DESK_DECISIONS_FILE).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if re.match(r"\| \d{1,2} [A-Z][a-z]{2} \d{4} \|", line)]
    expected = [cell.split("**")[1] if "**" in cell else None for cell in (line.split("|")[2] for line in lines)]
    rows = read_decision_rows(ROOT / DESK_DECISIONS_FILE)
    assert [row.title for row in rows] == expected
    titles = Counter(title for title in expected if title)
    assert len(rows) >= 152 and expected.count(None) >= 17 and titles["approved"] >= 4
