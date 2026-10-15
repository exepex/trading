# Response 135: story C5b, a brake restart cites the owner's decision row (story text for the judge's check)

Builder: Claude, 15 Oct 2026. Branch `story/c5b-restart-decision` from `origin/main` (8b21876). Story text:
`docs/stories/C-code-roles.md` section C5b. Lane 1 (the brake: money and risk; `journal/` records). Text only; code
after the judge's check passes (quality rule 1).

## In short

- **A new column.** `owner_overrides.csv` gets a fifth column, `decision`: the exact bold title of a
  `docs/DESK_DECISIONS.md` row.
- **Five rules for a valid restart.** The cited row:
  - exists exactly once;
  - quotes the owner (`(owner: "`);
  - names the book;
  - is dated on or before the restart;
  - is not reused by another restart of that book.
- **Both checks, failing closed.** C2 and C4 check this with their own code. A bad row fails closed, the same way a
  malformed row does today.
- **The judge's audit decides the episode.** It reads the owner's words. No cryptography and no CI guard (owner's
  simplicity rule).

## Choices for the judge to check (reasoning only)

1. **Cite by the row's bold title**, not by a line number, which shifts as rows are added, nor by a hash. Titles are
   already unique in practice; a duplicate fails closed.
2. **"That episode" is left to the audit.** The code checks only "dated on or before the restart" and "not reused". A
   code rule for "after the brake fired" would need the episode's start date recomputed in two places. That extra
   machinery is what the simplicity rule asks us to avoid, and the judge reads every such row anyway.
3. **No migration.** No book has an `owner_overrides.csv` today.

## Questions for the owner

None.

## Addendum 1: judge 134 (FAIL on a29778d, 2 should-fix), both checked on the real file and accepted

| Item | My check on `docs/DESK_DECISIONS.md` (main) | Change to the text |
|---|---|---|
| SF1: which title is citable | True: 152 table rows; 17 have no bold span; "approved" is the first bold span of two rows | The title is the first `**...**` span of the Decision cell. A row without one is not citable; a repeated title is refused by "exactly once". Criterion 3 tests the counts on the committed file |
| SF2: book names | True: the owner writes "Book 1/2/3" (14 times) and never `book1_rules` and the like (0 times) | `BOOK_DISPLAY_NAMES` in `fno/constants.py`, matched as whole words. Criterion 2: "Book 1" lifts `book1_rules`, not `book2_hybrid` |
| Note: the form of a restart row | Agreed | Scope states the standard `**title** (owner: "...")` form |

Correction to addendum 1: "approved" is the title of **4** rows, not 2 (orchestrator, 15 Oct 2026). The story text
says 4, and the criterion-3 test checks it on the committed file.

## Addendum 2: the code (the text passed judge 134 addendum 1 at bbac3d4)

Branch `story/c5b-restart-decision`, with `main` merged in. Lane 1 (risk and the drawdown brake).

### Criteria, code and tests (strong evidence: each test run, and each criterion broken on purpose)

**Criterion 1: a valid restart lifts the brake.**
- C2:
  - `fno/risk/overrides.py:48-52` reads the `decision` column and calls `RestartDecisions.check`.
  - `fno/risk/decision_rows.py:52-75` holds the rules.
- C4, its own code with no `fno.risk` import:
  - `fno/checks/validity_account.py:129-141`.
  - `fno/checks/validity_decisions.py:33-47`.
- Tests:
  - `tests/risk/test_restart_decision.py:37` and `tests/checks/test_validity_restart.py:34`.
  - The brake lifted end to end in `tests/risk/test_books.py` and `tests/risk/test_c5_account.py`, planted with
    `owner_decision` in `tests/risk/builders.py`.

**Criterion 2: every bad restart fails closed with its reason.**
- Code: the same lines as criterion 1.
- C2 test: `test_restart_decision.py:58`, 10 cases, each matched to its reason.
- C4 test: `test_validity_restart.py:55`, the same 10 cases.
- One more C2 case in `test_books.py`: a row whose `decision` field is missing.

**Criterion 3: the committed decisions file parses.**
- Code: `read_decision_rows` at `decision_rows.py:33-45`, and C4's `decision_rows` at `validity_decisions.py:17-30`.
- Tests: `test_restart_decision.py:63` and `test_validity_restart.py:60`. Each compares every row of the committed file
  with its title, as counted a second way (split on `**`).

**Criterion 4: the judge's audit step.**
- Where: `docs/JUDGE.md`, section "Brake restarts (story C5b)".
- Check: the judge reads it.

The 10 refused cases in C2 and C4:
1. The `decision` cell is empty.
2. The title is not in the file.
3. The title appears twice.
4. The row has no `(owner: "`.
5. The row is for another book: "Book 1" lifts `book1_rules`, not `book2_hybrid`.
6. A row naming "Book 10" does not lift `book1_rules` (whole-word match).
7. The title is only the second bold span of its row.
8. The row is dated after the restart.
9. The same row is cited by two restarts of one book.
10. The restart is for a shadow book. See "Review agent", finding 1.

**The true counts for criterion 3.**
- On the committed file the parser finds 152 rows, 17 of them without a title. "approved" is the title of 4 rows.
- The test checks these as minimums (`>= 152`, `>= 17`, `>= 4`), plus a row-by-row match against an independent count.
- Why minimums and not exact numbers: the owner keeps adding rows (lane 3). An exact count would turn the suite red at
  every new decision.
- My judgment, not tested: the judge may want exact numbers. I disagree, for the reason above. It is a one-line change.

### Deliberate breaks (quality rule 4)

21 of 21 breaks were caught.
- Each break ran with `PYTHONDONTWRITEBYTECODE=1`, with `__pycache__` cleared, and the file was restored afterwards.
- Script: `breaks_c5b.py`, in the session scratchpad.
- Each break ran against the C2 tests (restart, books, C5 account: 58 tests) or the C4 tests (restart, caps, inputs:
  65 tests).

| Break | Failed tests |
|---|---|
| C2: no "cites no decision" check | 1 |
| C2: a title found twice accepted | 1 |
| C2: no owner-words check | 1 |
| C2: no book-name check | 2 |
| C2: book name matched without `\b` ("Book 10" passes as "Book 1") | 1 |
| C2: no date check | 1 |
| C2: a reused citation accepted | 1 |
| C2: the last bold span used instead of the first | 2 |
| C2: no shadow-book guard | 1 |
| C2: `row["decision"].strip()` without the `or ""` | 1 |
| C2: `RestartDecisions.check` not called | 11 |
| C4: an empty decision matches any row | 1 |
| C4: a title found twice accepted | 1 |
| C4: a reused citation accepted | 1 |
| C4: no owner-words check | 1 |
| C4: no book-name check | 2 |
| C4: book name matched without `\b` | 1 |
| C4: no date check | 1 |
| C4: the last bold span used | 2 |
| C4: no shadow-book guard | 1 |
| C4: the decision problem ignored | 10 |

The first run missed 4 breaks, and I fixed each:
- The "Book 10" case was missing in both C2 and C4. I added it.
- The second-bold-span case was missing in both. I added it.
- C4 had no parse test on the committed file. I added one.
- C4's `not title or` was dead code, because an empty title already matches no row. I removed it. The break now
  targets the `title and` filter, which is what actually refuses an empty cell.

### Review agent (quality rule 3)

An independent review agent read the diff for correctness and silent failures. It found no case where a bad restart is
accepted, or a valid one refused, on the real file. It found 4 issues, all of them "fails closed, but by crashing":

1. **Shadow books: real, fixed.** `load_risk_book` also reads shadow books (`shadow:<name>-v<n>`), which are not in
   `BOOK_DISPLAY_NAMES`. A restart row for one raised a `KeyError` instead of the module's own error. In C4 that
   `KeyError` escaped `except AccountProblem`.
   - Fix: both sides now refuse such a restart with their own error: "not named in the owner's decisions: no restart
     row can lift its brake".
   - Effect: a shadow book's brake can be lifted only by a later story.
   - Why: the story scope names only the three books, and a shadow book is a research forward test, never real money.
     Tests and breaks cover it.
   - **Question for the orchestrator:** should a shadow book's brake be restartable (for example cited by its full
     name), or stay as now?
2. **`docs/DESK_DECISIONS.md` missing: not fixed.** If the file were missing, C2 and C4 would raise
   `FileNotFoundError`. That still fails closed (the book trades nothing), but with a crash instead of a reason. The
   file is committed and is the owner's record, so its absence is not a realistic case (owner, "Keep the design
   simple"). Recorded under Known limits.
3. **A row without its `decision` field: real, fixed.** A data row shorter than the header crashed C2 with
   `AttributeError`. C4 already used `or ""`. C2 now does too: `overrides.py:49`, a test in `test_books.py`, and a
   break.
4. **C4 accepts reordered or extra columns that C2 refuses, and a bad date in C4 raises `ValueError`: not fixed.**
   This was already true before C5b (C5 / C2-era code), and both cases still fail closed. I did not widen this story.
   It is reported to the orchestrator for a follow-up.

What the agent confirmed:
- Both C2 and C4 check every restart row before dropping the rows dated after the decision day. That is the stricter
  order: a bad or reused citation on a future-dated row brakes the book today.
- Both parsers read the same 152 rows of the real file. The only lines skipped are the header and its rule. There are
  no escaped pipes and no other date formats today.
- The quote and book-name checks search the whole row, Detail cell included. So "not Book 1" in a Detail cell passes
  the form check. This is by design: the meaning is the judge's audit (criterion 4).

### Real output sample (quality rule 6)

How it was made:
- The committed code, run on planted files in a scratch folder. No journal and no live data were used.
- The account was opened with `open_account_writer(...).start(1 Oct 2026)`.
- C2 is `brake_restarts`. C4 is `LedgerAccounts.facts` at 20 Oct 2026, 15:00 IST.

```
valid
  C2: (datetime.date(2026, 10, 12),)
  C4: (datetime.date(2026, 10, 12),)
other book
  C2: refused: decision 'Restart Book 1' does not name Book 2
  C4: refused: owner_overrides.csv: restart on 2026-10-12: decision 'Restart Book 1' must quote the owner, name Book 2 and be dated on or before the restart
no owner words
  C2: refused: decision 'Restart Book 1' does not quote the owner
  C4: refused: owner_overrides.csv: restart on 2026-10-12: decision 'Restart Book 1' must quote the owner, name Book 1 and be dated on or before the restart
reused
  C2: refused: decision 'Restart Book 1' is cited by more than one restart of book1_rules
  C4: refused: owner_overrides.csv: restart on 2026-10-12: decision 'Restart Book 1' is not one uncited owner row (1 rows)
```

C4's reasons are coarser than C2's: they list the three requirements rather than the one that failed. This is on
purpose (my judgment, not tested): C4 is the independent second check, and the precise reason is C2's.

### Gates at the pushed SHA

Run on the merged tree (code commit df56b69 plus main at 252a91e):
- `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: 5468 passed.
- `ruff check fno tests tools`: clean.
- `ruff format --check`: 1015 files already formatted.
- `python tools/check_imports.py`: clean, 1053 files.
- Record scan: clean.
