# Response 211: R3 code, part A (build order A): claims (for the judge)

**Branch:** `story/r3-shadow-accounts` (from `main`). **Story text:** `docs/stories/R-factory.md`, R3 (judge 208
addendum 1 PASS). Owner's decision 2 A: account opening, own terms and the Test B path now; fills with E8 part 1b; B0's
registration after this merges. Lane 1.

| # | Claim | Evidence |
|---|---|---|
| 1 | Book 1's run opens each research version's shadow account before D2 reads its inputs (criterion 1). | `fno/books/book1.py` `decide` calls `open_shadows(shadow_on(day), day)` before `inputs.day`; `test_shadow_accounts_are_opened_before_d2_reads_its_inputs`. Mutation (call removed) fails it. |
| 2 | An account already opened is never reset. | Strong: the opener is the existing `start_shadow_books`. Under the account lock, `open_account_writer` pulls the account from Drive (E2c `files`) before `writer.start`, which opens only a never-started account (`tests/desk/test_shadow_books.py`: a second call opens nothing). `cmd_book1` passes its shared download into `build_book1`. |
| 3 | Each shadow is valued on its own terms; Book 1's terms never reach a shadow (criterion 2). | `opening_runs`, `opening_trades` and `recorded_terms` take `decider`; the shadow books get `recorded_terms(account, decider=Book 1)`; `test_each_account_takes_only_its_own_records_and_terms`. |
| 4 | Book 1's readers take no shadow record, and the isolation does not rest on the `shadow-` prefix (criterion 9, E5's readers). | `_chosen` keeps a record only if its `mode` matches the reader. Two tests: same-day with and without a shadow; and a wrong-mode record with a matching id. Mutation (mode check removed) fails the second. |
| 5 | Test B's R3 input points at the shadow accounts (criterion 7). | `fno/budget/stop_rule_tracker.py` `SHADOW_ACCOUNTS = journal/shadow`; zero shadows still give "undecided" (`fno/forecast_v4/stop_rule.py`, unchanged). |
| 6 | Nothing fills a shadow yet (criterion 6). | No fill code added; shadow orders and fills are E8 part 1b's. |
| 7 | E6, S2 and S3's Book 1 views are unchanged (criterion 9, the rest). | Some evidence: E6's Book 1 section and S2's board read Book 1's own account, which R3 does not write. S3's code is not built yet. Its future Book 1 actions must read decision records through the same mode rule. |

**Gates:** `pytest -q -n auto` 6,792 passed; `ruff check`, `ruff format --check`, `check_imports` and `check_records` are
clean.

**Known limit:** on a fresh checkout, `journal/shadow/` holds no committed files: accounts are kept in Drive (E2c). So
Test B's `exists()` is true only after a run has opened or downloaded a shadow.
