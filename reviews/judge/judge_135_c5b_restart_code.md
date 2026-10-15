# Judge 135: story C5b code, a brake restart must cite one owner decision row (judge C)

Date: 15 Oct 2026 (UTC). Branch `story/c5b-restart-decision` at **b2a4b0dd322c29b639d2b07530491e5bab173b0e**.
- Claims: response 135 addendum 2.
- The story text was passed by judge A (judge 134 addendum 1).
- Judged on the real paths, under the owner's "keep the design simple" rule.

## Gates

- `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: **5,468 passed** (the builder's figure).
- ruff check, format and `check_imports.py` are clean.
- `merge-tree` with `origin/main`: no conflict.

## Verdict: PASS (code)

| Real path | Status | Evidence |
|---|---|---|
| A restart counts only with a citation | MET | C2 (`fno/risk/decision_rows.py`, called from `overrides.brake_restarts`) and C4 (`fno/checks/validity_decisions.py`, called from `LedgerAccounts.facts`) each read `docs/DESK_DECISIONS.md` themselves. The cited title must be the first bold span of exactly one dated row, and that row must hold `(owner: "`, name the book as a whole word and be dated on or before the restart. A title may be used once per book. Any failure raises (C2 `RiskInputError`, C4 `AccountProblem`), so the brake stays on: fail closed |
| "Book 1" never matches "Book 10" | MET | `\bBook 1\b` finds no word boundary between `1` and `0` |
| C4 independent of C2 | MET | C4 has its own regex and parser, with no `fno.risk` import |
| Existing data | MET | No `owner_overrides.csv` exists on `main` (`git ls-tree` on origin/main), so the new `decision` column breaks no stored file |
| The audit step | MET | `docs/JUDGE.md` "Brake restarts": every override-row change is lane 1, and the judge reads the cited row and confirms the owner's own words restart that episode |

### The orchestrator's two points

- **Criterion 3's minimums (at least 152 rows, at least 17 untitled, at least 4 "approved"): accepted.**
  `DESK_DECISIONS.md` is append-only, so exact counts would break on every new owner row. The real check is that the
  parser's titles equal a second, independent count by splitting on `**`, row for row
  (`test_validity_restart.py:64`, `test_restart_decision.py:72`). The minimums only guard against the parser reading
  nothing.
- **Shadow-book brakes cannot be lifted: agreed for now.** `BOOK_DISPLAY_NAMES` holds Books 1-3 only, so a shadow's
  restart is refused by name (fail closed). Shadows are research records that never trade money. If a shadow ever needs
  its brake lifted, that is an owner decision and a story.

**Note (does not change a trade):** the book must be named exactly "Book 1", "Book 2" or "Book 3" in the owner's row.
A row saying "all books" or "book 1" in lower case is refused (fail closed, the reason names it). The owner or the
orchestrator then words the row with the book's name.

**Verdict: PASS for b2a4b0dd322c29b639d2b07530491e5bab173b0e** (code). Rule 9: ChatGPT next.
