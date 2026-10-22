# Story O1-desk-freeze: the paper desk's daily steps freeze behind one switch

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1, judge D: it stops fills and exits. Ordered by the
orchestrator on 22 Oct 2026, from the owner's decision (`docs/DESK_DECISIONS.md`, 22 Oct, cut-list item 2: freeze from
Mon 26 Oct, after the v4 freeze, until the edge study shows a trade with an edge after costs). It is built on a
branch now and merges only after Monday 26 Oct's run, and never between 14:00 and 16:15 IST.

## The rule

One switch in `config.yaml`, `desk.frozen: true`, freezes the paper desk's daily steps. Setting it to `false` (one
line) restarts them the next session. The steps are:
- E3's steps: `versions`, `pack`, `decisions`, `snapshot`, `fills`, `exits` and `trade_marks`;
- O1's desk steps: `book1` (Book 1's decision), `owner_timing_fills` (E8, already off), `reviews` (E6) and `card` (T1).

A frozen step is recorded in the run log with `status: frozen` and the reason code `desk:FROZEN`. It runs nothing,
writes nothing and commits nothing but the log, and alerts nothing (a frozen day is a decision, not a failure).

Everything else runs as today: the 3 pm quote parts, A14c's margin check (off), the weather, the v4 forecasts, G13's and
G13b's steps and scores, the candles and A4h's close reads. The risk manager and the data checks are not changed.

## Design

1. **The freeze replaces a step's action, never its time (strong evidence, read from `DailyRun._plan`).**
   - Only the desk steps carry a time (14:58 pack, 15:12 decisions, 15:15 snapshot). O1's own steps run in their
     turn, and the run's waits are where the 3 pm parts are started and serviced.
   - If frozen steps were simply skipped, `quotes_done` would run at about 14:10. Its 20-minute limit would end near
     14:30, before the parts' 14:38 start, so every part would be "never started" and the day's quotes lost.
   - So a frozen step still waits until its own time, then records `frozen`. The day's timetable stays byte for byte
     the same. Only the actions change.
2. **One place decides.** `DailyRun` takes the set of frozen step names (E3's `DailyRun`, agreed for E3 by the
   orchestrator as before) and records `frozen` for any of them in place of the action. The set comes from
   `config.yaml` through O1's composition root: E3's and O1's desk steps above when `desk.frozen` is true, none when
   false. `desk` is already an allowed key (it holds E3's `timetable`), so `frozen` sits beside it.
3. **Open positions are the one exception (reasoning only; the owner decides).**
   - Freezing `exits` and `trade_marks` while a book holds an open trade would leave that trade unclosed and unmarked
     until the restart. That is a risk the cut-list's "risk and data checks unchanged" does not intend.
   - Proposal: `exits` and `trade_marks` keep running while any book holds an open position. The day's log then
     names why ("open positions: <count>"), and they freeze from the first session with none.
   - Today no book holds a position (the committed logs since 19 Oct show no trades), so in practice the whole desk
     freezes.
   - **Question for the owner, through the orchestrator:** this exception, or a plain freeze of `exits` too?
4. **What reads the desk steps on a later day treats a frozen step as "not a desk day", never as a failure.**
   - O1's block readers (`_unreviewed`, `_unscored`, `_unfilled`) block nothing after a frozen day. Without this,
     the restart day would refuse every entry, because the previous session's exits were "not reviewed".
   - O8's health check (`RunLogCheck`) shows a frozen day as frozen, not as missed or late decisions.
   - Scoreboard B (`CommittedRuns.missed_runs`) counts no missed decision on a frozen day. Otherwise every frozen day
     would count against Book 1.
   - Each of these reads only `status`, with `.get`, as O1-status-only already requires.
5. **The restart is the next session after the switch is set to false.** That session runs the full desk. Its block
   readers look at the last frozen session and block nothing, because nothing was open.

## Owners whose code this touches (agreed through the orchestrator before the code, under the one-builder rule)

- E3: `fno/desk/daily_run.py` (the frozen set, recording `frozen` in place of the action, and the block readers).
- O8: `fno/health/desk_checks.py`. S2: `fno/scoreboard/committed_runs.py`. Both only read `status`.
- `config.yaml`: `desk.frozen: false` until the owner's date. The orchestrator sets it to true after Monday 26 Oct's
  run, in a judged commit.
- O1-status-only's registry gains `desk:FROZEN`.

## Acceptance

1. **A frozen session keeps the timetable and the quotes.** With `desk.frozen: true`, the e2e normal day records
   every desk step `frozen`, starts no `desk book1` child, and writes nothing in the accounts or Drive's private
   files. The 3 pm parts are still recorded exactly as on the twin day (same tree for the quote folders), and
   `quotes_done` runs after the 15:15 snapshot time, as today.
2. **The non-desk steps run unchanged.** Weather, v4 forecasts, G13/G13b, candles and close reads have the same
   results as the twin day.
3. **No alert on a frozen day**, and the day ends "day done".
4. **The restart day blocks nothing.** The session after a frozen one, with the switch set to false, runs the full
   desk; `fills` is not blocked by `_unreviewed`, `_unscored` or `_unfilled`.
5. **Health and scoreboard B read a frozen day as frozen**: no missed run, no late decision.
6. **The open-position exception** (if the owner chooses it): with an open trade, `exits` and `trade_marks` run and
   the other desk steps freeze.
7. **The switch is the only control.** `desk.frozen` absent or false gives today's run unchanged (the existing suite
   passes untouched). A planted freeze of a non-desk step (`quotes_done`) is refused by a test of the frozen set.

## Known limits

- A frozen step records no decision, so D3's decision records, scoreboard B and E6's scorecards have a gap for the
  frozen sessions. That is intended: nothing was decided.
- The card (T1) does not go to #fno-desk while frozen. The owner sees the forecasts in #fno-forecast.
