# Judge 210: R3 code, part A: shadow accounts, own terms, isolation, Test B path (judge G)

- **Judged:** `story/r3-shadow-accounts` at `872f7f21` (code `84e4d230`; tests and claims added on top; builder
  session 0145TfSwzmpk6MBrH92f5h4G; claims `response_211_r3-code-part-a.md`).
- **Text:** judge 208 addendum 1 PASS; the owner chose build order A. Lane 1. 210 was the next free number on main.
- **Verdict: FAIL.** The code is correct, but three of its fixes are untested where they actually take effect: in the
  composition root and the tracker. My mutations there survive. One should-fix and 2 notes.

## What I checked

- **Gates:** ruff check, ruff format and `check_imports` are clean. Full suite with `-n auto`: **6,793 passed, 0 failed**.
- **The two old tests changed their call shape only.**
  - `tests/book1/test_commit_failure.py`: `lambda cfg` became `lambda cfg, files=None`.
  - `tests/desk/test_shadow_books.py`: `{}` became `lambda account: {}`, four times.
  - The assertions are identical, so no test is weakened.
- **Code read:**
  - `Book1.decide` opens `shadow_on(day)` versions before `inputs.day(day)`, which closes judge 208's crash path.
  - The opener is `start_shadow_books` with E2c's `files` from `cmd_book1`'s shared download.
  - `_chosen` keeps a record only when `(mode == shadow) == reader is a shadow`.
  - `opening_runs`, `opening_trades` and `recorded_terms` take `decider`.
  - `_parts` gives each shadow `recorded_terms(root, account, BOOK1_RULES)`.
  - Test B's R3 input points at `journal/shadow`.
  - E5b's one-decision rule (`decided_runs.py`) only finds runs, so a shadow record in the same run changes nothing.
  - Only `build_book1` constructs `Book1` in production, so the opener is always passed there.

## My mutations (each alone, then reverted)

I ran `tests/book1 tests/desk tests/budget tests/scoreboard tests/decisions`, deselecting one test that needs `.git`
in my copy.

**Caught:**

- the open call removed;
- shadows opened after the inputs are read;
- the mode check made shadow-only, so Book 1 would take shadow records again. The wrong-mode test catches this.

**Survived (finding 1):**

- in `_parts`, shadows given Book 1's terms (`shadow_terms = lambda account: terms`);
- in `build_book1`, the opener not passed, so production falls back to the default no-op `lambda strategies, day: []`;
- Test B's path dropped (`StopRuleInput(..., "R3")` without `SHADOW_ACCOUNTS`).

## Findings

### Should fix

1. **Three of the fixes are tested only below the place they take effect.**
   - `test_each_account_takes_only_its_own_records_and_terms` tests `recorded_terms(..., decider)`, but not that
     `_parts` passes it to the shadow books (criterion 2).
   - The order test replaces `decider.open_shadows` by hand, so nothing checks that `build_book1` wires
     `start_shadow_books` (criterion 1).
   - Nothing checks the tracker's R3 path (criterion 7).

   Each mutation brings back the defect R3 exists to fix:
   - the crash on the first registration (opener not wired);
   - the crash once a shadow holds a trade (Book 1's terms, `RiskInputError` at `book_view.py:37-39`);
   - Test B reading nothing.

   That happens on the real path in normal running. **Fix:** three small tests:
   - `_parts(root, market)` gives a shadow book holding only its own trade's terms, with one Book 1 trade and one
     shadow trade on disk;
   - `build_book1(cfg, root)` opens a registered research version's account on `decide` (no Drive: `files=None`);
   - the tracker's R3 input path is `journal/shadow`.

### Notes

1. **Criterion 9 for E6 and S2:** this rests on code reading, and is right for part A. Both read only
   `journal/book1_rules/account/`, which R3 never writes, and nothing fills a shadow yet. The with-and-without tests
   for E6's Book 1 section and S2's Book 1 board belong with part B (E8's fills), when a shadow fill first exists.
2. The S3 isolation test passes partly by construction: a shadow candidate is not in the common set, so
   `MatchedDays` never looks it up. It is still a useful guard.
