# Response 248: LM1 thresholds, the question for the owner (builder 012eM7Ti, 16 Oct 2026)

Sent to the orchestrator on 16 Oct to put to the owner (CLAUDE.md: everything for the other side is in the repository).
The LM1 story is `docs/stories/LM1-position-monitor.md` (judge 215 PASS). The handover from 01XFXpbk was agreed on 16 Oct. The method is below.


The monitor only sends alerts. It never opens, changes or closes a trade. Every value below is a starting setting (in
`config.yaml`, under `monitor`), and the owner can change any of them later.

Data used:
- NIFTY's 15-minute candles from Groww, read from the A16b archive in Drive and checked against their SHA-256: 1,668
  full sessions, 1 Jan 2020 to 14 Oct 2026.
- NSE's previous close (`warmup_closes.csv`).
- A16's first live day (16 Oct 2026, the 23 marks recorded so far).

Labels:
- **Strong evidence** means many years of data, tested.
- **Some evidence** means data exists but is thin.
- **Reasoning only** means no data.

## Key numbers

- **One 15-minute step** (how far NIFTY moves between two marks): typically 0.07%. It is 0.31% or more once in 20
  steps, and 0.54% or more once in 100.
- **One hour** (how far NIFTY moves in 60 minutes): typically 0.13%. It is 0.58% or more once in 20 hours, and 1.03%
  or more once in 100.
- **How often 0.5% moves happen:** a move of 0.5% or more happens in 7.2% of hours, and in 1.3% of 15-minute steps.

These are strong evidence (1,668 sessions).

## The questions

| # | Threshold | Proposed | Why | Cost of a false alarm | Cost of a miss | Label |
|---|---|---|---|---|---|---|
| 1 | Loss used: WARNING | 50% of the position's maximum loss | Design 4.2 and 6.5 | One message, no action | Late news of half a loss: at most Rs 5,000 on a Rs 10,000 trade | Reasoning only |
| 2 | Loss used: DANGER | 80% | Same | Same | At most Rs 2,000 more before the maximum loss is reached | Reasoning only |
| 3 | Short strike near (DANGER) | NIFTY within 0.5% of a short strike | 0.5% is about 125 points. NIFTY moves that far within an hour 7% of the time, so with the owner allowed 60 minutes to act, the alert usually comes before the strike is crossed | Repeats on a quiet day when the strike sits close | The strike is crossed with no warning beforehand | Strong evidence (the move sizes); the choice of 0.5% is reasoning |
| 4 | Big move (DANGER, one alert for the whole desk) | NIFTY at least 1.5% from the previous close | Design 4.2 | See below | A real stress day is not flagged | Strong evidence |
| 5 | Quotes stale (WARNING) | No good mark for 30 minutes (two missed marks) | Matches A16's 30-minute silence rule (`SILENT_AFTER`) | See below | Positions go unwatched without anyone knowing | Some evidence (one day) |
| 6 | Expiry near (WARNING) | Proposal: 09:30 mark on the session before expiry, and again on expiry day | NIFTY options settle in cash, so delivery risk applies only to stock options. A16 marks NIFTY only, so stock options cannot be marked yet | One message a week | An expiry-day position the owner forgot about | Reasoning only |
| 7 | Alert limits | One alert per condition per position per hour (one per hour for desk-wide conditions); after 10 DANGER alerts in a session, a summary every 30 minutes | Design 6.5 | n/a | n/a | Reasoning only |

### What the data says about the big-move alert (question 4)

A 1.5% move is not rare:

| Period | Sessions | Days a mark reached 1.5% from the previous close | Share |
|---|---|---|---|
| All years | 1,668 | 266 | 15.9% |
| 2020 | 248 | 85 | 34% |
| 2023 | 245 | 10 | 4% |
| 2024 | 245 | 22 | 9% |
| 2025 | 245 | 18 | 7% |
| 2026 (to 14 Oct) | 192 | 33 | 17% |

Other thresholds, all years:
- 1.0%: 34.7% of sessions.
- 2.0%: 7.4%.
- 2.5%: 4.1%.

Once a day crosses 1.5%, it usually stays there: 8 of the 26 marks at the median, and 26 of 26 for the top tenth. 61
of the 266 days had already crossed 1.5% at the 09:15 opening gap.

If the alert repeats every hour while the move lasts, a stress day sends up to about 6 identical DANGER alerts.

**Q4b:** after the first big-move alert, should the monitor alert again only when the move grows by another 0.5% (at 2.0%,
then 2.5%), instead of every hour? My recommendation is yes (reasoning only). An alert that repeats with no new
information trains the owner to ignore DANGER. Each new 0.5% step is new information.

### What A16's first live day says about stale quotes (question 5)

On 16 Oct, A16 recorded these marks:

| Status | Marks | When |
|---|---|---|
| Missed | 3 | 09:15 to 09:45 (the routine started late) |
| Good | 11 | |
| Incomplete | 9 | 6 of them had 73 to 87 of about 224 contracts failed; 3 had 1 failed |

The story's rule says only a good mark is checked. Under that rule, the run of incomplete marks from 12:00 to 12:30
would already have fired the stale WARNING. On a normal day, half of all marks would be "no check".

**Q5b:** should an incomplete mark still be checked for any position whose legs are all present on it? My recommendation is
yes (some evidence: one day). The NIFTY index level itself is good on those marks (index age 0.7 to 1.5 seconds), and
a leg that is missing already gives "cannot mark". Then only missed, failed or late marks would count as stale.

## What I do not know yet (reasoning only)

1. **Bid/ask marking.** Loss used is measured at bid/ask, the price the position could actually be closed at. Right
   after entry, a spread already shows a loss equal to the bid-ask cost. For a far out-of-the-money (OTM)
   defined-risk spread, that can be a noticeable share of the 50% line. I cannot measure this until a real position
   exists. The first 5 live sessions with a position will report it, as counts only.
2. **The short-strike threshold.** 0.5% is a single cut. A threshold based on standard deviations (for example 0.5
   of the hour's typical move) would adapt to VIX. I recommend keeping 0.5% fixed now (KISS) and reviewing it with the
   weekly replay's false-alarm share.
3. **Waiting checks.** The VIX +10% check and the weather check stay as "waits" until their data exists. They need no
   values now.

## Answer format

For each of questions 1 to 7, plus Q4b and Q5b, answer "accept" or give a new value.

## What each alert would say (examples; the wording follows the story's rules)

- "F&O monitor: information, no action. NIFTY is 1.6% below the previous close at 10:30. The paper record changes only at the next daily run's execution snapshot."
- "F&O monitor: review your position. Loss used 82% of maximum on <trade> at 13:15. The paper record changes only at the next daily run's execution snapshot." (No contract price. Index levels are allowed.)
- **VIX up 10% in a session:** not available yet. A16's mark has no intraday VIX, so nothing is built and no alert can fire.
- **Weather turned RED or AMBER intraday:** not available yet. M1 rates the weather once a session.

## Method (repeatable)

The 15-minute copies come from `research/data/manifests/groww-candles/nifty-15m.csv`. They were loaded with
`CandleArchive.load`, which checks each file's SHA-256. Each session's 26 levels come from `session_candles`: the
09:15 open, then the close of each candle. Sessions with a missing candle were left out, which leaves 1,668. The
previous close is NSE's `underlying` in `research/data/nifty-panel/warmup_closes.csv`, regular sessions only.

The 15-minute and 60-minute moves are absolute changes between levels 1 and 4 marks apart, within one session. The
replay over A16's live marks covers one day (16 Oct, `research/data/intraday/slots/2026/10/16/`).

## Round 1 code claims (for judge B; orchestrator's go, 16 Oct: pure checks, texts and limits, unwired)

Branch `story/lm1-code`. A16's `MarkObserver` port does not exist yet (orchestrator gave its go to A16's builder on 16
Oct). So nothing here runs on a mark, posts to Slack, writes a file or reads Drive. Round 2 adds the observer, the
adapters, the alert path through O1's `ReportedAlerts`, the private records, the heartbeat and the mark rows. Round 3
adds the weekly replay.

| Claim | Where | Proof |
|---|---|---|
| Criterion 1: no entry, exit, fill or order path. Every module `fno.monitor.wiring` loads, checked in a fresh interpreter, is outside `fno.desk`/`fno.books`/`fno.daily` except `fno.desk.timetable` (the execution snapshot's time), and none is named after a trade path | `fno/monitor/*`; E4's rule names are kept as plain labels, pinned to E4 by a test | `tests/monitor/test_no_trade_path.py` |
| Criterion 2: with no open position nothing runs (`positions: 0`, no condition) | `monitor.py` | `test_no_position_runs_no_check` |
| Criterion 3: each check fires at its threshold and stays quiet just below. Loss 50% and 80%. Short strike exactly 0.5% from the index level. Big move 1.5%, plus each further 0.5% step when `big_move_step_pct` is set (Q4b), else hourly. Each E4 rule. Stale at 30 minutes. Expiry from N sessions before (NSE calendar). VIX and weather exist only as `WAITING_CHECKS` | `checks.py` | `tests/monitor/test_checks.py` |
| Criterion 4: a mark outside the usable statuses (or with no index level) gives only the stale WARNING. An unmarked position gives "cannot mark" with no value. An incomplete mark is usable only when `check_incomplete_marks` is true (Q5b) | `monitor.py`, `checks.py` | `test_an_unusable_mark_gives_only_the_stale_warning`, `test_an_incomplete_mark_is_checked_only_when_the_setting_allows` |
| Criterion 5: one alert per key per hour (`hourly`) or per session (`once`). Desk-wide conditions are one key for the desk (judge 215 note 2). The 11th DANGER of a session folds into one summary at most every 30 minutes; WARNINGs are never folded | `limits.py` | `tests/monitor/test_limits.py` |
| Criterion 6: every text starts "F&O monitor:"; the first line is "action: ..." or "information, no action"; the last line is the 60-minute assumption, naming today's or the next session's execution snapshot from the desk timetable; no text contains "exit" or "close" (any case); rupees appear only for the position's own loss; NIFTY levels are allowed (judge 215 note 3) | `texts.py` | `tests/monitor/test_texts.py` |
| Settings: all from `config.yaml` `monitor` (an allowed key now), version `lm1-proposal-1`. A missing, unknown or bad value stops at start | `settings.py`, `config.yaml`, `fno/config.py` | `tests/monitor/test_settings.py` |

**Float noise at a threshold (found by a test):** 25,375 / 25,000 − 1 gives 1.4999...%, so a move exactly at 1.5% did
not fire. The percentages are now rounded to 6 digits before the comparison.

**Mutation proofs (each planted bug fails at least one test):**
- loss `>=` to `>`;
- strike `<=` to `<` (it survived until the exact-0.5% case was added);
- the handled exit rule ignored;
- the hourly limit halved;
- the storm limit removed;
- staleness-first removed;
- the run with no positions;
- the 60-minute line fixed to "today".

**Gates:** pytest 7,249 passed; ruff check and format; `check_imports` clean; every file is under 350 lines.

**Interpretations to check (reasoning only):**
- After the 10th DANGER, the summary lists only the DANGER conditions of the mark it is sent on. Conditions held in
  between are kept for the record (round 2) but not repeated.
- An expiry warning is `once` per session, and an exit rule reached is `once` per session, so a whole day is not
  hourly noise.
- The stale clock starts at the session's first mark (09:15) when nothing usable came yet.

### The owner's decision applied (DESK_DECISIONS, 16 Oct 2026, row "LM1 position monitor: starting thresholds", 4186a4ce)

The owner accepted every recommendation. `config.yaml` `monitor` now holds the decided values, with version
`owner-2026-10-16`:
- `big_move_step_pct: 0.5` (Q4b: repeat only on another +0.5%);
- `check_incomplete_marks: true` (Q5b);
- the other values as proposed.

The row says the expiry WARNING is "at 09:30 on the session before expiry and on expiry day". So a new setting,
`expiry_warn_from: "09:30"`, holds back an earlier mark (09:15). The warning stays `once` per session.

The row says "only missed, failed or late marks count as stale". The code counts every status except good and
incomplete, which also includes A16's `stale` status (an index reading too old). I read that as the row's intent:
a stale index cannot be checked.

Tests:
- `test_the_repository_config_holds_the_owners_decided_values` pins every decided value.
- `test_expiry_warns_from_the_0930_mark_only`.

## Round 2a code claims (orchestrator's go, 16 Oct: round 2 on story/lm1-code with A16's port merged in)

A16's port (`story/a16-mark-observer` 938577b3, judge D) is merged into this branch. Round 2 is split: 2a here; 2b is
the real position adapter (below).

| Claim | Where | Proof |
|---|---|---|
| `MonitorObserver` implements A16's `MarkObserver`: a handled mark is skipped; with no position nothing is checked or sent; otherwise read, check, alert, then the public row and the heartbeat. A failure is named by class in the row and heartbeat, then raised (A16 isolates it) | `observer.py` | `tests/monitor/test_observer.py` |
| Criterion 2 live: with nothing open, one row (`positions 0`, `checked False`) and the heartbeat, nothing sent | `observer.py` | `test_with_nothing_to_watch_only_the_row_and_heartbeat_are_written` |
| Criterion 7: the public row is the one-handling marker (a second fire, and a rerun after Drive recovers, send nothing). Every condition is recorded privately: `held`, or `sending` written before the send, then `sent` or `failed`. Drive down: the alert still goes out and the row says `alert_record_failed`. A refused send is printed (`alert NOT sent ...`, for the connector), recorded `failed`, sent again at the next mark, and its first record is kept. No public file names a trade, a price or a loss | `alerting.py`, `alert_records.py`, `mark_rows.py` | the observer tests, including `test_the_sending_row_is_in_drive_before_the_alert_goes_out` |
| The hourly limit holds across marks and runs: the history is the session's `sent` rows read back from Drive, never local state | `alert_records.py` | `test_the_hourly_limit_holds_across_marks_through_the_private_history` |
| Mark reader: the document's level only on a usable status; the last usable mark from A16's ledger (incomplete counts, decision 4186a4ce), but a mark not checked here never resets the stale clock; A16's clock skew carried into the record; NSE's archived close of the previous session; when it is unknown, the row says `previous_close_known False` | `mark_reader.py` | `tests/monitor/test_mark_reader_and_heartbeat.py` |
| Criterion 9: `MonitorSilence.check(now) -> SilenceResult` reuses A16's `heartbeat_state` (30 minutes, 09:45-15:45, recorded sessions), never a copy. It is silent only while positions are open, with the story's exact text | `heartbeat.py` | same file |
| The alert records are git-ignored (`journal/monitor/`) | `.gitignore` | `test_the_alert_records_folder_is_git_ignored` |
| Alert seam: `monitor_alerts()` in `wiring.py` returns the one existing sender. O1's `ReportedAlerts` wraps it there when O1 merges | `wiring.py` | `test_the_observer_and_silence_check_build_from_the_repository_config` |
| Criterion 1 still holds: the fresh-interpreter import list of `fno.monitor.wiring` has no desk, books or daily module except `desk.timetable`. The app's composition root (which also builds the books' services) is imported only inside `monitor_alerts()`, for the sender | `wiring.py` | `test_no_trade_path.py` |

**Choices to check (reasoning only):**
1. **Path.** The public rows and heartbeat are under `research/data/intraday/monitor/`, not the story's
   `research/data/monitor/`, so they go up in A16's own commit (A16e: its committer refuses anything else staged, and a
   second LM1 push inside the observer would race A16's). Sent to the orchestrator for its OK.
2. **E2c's `PrivateFiles` is not used.** The records use the same store under it, `DriveIndexStore` over Drive's
   `paper` area. `PrivateFiles` imports E4's desk records (and through them the fill and entry modules), which
   criterion 1 keeps out of the monitor. Same Drive area, same mirror-then-replace order.
3. **Not wired into A16's recorder.** The story says "wired from the start condition: no code runs before the first
   position". At go-live there are three one-line changes in A16's files, each agreed with the A16 builder:
   - `build_monitor_observer(cfg, folder)` replaces `NoObserver()`;
   - `"monitor/"` joins A16's `OWNED_PATHS`;
   - `heartbeat_check` also asks `build_monitor_silence(folder, PublishedHeartbeat(...))`.
4. **The previous close is NSE's official one** (index-close archive, written at 21:11 IST with retries at 07:41 and
   11:41). On a morning it is late, the big-move check cannot run, and the row says so.

**Round 2b (not built): the real position adapter.**
- It needs E4's net-if-closed. Today that is private in `ExitDesk`, a class that writes fills, so it would be
  extracted as a pure valuation (an E4 change).
- It also needs each trade's exit rules (from the playbook, which is empty) and C2's `HeldMaxLoss`.
- It waits for the first expected position and the E4 and E3 owners.

**Mutation proofs (2a):** each of these planted bugs fails at least one test:
- one-handling removed;
- `failed` counted as sent;
- the sending row not written before the send (it survived until the in-flight test was added);
- silent with no positions;
- an unchecked mark resetting the clock;
- Drive down stopping the send;
- a failure not recorded.

**Gates:** pytest 7,398 passed; ruff check and format; `check_imports` clean; every file is under 350 lines.

## Judge 264 (round 1 FAIL) addressed

**Should-fix accepted (reproduced on 15886d25).** On 1 Dec 2026, a position expiring 28 Jan 2027 at 90% loss used
gave `CalendarError` and no condition at all. The cause was in the design: the expiry check counted sessions for every
position, and any exception from one check took down the whole mark. Fixed at both levels:

1. **`ExpiryNear` counts sessions only when the expiry can be inside the window.** NSE's longest gap between sessions
   from 2017 to 2026 is 5 calendar days (2,478 sessions; pinned by `test_the_seven_day_bound_holds_on_the_calendar`).
   So an expiry more than 7 × (N + 1) days away is more than N sessions away and needs no calendar. When a near expiry
   cannot be counted (past the calendar's end), that position gets a named WARNING, `expiry_uncounted`, with the
   calendar's own words. The first line is "action: check <trade>'s expiry date yourself; NSE's calendar needs next
   year's holiday rows". Every other check still runs.
2. **`PositionMonitor` runs each check in isolation.** A check that raises becomes its own WARNING (`check_failed`,
   desk-wide, hourly, the error's class name only), and the other checks still run. A future bug in one check can no
   longer silence the others, and it is never silent itself.

**Tests:**
- the judge's case (`test_a_far_expiry_past_the_calendar_end_never_stops_the_other_checks`: only the loss DANGER);
- a near expiry past the end (`expiry_uncounted` plus the loss DANGER);
- a broken check isolated;
- both new alert texts follow the first-line and no-exit/close rules.

**Mutation proofs:** removing the bound, the isolation or the `CalendarError` catch each fails a test.

**Note for the owner (judge 264's request).** The owner's row says one alert per condition per position per hour. An
**exit rule reached** is alerted **once per session** instead. It is information only, and E8's daily exit alert stays
the one action alert, so repeating it hourly would add noise and lose no action. The owner can ask for hourly instead.
