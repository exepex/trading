# Judge 249: E2d per-trade daily marks, story text (story/e2d-trade-marks at ec2827ea)

Judge B, 16 Oct 2026. Lane 1 (a new story, touching the paper accounts and the record scan). The claims are in the
builder's message (session 0134MoC6; no response number yet). The diff is a new E2d section at the end of
`docs/stories/E-paper-desk.md` plus a register row.

**Verdict: FAIL.** One should-fix: the story builds a second copy of a marking rule that already exists in scoreboard B.

## Claims checked on main

| Claim | Result | Evidence |
|---|---|---|
| `record_equity` has no caller outside tests | TRUE | `git grep record_equity`: `fno/books/account.py:203` and `tests/books/test_paper_account.py` only |
| Marks live only in memory during the exit review; `daily_totals.csv` holds closed equity only | TRUE | no writer of an open trade's value in `fno/desk/` |
| E1's `Mark(stale=True)` exists | TRUE | `fno/books/equity.py:27` (`price`, `stale`); `MissingMark` also exists |
| Only `.gitignore` keeps account files out; the record scan refuses Groww quotes by path only | TRUE | `.gitignore` lines 11-12; `fno/record_scan/forbidden_files.py` has `RAW_GROWW_QUOTES` only |
| Marking after the exit review sees the day's new entries | TRUE | `fno/desk/daily_run.py`: snapshot, fill (78-82), then exits (89) |
| Scoreboard B re-marks at score time and is not affected | TRUE, but see the should-fix | `fno/scoreboard/daily_values.py` |
| No other register row covers account marks or the record scan's account paths | TRUE | register rows E2c (done), LM1 (alerts only), P2c (reader) |

## Should-fix: one marking rule, not two (one builder per function, DRY)

`fno/scoreboard/daily_values.py` (story S2) already computes exactly what E2d specifies:
- each open trade's value per session, as its cash flow so far plus the held legs at the mid of that day's execution
  snapshot (`DayMarks`, `key_of`);
- a leg without a valid mid keeps its last valid mark, flagged stale;
- a leg never marked leaves the day unvalued.

E2d's "unrealised = mark value plus the trade's cash flow so far" is that same `TradeDay.value`. As written, E2d will
build a second implementation of that rule. The two can disagree on a normal path: E2d's design 2 takes the stale
fallback "from the account's own mark record" (`trade_marks.csv`), while S2 takes it from the snapshot history.
Concrete case:
1. A run's marking step is lost one day (Drive refused, alerted, that day's rows not written).
2. On a later day the contract has no valid quote.
3. E2d then uses an older mark than S2 does, so the paper-books page and scoreboard B show different values for the
   same trade and day.

`daily_values.py` is hashed by the S1 protocol (`research/evaluation/PROTOCOL.md:427`), so E2d must reuse it without
editing it. The story text needs:
1. E2d's marks and trade values come from the same rule S2 uses: import `trade_days` / `DayMarks` / `key_of`, or one
   shared function both call, without editing the hashed file. The stale fallback comes from the execution snapshots,
   not from the account's own earlier rows.
2. An acceptance criterion: for a fixture with an open trade over several sessions, including a missing quote, E2d's
   mark value and unrealised equal S2's `trade_days` value for every session.

## Notes only (no should-fix)

- `ForbiddenFiles.matches` takes one fixed folder prefix. `journal/<book>/account/` and
  `journal/shadow/<account>/account/` need a matcher with a wildcard segment: a new class beside it, not a change to the
  Groww one. That is for the code judge.
- `top_up` also writes an equity row on its day. A same-day `record_equity` replaces it (by date), which is right
  because the later row has the later state. Worth one test in the code phase.
- An entry fills at one side of the quote, so a leg can fill while its mid is invalid (one side missing): the entry day
  is then "unmarked" and alerted. That is correct, and rare.

## Rest of the text

The other design points (snapshot only, never invented, Drive only, public totals unchanged, shadows in their own
files, rerun idempotent) are sound and testable. The acceptance criteria are concrete, nothing posts while building,
and the scope is clear.

## Gates

Story text only: no code to run. The claims above were checked by me on main and ec2827ea.
