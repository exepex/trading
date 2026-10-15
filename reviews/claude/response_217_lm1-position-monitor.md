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

## Agreed with the neighbouring owners (16 Oct), each checked against the code or the story it names

- **A16 builder:** LM1 runs through A16's new `MarkObserver.after_mark` port (theirs to build, isolated: a monitor
  failure never stops the recorder); a stale or failed mark is "no check"; `MonitorHeartbeat` in `fno/monitor/` reuses
  `fno/intraday/heartbeat.py`; no VIX in A16's mark, so the VIX check waits (strong evidence: `fno/intraday/` has no
  VIX).
- **O1/O2 builder:** alerts through O1's `ReportedAlerts`; after the execution snapshot only exit-rule hits the daily
  run handled are quiet, market and loss alerts continue to 15:30 (accepted: my first rule would have dropped a real
  DANGER on a position held overnight); O2 drives `MonitorSilence.check(now)` with the pinned WARNING text. The card's
  uptime line is the card builder's (T2/T3, asked).
- **O8 builder:** the intraday silence check stays A16's and runs where A16's runs; uptime needs per-mark rows, so LM1
  commits one public row per mark (counts only); an uptime line in O8's message is separate O8 work.
- **E2c builder:** alert records name a position and its loss, so they are private: one file per mark through
  `PrivateFiles`, git-ignored; "sending" row, send, outcome row; Drive down still sends; the public mark row is the
  one-handling-per-mark marker (no repeat on overlapping fires).
- **E8 builder:** LM1 cannot set E8's T (T is E8's own post); wording "F&O monitor: information, no action", never
  EXIT/CLOSE or a price, so the owner is not led to act on it.
- **M2 builder:** no intraday weather reading exists in M1, so the weather check waits; M2 owns the daily record's
  upgrade.
