# Story LM1: the position monitor, alert only

**Repository:** trading · **Lane:** 1 (alerts, an outside service, a routine step) · **Size:** M · **Slice:** B ·
**Sources:** design v2 4.2 and 4.4 (`docs/design_v2/04_layers_card_monitor_learning.md:60-93, 140-161`), 6.5
(`06_risk_and_alerts.md:69-96`), REPLAN (`REPLAN.md:123-125`: "LM1 monitor, `alert_only`, starts only when the first
paper or shadow position is open: a monitor with nothing to watch adds nothing"), `REPLAN_new_stories.md:108-115`.

**Description:** As the risk manager and the owner, I want every open paper or shadow position watched on each
15-minute snapshot during market hours, with a fast, plain alert on real danger and silence otherwise, and a heartbeat
that shows the monitor is alive, so that the owner hears about a position in trouble within one snapshot instead of at
the next daily run, while nothing in the monitor can open, change or close a trade.

**Context and why:**
- Today exits are reviewed once a day, at the daily run (execution snapshot 15:15, E3), and alerts come only from that
  run. A position can lose most of its maximum loss between two daily runs without a word.
- Design 4.2 defines the monitor; 6.5 defines the alert classes (DANGER, WARNING), the first-line rule, the limits
  and "monitor silent". Mode `alert_only` is the default: it alerts; exits still happen only at the daily decision
  time. LM2 (slice C) adds `intraday_exits`; it is out of this story.
- **Nothing to watch yet (strong evidence, `journal/` on main, 16 Oct):** no paper trade is open (each book's daily
  total shows 0 open trades), no shadow account exists, the playbook registry is empty. A16, the monitor's price
  source, is not live (its routine waits for the owner, then a 5-session trial). So this story is text now; its code
  starts when the first paper or shadow position is expected (orchestrator's go), never earlier.
- Defined risk is the protection, not speed (6.5): every trade's worst loss is fixed at entry (Rs 10,000 a trade,
  C2/C5). The monitor adds information, never a stop.

**Scope.** In: the monitor's checks on each A16 mark, its alert records, its heartbeat, the "monitor silent" case
(through the existing silence checker), the weekly replay for missed alerts, the start condition. Out: any entry, exit,
order or fill (no entry or exit code path is wired into it); LM2's `intraday_exits`; the daily run's exit alerts (E3,
E8); the daily RED weather alert (M2); a second weather or risk model; any schedule or routine change by this builder.

**Expected design** (design 4.2's interfaces; reuse first):
1. **Where it runs (no new schedule):** one step right after each A16 mark in the same routine run, reading that mark
   through A16's reader (`SnapshotFiles` / `IntradayQuoteSource`, the ledger-named copy, never a bare file name).
   Placement agreed with the A16 builder (open point 1).
2. **`PositionMonitor`** runs one `MonitorCheck` per condition (strategy pattern) over every open position of every
   book and shadow account (E1's `PaperAccount`, read-only). Wired only in a new `fno/monitor/wiring.py`. Staleness
   is checked first: a stale or failed mark gives the staleness WARNING and no other check runs on it.
3. **The checks** (design 4.2 and 6.5; thresholds are proposals, versioned in `config.yaml` `monitor`, owner decides):

| Check | Fires when (on the mark) | Class | Reads |
|---|---|---|---|
| Loss used | a position's marked loss reaches 50% / 80% of its maximum loss at entry | WARNING / DANGER | its legs' bid/ask on the mark (E4's marking) |
| Short strike near | NIFTY within 0.5% of a short strike of an open position | DANGER | index quote, the position's legs |
| Exit rule reached | a registered exit rule (E4's `ExitRule`: profit target, stop loss, time exit) would close it on this mark | DANGER, information only (below) | E4's rules on the mark's marks |
| Big move | NIFTY at least 1.5% from the previous close | DANGER | index quote, A13's previous close |
| VIX jump | VIX up at least 10% in the session | DANGER | an intraday VIX value (open point 3) |
| Weather upgrade | the weather upgraded during the session (AMBER: WARNING; RED: DANGER) | WARNING / DANGER | M1's own rule on the mark (open point 4) |
| Quotes stale | no good mark for 30 minutes (A16's statuses) | WARNING | A16's ledger |
| Expiry near | an open position's expiry or physical settlement is within its registered window | WARNING | the position, the NSE calendar |

   A position whose legs are not on the mark (A16 keeps contracts within 6% of the index) is "unmarked": the
   loss-used check says so once an hour (WARNING, "cannot mark"), never a guessed price.
4. **Alerts** through the one existing `AlertSender` (`fno.composition.build_alert_sender()`, #fno-desk only), no new
   class, wrapped in O1's `ReportedAlerts` (`fno/daily/alerts.py`, after O1 merges; no second wrapper), so an alert
   Slack does not take is never lost: it prints "alert NOT sent: <reason> | <text>" and the routine's prompt posts those
   lines with the Slack connector, as CLAUDE.md's 3 pm rules say (agreed with the O1/O2 builder, 16 Oct):
   - the first line says what to do, or "information, no action" (6.5);
   - each says what the paper record assumes if the owner acts 60 minutes later; in `alert_only` that is always "the
     paper record changes only at the next daily run's execution snapshot" (today's before 15:15, the next session's
     after it);
   - one alert per condition per position per hour; after 10 DANGER alerts in a session, one summary every 30 minutes;
   - each alert is a record (condition, position, snapshot time, sent time, outcome of the send) in
     `research/data/monitor/alerts/<YYYY>/<date>.csv`; a send that fails is printed by `ReportedAlerts`, retried at
     the next mark, and its record keeps the first try.
5. **No duplicate of the daily run's alerts:**
   - an exit rule reached intraday is one information alert ("<trade> reached its <rule> at HH:MM; the paper exit
     happens at today's daily run, and its exit alert follows then"); it names no action and never sets E8's T; E8's
     exit alert at the daily run stays the only action alert (open point 5 with the E8 builder);
   - after the day's execution snapshot (`config.yaml` `desk.timetable.execution_snapshot`, 15:15 today; read, never
     typed) the monitor stays quiet only about an exit-rule hit that the daily run's exit review already handled (same
     position, same rule, same session); market and loss DANGER and WARNING alerts continue to the last mark (15:30),
     under the hourly limit, because the daily run reports only what its 15:15 snapshot decided and a position may stay
     open overnight (O1/O2 builder, 16 Oct);
   - the daily RED weather alert is M2's; the monitor alerts only an upgrade during the session.
6. **Silent with nothing to watch:** with no open position the monitor runs no check, sends nothing and only writes
   its heartbeat (`positions: 0`). It is wired from the start condition: no code runs before the first position.
7. **Heartbeat and "monitor silent":** after every mark it checks, the monitor writes
   `research/data/monitor/heartbeat.json` (mark time, finish time, positions watched, alerts sent). The existing
   silence checker (A16's `heartbeat-check`, `fno/intraday/heartbeat.py`: 30 minutes, 09:45-15:45 IST) gains this
   second heartbeat, and reports "monitor silent" (WARNING) only while positions are open (6.5). One checker, not a
   second one (open point 1). The interface O2's suite drives (`tests/e2e/test_monitor_silent.py`, with a fake clock):
   `MonitorSilence.check(now) -> SilenceResult` (silent or not, minutes since the last finish, positions open). The
   WARNING's exact text: "Action: check the position monitor's routine (story LM1). WARNING, monitor silent: no
   monitor heartbeat for {minutes} minutes while {positions} positions are open; alert_only strategies continue and
   no exit changes." In `alert_only` a silent monitor blocks nothing; new entries are blocked only for
   `intraday_exits` strategies (LM2). The daily card reports the day's monitor uptime (marks checked / due).
8. **Clock (4.4):** times stored in UTC with offset, shown in IST; A16's skew flag (above 5 s) carries into the alert
   record; the monitor never uses a mark's time it cannot trust as "live" (staleness first).
9. **Weekly replay:** `python -m fno monitor replay --week` runs the week's committed marks through the same checks and
   compares the alerts it would send with the alert records: missed alerts, late alerts (snapshot to sent), false
   alarms (conditions gone at the next mark). Written to `research/data/monitor/replay/<week>.md`; numbers only.

**Open points, to agree before the judge (asked 16 Oct; answers in response 217):**
1. A16 builder: the step's place in the recorder's run; the second heartbeat in A16's checker.
2. O1/O2 builder: **agreed 16 Oct** (alert path through `ReportedAlerts`, the boundary after the execution snapshot,
   the monitor-silent interface and text above).
3. A16 builder: an intraday India VIX value; if none exists, the VIX check waits for a source and nothing is built.
4. M1/M2 owner: whether M1 can read the weather on a mark; if not, the weather check waits for M1's intraday rule.
5. E8 builder: the information-only exit alert never becomes E8's T.

**Acceptance criteria:**
1. No entry, exit, order or fill path: the monitor's wiring imports none (a test lists its imports; the judge can
   check).
2. With no open position, a mark writes only the heartbeat (`positions: 0`) and sends nothing.
3. Each check fires on a fixture mark at its threshold and stays quiet just below it (50%/80% loss, 0.5% strike,
   1.5% move, 10% VIX if built, each exit rule, weather upgrade if built, 30 minutes stale, expiry window).
4. A stale or failed mark gives only the staleness WARNING; an unmarked leg gives "cannot mark", never a value.
5. The same condition on the same position alerts once per hour; the 11th DANGER in a session starts the 30-minute
   summary.
6. Every alert's first line is an action or "information, no action", and it states the 60-minute assumption.
7. Every alert is recorded; a failed send prints "alert NOT sent", is retried at the next mark and keeps its first
   record.
8. An intraday exit rule reached gives one information alert and never an E8 exit alert or T; after the execution
   snapshot an exit-rule hit the daily run handled sends nothing, while a NIFTY 1.5% move at 15:25 on a position
   kept open still gives its DANGER.
9. A heartbeat older than 30 minutes inside 09:45-15:45 with positions open gives "monitor silent" (WARNING, the text
   above) through `MonitorSilence`; with no position open it gives nothing (O2's `tests/e2e/test_monitor_silent.py`
   also pins this).
10. The weekly replay reproduces the alert records of a fixture week and lists one planted missed alert.
11. Gates: pytest, ruff, ruff format, the import check; no file or class over 350 lines.

**Test plan:** fixture marks built from a real A16 slot layout; one fixture per check at and below its threshold; the
hourly limit and the summary; a failed send; the 15:15 boundary; the silent checker with and without positions; the
replay. A real-data dry run on the first five live A16 sessions once a position is open (counts and latency only).

**Judge verifies:** the monitor cannot open or close a trade (imports); a quiet day sends nothing; alerts follow 6.5's
first-line rule and limits; no second heartbeat checker or alert sender exists.

**Known limits:**
- A 15-minute check cannot catch a move inside 15 minutes; defined risk, not speed, protects the book (6.5).
- The monitor and its silence checker run on the same routine platform (A16's line 461-466), so a platform outage
  silences both; an independent host is a later decision, not LM1's.
- A16 keeps contracts within 6% of the index, so a far leg can be unmarked; the monitor says so instead of guessing.

**Depends:** A16 live (and its 5-session trial), E1 accounts, E4's exit rules, T1 (the card's uptime line), O1's
alert path; the first open paper or shadow position · **Status:** story text, open points with their owners
(`reviews/claude/response_217_lm1-position-monitor.md`)
