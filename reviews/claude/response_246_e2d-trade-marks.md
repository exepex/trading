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
