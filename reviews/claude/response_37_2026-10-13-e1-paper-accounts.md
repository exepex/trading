# Response 37: builder's claims for story E1 (paper accounts per book, single-writer lock)

Story: `docs/stories/E-paper-desk.md#e1-paper-accounts-per-book-with-a-single-writer-lock`. Status: built 13 Oct 2026,
awaiting the judge (`docs/JUDGE.md`). Depends on C1 (built, awaiting judge), whose `Order`, `Trade` and `trade_line`
are used unchanged.

## What was built

| File | What it does |
|---|---|
| `fno/books/paths.py` | Book names checked against `fno.constants.BOOKS`; every account file must sit directly inside `journal/<book>/account/` (criterion 6) |
| `fno/books/lock.py` | `AccountLock(root, book)`: non-blocking `flock` on `journal/<book>/account/.lock` plus a lease (holder host, PID, process start time; start; expiry) |
| `fno/books/fills.py` | `Fill`: wraps C1's `Order`; charges from `fno.costs` on the fill price (`Fill.priced`); its cash-ledger row |
| `fno/books/equity.py` | Positions per trade and the three measures (closed equity, marked equity, available cash), defined once for C2 to reuse |
| `fno/books/account.py` | `PaperAccount` (read) and `AccountWriter` (write, lock checked on every write): `start`, `apply_fill`, `record_equity`, crash recovery |
| `fno/books/cli.py` | `python -m fno account init` (once; never resets) and `python -m fno account show <book>` |
| `fno/composition.py` | `open_account_writer(book)`: the one way to write (takes the lock, yields the writer); `build_paper_account(book)` |
| `fno/constants.py` | `BOOK1_RULES`, `BOOK2_HYBRID`, `BOOK3_AI`, `BOOKS`, `JOURNAL_FOLDER`, `LEDGER_OPENING`, `LEDGER_FILL` |
| `journal/<book>/account/` | Starting state of the three books, committed once (criterion 1) |

Book identifiers: the epic text already names them (`book1_rules`, `book2_hybrid`, `book3_ai`, top of
`docs/stories/E-paper-desk.md`); they are now constants in `fno/constants.py:22-25`.

**Files per account:** `cash_ledger.csv` (append-only; one row per fill plus the opening balance; the source of
truth), `positions.json` (a view rebuilt from the ledger after every write), `equity_history.csv` (one row per day;
a repeated day replaces its row). `.lock` and `*.tmp` are git-ignored.

**Definitions (from C2's text, implemented in `fno/books/equity.py:78-110`):** closed equity = Rs 5 lakh + net P&L of
closed trades; marked equity = closed equity + open trades at their marks (= cash + marked value of open positions;
tested); available cash = min(cash, marked equity) - margin blocked - premium reserved (orchestrator decision
13 Oct 2026 on doubt 2 below; `fno/books/equity.py:75`). A missing mark raises `MissingMark`;
stale marks are listed in the state.

## Acceptance criteria

| # | Criterion | Code | Test | Result |
|---|---|---|---|---|
| 1 | Each book starts at Rs 5,00,000 with no positions; starting state committed once | `fno/books/account.py:137` (`start`: refuses if the ledger exists), `STARTING_CASH_RS` at `:33`; `journal/{book1_rules,book2_hybrid,book3_ai}/account/` | `test_paper_account.py::test_the_committed_starting_state_is_rs_5_lakh_and_no_positions_for_each_book` (reads the committed files), `::test_starting_twice_changes_nothing` (byte-identical) | PASS |
| 2 | Two processes, same book, same moment: exactly one gets the lock, the other exits without writing | `fno/books/lock.py:125-127` (`LOCK_EX \| LOCK_NB` -> `AccountBusy`); CLI exit code 3 (`fno/books/cli.py`) | `test_account_processes.py::test_two_writers_on_one_book_exactly_one_writes`: two `python` processes start at the same instant, each holds 2 s; exit codes `[0, 3]`, one fill in the ledger | PASS |
| 3 | Two books at the same moment both succeed | separate lock file per book (`lock.py`, path from `paths.account_folder`) | `::test_two_books_written_at_the_same_moment_both_succeed`: exit codes `[0, 0]`, each book has its own fill | PASS |
| 4 | Crashed holder's lock released when its lease expires and holder is gone; never while holder alive | `fno/books/lock.py:151-168` (`_check_previous_lease`), `:83` (`holder_alive`: PID plus `/proc` start time, so a reused PID is not the holder) | `::test_a_crashed_holders_lock_is_freed_only_after_its_lease_expires` (process SIGKILLed while holding: busy before expiry, taken over after); `::test_a_live_holder_keeps_its_lock_after_its_lease_expires` (lease 0.5 s, holder alive 4 s: busy); `::test_a_lease_naming_a_live_process_is_never_taken_over_even_when_expired` (lease rule alone, no flock: refused while the named process runs, taken over once killed) | PASS |
| 5 | Restart after an interrupted write neither loses nor repeats a fill (idempotent by fill ID; test kills the writer mid-way) | `account.py:149` (`apply_fill`: same fill ID + same content -> skipped; same ID, other content -> error), `:185` (`_recover`: drops a half-written last line, rebuilds the view), `:196` (one appended line, `fsync`ed before the view) | `::test_a_restart_after_a_crash_mid_write_neither_loses_nor_repeats_a_fill[before_view]` and `[half_line]`: the writer is SIGKILLed after the 2nd fill's ledger line / halfway through it; the retried run gives fills f-1, f-2, f-3 exactly once, no half line, view equals ledger | PASS |
| 6 | No code path lets one book read or write another's account files | `fno/books/paths.py:17-38` (unknown book refused; names with separators or `..` refused; resolved path must stay inside; account folder linked to another book refused); `account.py:178` (writer needs a held lock for the same book and folder) | `test_paper_account.py::test_an_account_never_reaches_another_books_files`, `::test_an_account_folder_linked_to_another_book_is_refused`, `::test_writes_need_this_books_lock_held` | PASS |

Extra tests: `::test_the_three_measures_by_hand` (a two-leg spread valued by hand, available cash, stale and missing
marks), `::test_a_closed_trade_matches_the_cost_accountants_trade_net` (a closed trade's account P&L equals C1's
`trade_line(...).net`, so the account and the three ledgers agree; a new fill on a closed trade is refused),
`::test_a_repeated_fill_id_is_skipped_and_a_reused_one_refused`, `::test_the_equity_history_keeps_one_row_per_day`,
`::test_bad_fills_are_refused`, and for available cash `::test_available_cash_never_counts_a_bought_premium_as_spendable`,
`::test_available_cash_never_counts_a_short_options_open_loss_as_spendable`, `::test_available_cash_of_a_flat_account_is_its_cash`.

## Command output (13 Oct 2026)

```
$ python -m pytest -q
191 passed in 22.70s
$ ruff check fno tests tools
All checks passed!
$ python tools/check_imports.py
clean: 80 files, 1 archival skipped
$ python -m pytest tests/books -v      (20 tests)
test_account_processes.py: 7 passed (criteria 2, 3, 4, 5); test_paper_account.py: 13 passed (criteria 1, 6, definitions)
$ python -m fno account init
book1_rules: started / book2_hybrid: started / book3_ai: started      (first run)
book1_rules: already started; unchanged ...                           (second run, exit 0)
```

Largest files: `fno/books/account.py` 211 lines, `fno/books/lock.py` 180; none over 350.

## Doubts and limits (stated, not hidden)

1. **An OS lock protects one machine only** (strong evidence: `flock` is held by one kernel). Cloud routines run in
   separate containers with separate checkouts; there the lock file is not shared (it is git-ignored). Between
   containers the guards are git (a push from a stale checkout is rejected; the routine must pull, re-run and retry)
   and fill-ID idempotency. E3/O1 should state "pull, write under the lock, commit, push; on rejection pull and retry
   with the same fill IDs". Reasoning only for the routine design; it belongs to E3/O1, not E1.
2. **C2's first "available cash" counted a bought option's premium as spendable twice** (strong evidence,
   arithmetic): buying 65 units at Rs 100 lowers cash by Rs 6,500 plus charges while marked equity barely moves; and a
   short option's open loss lowers marked equity but not cash. **Resolved 13 Oct 2026 (orchestrator decision):**
   available cash = min(cash, marked equity) - margin blocked - premium reserved, implemented and tested (three tests
   above). The orchestrator updates C2's story text and the decision record.
3. **Crash recovery waits for the lease** (default 600 s) even on the same host, where the dead `flock` already proves
   the holder gone. This follows the criterion's wording ("released when its lease expires and its holder is gone").
   600 s is a choice (reasoning only), accepted by the orchestrator; it is the named constant
   `DEFAULT_LEASE_SECONDS` in `fno/books/lock.py` (and a parameter of `open_account_writer`), not a magic number.
4. A lease holder on another host cannot be checked: it counts as alive until its lease expires. A lease that cannot
   be read (crash while writing it) counts as held until the default lease has passed since the file was written.
5. Linux and macOS only (`fcntl`); fine for cloud routines, not for Windows.
6. Design 12.6 has two stale references: "story E1 criterion 9" (E1 has six criteria) and "fill model (E1)" (the fill
   model is E4). Not edited here (not this story's file); the orchestrator fixes them.
7. Money safety: no order function; no price is ever invented (missing mark raises); a reused fill ID with different
   content raises rather than being skipped; a closed trade cannot be reopened under the same ID.
