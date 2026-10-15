# Response 217: LM1, the position monitor, alert only (story text and claims)

Story text: `docs/stories/LM1-position-monitor.md`. Code starts only when the first paper or shadow position is
expected (REPLAN: "a monitor with nothing to watch adds nothing").

## Claims

1. **It cannot trade.** No entry, exit, order or fill path is wired into the monitor; a test lists its imports.
2. **Real cases only.** Each check is design 4.2's list, read from A16's real mark content and E1/E4's real positions
   and exit rules; a check whose input does not exist yet (intraday VIX, intraday weather) waits and builds nothing.
3. **Silent when there is nothing to watch.** No open position: no check, no alert, only the heartbeat. Today nothing
   is open (strong evidence: `journal/` daily totals show 0 open trades on 15 Oct; no shadow account exists).
4. **No duplicates, no second version.** One `AlertSender`, A16's one silence checker with a second heartbeat, E4's
   exit rules, M1's weather rule; the daily run's exit alerts (E8) and the daily RED alert (M2) stay theirs.
5. **Honest limits.** 15-minute marks cannot catch faster moves; the monitor and its checker share one routine
   platform; far legs outside A16's 6% band are reported unmarked, never guessed.

## Open points (asked 16 Oct)

- A16 builder: the step's place after each mark; the second heartbeat; an intraday VIX value.
- O1/O2 builder: the alert path, the 15:15 boundary, the monitor-silent case in O2's suite.
- E8 builder: the information-only exit alert never sets E8's T.
- M1/M2 owner: an intraday weather reading on a mark; M2's daily RED boundary.
