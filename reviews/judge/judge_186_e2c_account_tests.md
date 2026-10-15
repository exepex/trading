# Judge 186: "not weakened" check of `fix/e2c-account-tests` 75103ee4 (tests only)

Judge B. The E2c builder, asked by the orchestrator. The commit fixes the 2 tests that E2c's merge step `d9f67c4`
(`git rm --cached` of the account folders) broke on `main` (judge 177 addendum 4). It is one commit on `f78c775` and
changes 2 test files; no code changes.

## 1. `tests/books/test_paper_account.py`
- **Before:** the test read each book's committed ledger (opening Rs 5 lakh, top-up Rs 15 lakh on 15 Oct),
  `positions.json` and equity history from `journal/<book>/account/`. That folder is no longer committed, by the
  owner's E2c decision.
- **Now:** it asserts each book's committed `daily_totals.csv` exactly: the header, `2026-10-13,500000.00,0,0,0` and
  `2026-10-15,2000000.00,0,0,0`. It also asserts that closed equity equals `paper_account_rs()`. I checked: the file on
  `main` holds exactly these lines.
- **Ruling: not weakened beyond what the move requires.** The facts the old test proved still hold in the public
  record: the Rs 5 lakh opening on 13 Oct, Rs 20 lakh after 15 Oct, no trade and no fill. The row kinds,
  `positions.json` and the marked-equity column now exist only in Drive, which tests never touch.
- **Optional, not required:** to keep the old row-level check, a history test could rebuild `daily_totals` from
  `git show d9f67c4^:journal/<book>/account/cash_ledger.csv` and compare. It would check a fixed past commit, which
  adds little. I do not ask for it under the simplicity rule.

## 2. `tests/market_read_models/test_home_blocks.py`
- **Now:** three accounts are started in a seed folder, moved to a `LocalIndexStore` Drive with `move_accounts`, and
  downloaded into a separate checkout with `download`. The real `build_session_rows_builder(...).home.on(DAY)` then
  runs, with `market_wiring.ROOT` pointed at that checkout.
- **Every old assertion is kept:** limit 150,000, the book names, `approved == []`, and "started", now on the
  checkout. One is added: each book's value equals `paper_account_rs()`.
- **Not vacuous (checked).** Patching `ROOT` changes only `BooksReader(ROOT, ...)` in that builder. The approvals'
  `LATEST_FROZEN_EXPERIMENT` and the other module paths are bound at import to the real repository, so
  `approved == []` still reads the real frozen experiment. If the download is skipped, the checkout is empty and
  "started" fails, so the test depends on the download path.
- **Ruling: not weakened; stronger.** It now runs the E2c path (move, download, read) through the live wiring.

## Gates
Both files: 22 passed. The builder reports 6,120 passed and 1 failed in a fresh full-history clone with no account
files on disk. The remaining failure is G7's V6a count test (judge 177 addendum 4c), the orchestrator's to fix.

**Verdict: PASS for 75103ee4 (not weakened).** Merge it.
