# Response 246: story E2d, per-trade daily marks (story text, claims for judge B)

Branch `story/e2d-trade-marks`. Builder 0134MoC6 (E2c's owner). The text is at the end of
`docs/stories/E-paper-desk.md` (section E2d), with the register row E2d.

## The gap (checked on `main`, 16 Oct 2026)

- `AccountWriter.record_equity` (`fno/books/account.py:203`) is called only by `tests/books/test_paper_account.py`.
- The desk's marks live only in memory during the exit review (`fno/desk/exits.py`).
- `journal/<book>/daily_totals.csv` holds closed equity and counts only.

So from the first open paper trade, nothing records an open trade's value. The P2 page `paper_trades` cannot publish
`open[].mark_value` or `unrealised`, or `accounts[].value`. Found by the P2 builder and the screens lead, and routed
by R2/G7. E2c moved `equity_history.csv` to Drive (its text says the file "would leak the same way once anything
calls it"), but no story wired the daily call. The gap is in E2c's own function, "marks, equity history". Scoreboard B
is not affected: it re-marks from the execution snapshots at score time (`fno/scoreboard/daily_values.py`).

## Claims (what the text commits to)

1. One source: the run's own 15:15 execution snapshot, the same one fills and exits use. No later quote, and no
   re-dating on a rerun.
2. No invented price. A contract without a valid quote takes its last valid mark, flagged stale (E1's `Mark`). With
   no earlier mark it is unmarked: that book writes no equity row that session, the trade's rows say unmarked, and one
   #fno-desk alert names book, trade and contract.
3. Private:
   - `trade_marks.csv` and the equity row go to Drive with the account (`ACCOUNT_FILES`);
   - `daily_totals.csv` is unchanged (no contract, price or mark);
   - a by-path refusal in the record scan for every account file closes the `git add -f` hole I found while writing.
     Today only `.gitignore` keeps account files out; `forbidden_files.py` refuses raw Groww quotes but no account
     file.
4. Idempotent per session, and one book's failure never stops another's (the exit review's per-book rule).
5. Shadow accounts are marked in their own files.

## Open, honest

- A stale mark carries forward without limit while a contract stays unquotable. The flag says so on every row and in
  `stale_marks`, but the text sets no maximum age. Reasoning only: a maximum is an owner number, so I did not invent
  one. If the judge or owner wants one, it is a config value.
- The P2c page is not built here; E2d gives it the rows to read.

## Addendum 1: R2/G7's review (all four points checked in code and accepted)

1. **One marking rule.** Accepted. S2's `fno/scoreboard/daily_values.py` (`trade_days`) already applies the same
   rule: the snapshot's mid; else the last valid mark, flagged stale; a leg never marked leaves the day unvalued. A
   second copy would let the page and scoreboard B disagree the day one changes. E2d therefore adds one shared marking
   function in `fno/books/marking.py` (E1's `Mark` lives in `fno/books`), and E2d calls it. R2/G7 moves
   `daily_values` onto it (it is theirs and hashed by S1). A test checks that E2d's value for a trade equals S2's
   `TradeDay.value` on the same fixture.
2. **A leg past its expiry.** Accepted. Between a contract's expiry and the publication of its final settlement price,
   no quote exists. The leg keeps its last valid mark with source `awaiting_settlement` (not `stale`), as S3's standard
   unit treats it (`past_expiry`), and the page shows "awaiting settlement". E7 settles it at the final settlement
   price at the next daily run after publication (`fno/desk/settlement.py`). A never-marked leg past expiry stays
   unmarked.
3. **The gap of an unmarked day.** Accepted, with one part pushed back. The brake reads closed equity
   (`fno/risk/book_view.py:24`), so an unmarked day never moves it; the text now says so. The gap is explicit, not
   silent: the session's `trade_marks.csv` rows say `unmarked`, naming the contract, and the page shows "not valued on
   <date>". I did not add a note column to the next day's equity row. The unmarked rows already record the day and the
   reason, `daily_values` already carries an unvalued day's change to the next valued day without interpolating, and a
   new column in `EQUITY_COLUMNS` would change every reader for no new information.
4. **Size and DRY.** Accepted: criterion 1 compares against S2's `TradeDay.value` for the same fixture, not a hand
   formula.

## Addendum 2: judge 250 and its addendum 1 (accepted; the design now has one rule and one history)

Judge B is right, and addendum 1's shared `marking.py` did not go far enough. One function fed two histories still
disagrees. The judge's example: D1 marked at 100; D2's marking step lost while D2's snapshot is valid at 110; D3 has
no quote. Taking the fallback from `trade_marks.csv`, E2d would mark D3 at 100, while S2 marks it at 110.

The rewritten text:
- **Imports S2's code unchanged:** `trade_days`, `key_of` and `DayMarks` from `daily_values.py`, and `SnapshotMarks`
  from `sources.py`. The fallback therefore comes from the trade's earlier execution snapshots, the same history
  scoreboard B reads. No `marking.py`, no edit to an S1-hashed file, and no S1 frozen-files change are needed (this
  replaces addendum 1's point 1 and R2/G7's frozen-files follow-up).
- **Stores per trade, not per contract:** status, value, mark value and stale contracts. A per-contract mark would need
  a second walk of the history. `trade_marks.csv` is an output only; nothing reads it back to value a trade.
- **One valuation path:** the equity row is written from the same values (marked equity = closed equity + the open
  trades' values), through a new `record_marked_equity`. The unused `record_equity(day, marks)` is removed with its
  tests.
- **Criterion 1** checks every session of a multi-session fixture, a lost marking day included, against S2's
  `trade_days`.
- **Criterion 12:** the S1-hashed files are unchanged.
- **The judge's notes:**
  - the account-folder refusal is a new wildcard matcher class, because `ForbiddenFiles` matches one fixed prefix;
  - a same-day top-up equity row is replaced, never doubled (criterion 5);
  - no age limit on a stale mark (S2 has none; a limit belongs in S2's rule, through S1).

## Addendum 3: the code (branch `story/e2d-code`)

The story text is merged (8908ba3c). The code follows it, with two changes, each said here, and judge B's and R2/G7's
notes.

**What was built:**
- **`fno/desk/trade_marking.py`** (new).
  - `mark_trade` calls S2's `trade_days` unchanged and takes the last session as the day's value. Its status is
    `valued`, `unmarked` or `awaiting_settlement`, a label on a stale leg past its expiry, with S2's value.
  - `TradeMarker` handles one account: its rows plus the equity row, or no equity row if a trade is unmarked.
  - `MarkingStep` is the run's step. It goes account by account, and a failure is alerted while the other accounts
    go on.
  - `marked_accounts` lists the run's books plus every started shadow account.
- **`fno/books/trade_marks.py`** (new): `trade_marks.csv`, its columns and its idempotent writer. A rerun replaces the
  session's rows; it checks the lock.
- **`fno/books/account.py`**: `record_marked_equity(day, open_trades_value, stale)`.
  - The parameter is named apart from `equity.py`'s `open_value` (judge B). Its docstring says why: passing legs-only
    would count the cash flow twice. Criterion 2's test checks that the row is not closed equity plus the legs alone.
  - `record_equity` and its per-contract `marks` path are removed, and their two tests are rewritten on the new method.
- **`fno/desk/daily_run.py`**: step 8, `trade_marks`, comes after `exits`. A commit stopped at it does not say "exits
  not reviewed" (`AFTER_EXITS`).
- **`fno/desk/daily_wiring.py`**: `build_trade_marker` is the only place that builds S2's `SnapshotMarks` (R2/G7). It
  reads the committed run logs' valid snapshot IDs when the step runs.
- **`fno/desk/private_files.py`**: `trade_marks.csv` is in `ACCOUNT_FILES`, before the events.
- **`fno/record_scan/forbidden_files.py`**: `ForbiddenFolders`, with `PAPER_ACCOUNT_FILES` for `journal/*/account/`
  and `journal/shadow/*/account/`. It is wired in `fno/composition.py` beside the raw Groww rule.

**Two changes from the text, both checked in code:**
1. **The marks do not go through `AccountSync.write`.** That call also commits the account's public
   `daily_totals.csv`. Shadow accounts have never had one: E2c writes them for the three books only, and nothing
   wrote a shadow account in the daily run before. So marking through it would have published a new file per shadow
   account. The step instead opens the same locked, Drive-pulled and Drive-pushed journal (`open_desk_journal` with
   the run's `PrivateFiles`, the function `DriveAccountSync` wraps) and commits nothing. Marking changes no ledger
   row, so criterion 7 holds by construction. A test checks that a shadow account gets no public file.
2. **The step is named `trade_marks`, not `marks`.** O8's health check already reports A16's 15-minute "marks", and
   "steps not run: marks" would be read as A16.

**Files outside my function, one line each:**
- O8's `DESK_RUN_STEPS` (`fno/health/desk_checks.py`) gains `trade_marks`. Its test pins it to the run's plan, and a
  run without its marking is now a miss. `test_a_run_log_missing_a_step_is_a_miss_naming_it` checks both `exits` and
  `trade_marks`.
- E3's run tests:
  - expect the new last step;
  - the rejected-push tests now reject the last step's commit (`REJECT_LAST`, `step trade_marks`);
  - E2c's Drive fixture gives the marking the same Drive-backed journal.
- These are expectation updates only: no check is removed or weakened.

**Criteria and tests:**

| # | Test |
|---|---|
| 1 | `tests/desk/test_trade_marking.py::test_same_as_s2_every_session_a_stale_day_and_a_lost_marking_day`: day 2's marking is lost, and day 3 is valued at day 2's mid, equal to S2's, not day 1's |
| 2 | `...::test_the_equity_row_is_closed_equity_plus_the_open_trades_values` (two trades, stale listed) |
| 3 | `tests/desk/test_trade_marking_step.py::test_an_unmarked_trade_sends_exactly_one_alert...` and `test_trade_marking.py::test_a_leg_never_quoted...` |
| 4 | `...::test_only_the_recorded_valid_snapshot_is_read_never_a_later_capture` |
| 5 | `...::test_a_rerun_gives_the_same_bytes_and_a_same_day_top_up_row_is_replaced` |
| 6 | `tests/record_scan/test_account_files.py` (a forced `git add -f` of `trade_marks.csv` and a shadow `equity_history.csv` is refused; daily totals commit) |
| 7 | `...::test_marking_leaves_the_public_daily_totals_unchanged` (and nothing is committed by the step) |
| 8 | `...::test_a_book_with_no_open_trade_gets_its_equity_row_and_no_trade_rows` |
| 9 | `test_trade_marking_step.py::test_one_account_s_failure_is_alerted_and_never_stops_another_s_marking` |
| 10 | `test_trade_marking_step.py::test_each_shadow_account_is_marked_in_its_own_files` |
| 11 | `...::test_a_stale_leg_past_its_expiry_awaits_settlement_with_s2_s_value_then_leaves_the_list` |
| 12 | `git diff origin/main -- fno/scoreboard fno/books/equity.py fno/scorecard fno/desk/pricing.py fno/desk/snapshot.py` is empty, and no file the branch changes is named in `research/evaluation/PROTOCOL.md` (checked by script) |
| end to end | `tests/timetable/test_marks_step.py`: E3's run over two days writes rows equal to S2's value from the committed run logs, with marked equity equal to closed equity plus the values |

**Gates:**
- `python -m pytest -q -n auto`: 7167 passed;
- `ruff check fno tests tools` clean;
- `ruff format` unchanged;
- `python tools/check_imports.py` clean;
- the largest new file is 122 lines.

**Open, honest:**
- A Drive failure in one account's marking is alerted and the other accounts go on, as in the exit review. It does
  not stop the run the way a failed commit does. The next session's marking writes that day's rows; the missed day
  has no equity row, and S2 is unaffected.
- No shadow account holds a trade yet (nothing fills one). The shadow path is exercised by the test only.
