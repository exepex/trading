# Response 110: story E1b, capital top-up to the Rs 20 lakh account (story text for the judge's check before code)

Builder: Claude, 15 Oct 2026. Branch `story/e1-topup` from `origin/main` (5a86aad). Story text:
`docs/stories/E-paper-desk.md` section E1b. Lane 1 (money: E1's ledger, C2, C4). Per quality rule 1 this push holds
the story text only; code starts after the judge's check passes.

## What the story does, in short

- **A new ledger entry kind, `capital_top_up`:** a dated row appended once per book. It brings the book to the books'
  `paper_account_rs` (Rs 20 lakh, a Rs 15 lakh top-up for each committed book); the 13 Oct opening rows are untouched.
- **Capital is the opening plus top-ups dated on or before a day.** Every reader of the old "starting cash" moves to
  capital: E1, C2 (risk view, `paper_account`), C4 (its own ledger read), P10 (Home's profit and loss) and S2's
  reconciliation.
- **The brake measures drawdown of profit and loss only.** The capital is constant across the closed-equity series, so
  a top-up never makes a new high and never lifts a braked book.
- **A command, `python -m fno account top-up`, computes the amount** and refuses a book at size, above it, not started,
  or with an open position. The orchestrator or owner runs it once after the PASS and the merge; I never run it on the
  real journal.

## Choices the judge should check (my reasoning, labelled)

1. **Capital is constant across the brake's series (shift, not step).** A step on the top-up day would make the top-up
   a new high: wrong per judge 105 minor 4. A constant shift keeps the drawdown identical to profit and loss. Reasoning
   only, tested in criterion 4.
2. **A top-up is refused while the book has open positions.** The day's equity row is written from the unmarked state,
   which is exact only for a flat book. All three books are flat today (no fill ever made), so this costs nothing now.
   Reasoning only.
3. **The amount is computed (size − capital), never typed.** This removes the chance of a mistyped Rs 1,50,000. If the
   books' size changes later, a new top-up brings the book to the new size; a decrease is refused (out of scope).
4. **The entry is idempotent by its day (`top_up_<date>`) and by "already at size".**
5. **`starting_cash` is renamed `capital`** in E1's state and every reader, because the name would otherwise lie
   (CLAUDE.md: names say what things do). This touches C2, C4 (own read), P10 and S2 code; all are in the gap list.

## Depends and blocked

- The code needs C5's `paper_account` rule and the books profile (`story/c5-risk-buckets`, judge C re-checking
  b929743). I will build on main once C5 is merged, or on C5's branch if the orchestrator prefers.
- Running the command on the real journal is not mine to do: lane 1 data, after the merge.

## Questions for the owner

None new. The per-book reading of the brake is the orchestrator's decision, owner to confirm, as in C5.

## Addendum 1: judge 110 (FAIL on d309de6, 1 should-fix, 3 minor), each checked

| Item | My check | Change to the story text |
|---|---|---|
| SF1: a top-up dated by day counts for the whole day | True. C4's `_filled_by` (`fno/checks/validity_account.py`) counts a row without a time zone for the whole cutoff date, so a 17:00 top-up would pass a replay of that day's 15:00 decision that was refused live | The row's `filled_at` is the write instant (IST, offset included). Capital = the opening plus top-ups written at or before the decision cutoff, in E1, C2 (the day at `DESK_DECISION_TIME`) and C4 (its cutoff). P10 stays end of day. Criteria 1, 3 and 5 test 17:00 against 15:00 on T and T + 1, and 10:00 on T. I chose the timestamp rule alone, not a time-window refusal: one rule, no second mechanism (reasoning only) |
| Minor 1: amount restores capital, not equity | Agreed | Scope and criterion 1 say so, with the Rs 10,000-loss example |
| Minor 2: target source; a second top-up | Agreed | Scope names `risk.profiles.books.paper_account_rs`; raising it is a lane-1 config change and an owner decision; criterion 8's output line names "a further top-up" |
| Minor 3: C4 parses a top-up between fills as a fill | True: `account_facts` runs `_trades(rows[1:])` over every row after the opening | C4 design line: trades only from fill and settlement rows; criterion 5 tests a top-up row between two fills |

**One disagreement, stated:** judge 110's project-rules section says the real-journal run is "never by the builder".
The orchestrator's later instruction, citing the owner's rule of 15 Oct 2026 ("1 B": builders run their own
commands), is that I run it after the merge and record its output. The story text follows the owner's rule and says
so.


## Addendum 2: the code (story text PASS at 9e426e8; C5 merged at a8379e6)

Built on `story/e1-topup` with `main` merged in (C5 included). Lane 1.

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | One `capital_top_up` row at its write instant (IST, offset kept); amount = size − capital (restores capital, not equity); earlier rows byte-for-byte | `fno/books/account.py` (`AccountWriter.top_up`, `TopUp`), `fno/books/fills.py` (`top_up_row`, `CAPITAL_KINDS`), `fno/constants.py` (`LEDGER_TOP_UP`) | `tests/books/test_top_up.py::test_a_top_up_appends_one_row_at_its_write_instant_and_changes_nothing_before`, `test_the_amount_restores_capital_not_equity` | strong evidence |
| 2 | Refused with a reason and nothing written: above size, open position, not started, no lock; at size: unchanged | `AccountWriter.top_up` | `test_a_top_up_is_refused_with_its_reason_and_nothing_written`, `test_a_book_at_size_is_left_unchanged_and_a_not_started_book_is_refused`, `test_a_top_up_needs_this_books_lock` | strong evidence |
| 3 | Capital = the opening plus top-ups written at or before an instant (17:00 on T: not at T 15:00, yes at T+1 15:00; 10:00 on T: yes); never a fill, trade, position or C1 line; the day's equity row written | `PaperAccount.capital(at)`, `PaperAccount.state(..., at)`, `AccountState.capital` (renamed from `starting_cash`, `fno/books/equity.py`) | `test_capital_counts_a_top_up_only_from_its_write_instant` (3 cases), `test_a_top_up_is_never_a_fill_a_trade_or_a_c1_ledger_line` | strong evidence |
| 4 | C2: `paper_account` follows capital at the decision cutoff (15:00 IST); the brake never lifts or moves (constant capital, profit-and-loss drawdown); boundary just under and over Rs 1,20,000 after a top-up; no higher high from a top-up | `fno/risk/book_view.py` (cutoff = day at `DESK_DECISION_TIME`, moved to `fno/constants.py`), `fno/risk/caps.py` | `tests/risk/test_top_up_brake.py` (6 tests) | strong evidence |
| 5 | C4's own read agrees with C2 on capital, cash and the series at the cutoff; a 17:00 top-up does not count at T 15:00; a top-up between fills is capital, never a fill | `fno/checks/validity_account.py` (`TRADE_KINDS`, `CAPITAL_KINDS`, C4's own), `fno/checks/validity_caps.py` (`paper_account_check` on capital) | `tests/checks/test_validity_top_up.py` (3 tests); C4's independence test passes | strong evidence |
| 6 | Home: pnl 0 against Rs 5 lakh before the top-up, 0 against Rs 20 lakh on and after, never −Rs 15 lakh | `fno/market_read_models/home_inputs.py` (capital at the end of each day) | `tests/market_read_models/test_home_blocks.py::test_a_top_up_is_capital_never_profit_on_home` | strong evidence |
| 7 | S2 reconciliation holds with a top-up in the ledger | `fno/scoreboard/reconcile.py` | `tests/scoreboard/test_reconcile_top_up.py` | strong evidence |
| 8 | Command: one line per book (topped up / already at size / refused: reason / "a further top-up"); non-zero exit if any refused | `fno/books/cli.py` (`top_up_books`), target `fno/composition.py` (`paper_account_rs`) | `test_the_command_tops_up_each_book_once_and_names_a_further_top_up`, `test_the_command_reports_a_refused_book_and_exits_non_zero` | strong evidence |
| 9 | Never edits an earlier row; never touches another book | append only (`_append_ledger_row`) | `test_a_top_up_appends_one_row...` (prefix bytes), `test_a_top_up_never_touches_another_books_files` | strong evidence |

**Gates:**
- full suite 5,142 passed (7m55s, `FNO_SLACK_BOT_TOKEN` unset);
- `ruff check fno tests tools` clean; `ruff format --check` 942 files;
- `python tools/check_imports.py` clean (980);
- record scan clean; no `--no-verify`.

**Each criterion broken on purpose** (`PYTHONDONTWRITEBYTECODE=1`, each file restored; script in my scratchpad):
19 of 19 caught.

| Criterion broken | File | Test run | Result |
|---|---|---|---|
| 1 amount = target - capital | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed in 0.14s |
| 1 write instant kept | `fno/books/fills.py` | `test_top_up.py` | caught: 1 failed in 0.14s |
| 1 restores capital, not equity | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 1 passed in 5.96s |
| 2 refused above size | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 2 passed in 0.21s |
| 2 refused with an open position | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 3 passed in 0.27s |
| 2 at size: nothing written | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 4 passed in 0.27s |
| 2 lock required | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed in 0.13s |
| 3 capital counts only from the instant | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 6 passed in 0.31s |
| 3 the day's equity row | `fno/books/account.py` | `test_top_up.py` | caught: 1 failed, 9 passed in 0.43s |
| 4 C2 capital at the decision cutoff | `fno/risk/book_view.py` | `test_top_up_brake.py` | caught: 1 failed in 0.17s |
| 4 brake series constant capital | `fno/risk/book_view.py` | `test_top_up_brake.py` | caught: 1 failed, 1 passed in 0.20s |
| 4 paper_account reads capital | `fno/risk/caps.py` | `test_top_up_brake.py` | caught: 1 failed in 0.18s |
| 5 C4 counts top-ups by its cutoff | `fno/checks/validity_account.py` | `test_validity_top_up.py` | caught: 1 failed in 0.15s |
| 5 C4 top-up never a fill | `fno/checks/validity_account.py` | `test_validity_top_up.py` | caught: 1 failed, 1 passed in 0.22s |
| 5 C4 capital includes top-ups | `fno/checks/validity_account.py` | `test_validity_top_up.py` | caught: 1 failed, 1 passed in 0.18s |
| 6 Home capital that day | `fno/market_read_models/home_inputs.py` | `test_home_blocks.py` | caught: 1 failed, 7 passed in 3.01s |
| 7 S2 cash against capital | `fno/scoreboard/reconcile.py` | `test_reconcile_top_up.py` | caught: 1 failed in 0.29s |
| 8 further top-up named | `fno/books/cli.py` | `test_top_up.py` | caught: 1 failed, 10 passed in 1.02s |
| 8 refused exits non-zero | `fno/books/cli.py` | `test_top_up.py` | caught: 1 failed, 11 passed in 1.09s |

**Known limits (said plainly; one line each, per the owner's simplicity rule):**
- C2 reads every fill in the ledger, not only those by the cutoff (unchanged C2 behaviour). Capital is now by
  cutoff; D3's replays use the stored book, not the ledger.
- `positions.json` now names the figure `capital_rs`, not `starting_cash_rs`. The three committed files change
  that key when the top-up rebuilds them: one of the three files the run may write.
- The run window (outside 14:50-15:30 IST) is a run condition, not enforced by code.

**The run on the real journal** happens after the PASS and the merge, by me, under the story's three conditions, with
the output and the commit recorded here.
