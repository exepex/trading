# A16. 15-minute quote recorder (NIFTY spot, near future, weekly and monthly chains)

**Repository:** trading · **Lane:** 1 (new story; outside service Groww, Drive, Slack alerts) · **Branch:**
`story/a16-groww-15min` · **Claims file:** `reviews/claude/response_108_a16-groww-15min.md`

**Description:** As the volatility trader and the data engineer, I want NIFTY's index level, its near future and the
weekly and monthly option chains near the money recorded every 15 minutes of every session, raw in Drive and as a
per-session realised variance in the repository, so that protocol v4 gets a far less noisy volatility target than
daily closes (design 5.1, strong evidence: Andersen, Bollerslev, Diebold and Labys 2003), the live monitor (LM1) gets
real exit prices, and the weekly chain is seen at real quotes.

**Context and why:** Design v2 `REPLAN_new_stories.md` (A16 paragraph), `02_layers_data_forecast_weather.md` 2.1,
`04_layers_card_monitor_learning.md` 4.2 and 4.4, `05_volatility_research.md` 5.2, `06_risk_and_alerts.md` 6.5 and
6.6. Owner decisions that bind it (`docs/DESK_DECISIONS.md`, 15 Oct 2026): the host is a Claude routine ("1 - A");
Groww's API terms allow storing quotes and showing them on the private dashboard ("no issues. we have paid
subscription"); raw Groww quotes stay in Drive (design 4.4); the key stays only in the routine's secrets; read-only
calls. Only recording builds this history: a missed snapshot is lost for good, so failures must be loud.

## Step 0: feasibility (live, read-only, 15 Oct 2026; counts and timings only, no prices)

Made with Groww's SDK `growwapi` 1.5.0 from this session (TOTP sign-in from the environment, 1.7 s). Calls used: only
`get_access_token`, `get_quote`, `get_ltp`, `get_ohlc`, `get_expiries`, `get_contracts`, `get_option_chain`,
`get_historical_candles` (and the deprecated `get_historical_candle_data` once). Scripts are not committed (they print
nothing beyond what is below). Pre-market run 07:01-07:07 IST; in-session run: see "In-session check" below.

**Historical candles (the back-fill question of design 2.1):**
- NIFTY 50 index 15-minute candles exist from **1 Jan 2020** (`groww_symbol` `NSE-NIFTY`, segment CASH). Nothing
  before: 0 candles for sampled days in 2008, 2012, 2015, 2016 and 2018. Strong evidence (direct reads).
- A 90-day request returns everything in one call (1,755 candles, 0.96 s); 32 calls of 90 days covered 1 Jan 2020 to
  14 Oct 2026 in 34.6 s.
- Each candle is 7 fields: start time (text, IST, no offset), open, high, low, close, then volume and open interest,
  both empty for the index.
- Coverage against our NSE calendar (A7): 1,686 calendar sessions (muhurat included) from 2020 to 14 Oct 2026; 1,685
  have candles; **10 Oct 2025 has none**. A whole-day request also returns a 09:00 candle (pre-open) and, from 2025, a
  15:45 one; asked for 09:15-15:30 only, a normal day gives exactly 26 candles (09:15 ... 15:30).
- Days with fewer than the normal candles besides muhurat: 24 Feb 2021 (13: NSE's outage day), 2 Mar 2024 and 18 May
  2024 (11: special Saturday sessions that were short), 26 Sep 2025 (23, ends 14:30), 29 Sep 2026 (21, ends 14:00).
  So Groww's history has holes of its own; a back-fill must check every day, never assume it is whole.
- Option and future candles exist too (`NSE-NIFTY-27Oct26-25000-CE`, `NSE-NIFTY-27Oct26-FUT`: 26 on 14 Oct;
  expired contracts of Aug and Sep 2026 still answer; a contract's candles start only when it was listed).
- Consequence: an intraday realised variance can be back-filled from 2020 from **candle closes**, a different
  measure from A16's **quote snapshots** (a candle close is the last trade of the 15 minutes before the next mark).
  The back-fill is a separate proposed story (see "Out of scope"), not part of A16.

**One live snapshot (timings and counts, pre-market, so books were empty):**
- Index quote `get_quote("NIFTY", NSE, CASH)`: 0.83 s; 27 fields (`last_price`, `ohlc`, `bid_price`, `offer_price`,
  `depth`, `last_trade_time`, ...). **`last_trade_time` was empty for the index** before the market opened; whether
  Groww fills it during the session decides the staleness rule (in-session check below).
- `get_ltp` and `get_ohlc` take a list of symbols in one call (0.8 s, 1.6 s) but carry no time and no bid/ask.
- Near future `NIFTY26OCTFUT` (FNO): 0.71 s; has `last_trade_time` and a 5-level depth. (The `NSE-NIFTY-...-FUT`
  form is refused by `get_quote`; it is the candle symbol only.)
- Expiries (`get_expiries`): 1.6 s; listed 19 Oct (Monday: 20 Oct is a holiday), 27 Oct (monthly), 3, 9, 17, 23 Nov,
  29 Dec 2026. Groww still refuses next year's list (A4's known gap; A4's NSE-file fallback applies).
- Option chain `get_option_chain`: 1.0-1.1 s per expiry; 470 and 522 legs; strikes 50 apart; **54 strikes within 6% of
  spot, 108 contracts per expiry**, every one with its trading symbol. The chain has last price, OI, volume and Greeks
  but **no bid/ask**, so bid/ask needs one `get_quote` per contract (A4's way).
- 216 contract quotes one after another: 170.5 s (0.79 s each), 0 errors, every one with `last_trade_time`.
- Rate limit (measured, 60 quotes per burst): 4 parallel workers 5.1 a second, 0 errors; 8 workers 9.9 a second,
  2 errors; 16 workers 16.3 a second, 24 errors (all `GrowwAPIException`; whether they were HTTP 429 was not shown).
  So the safe pace is about 5 requests a second: **a full snapshot (index, future, 2 chains, 216 quotes) takes about
  45-50 s** at 4 workers. Some evidence (one morning, pre-market).

**In-session check (amendment 1, live, read-only, 15 Oct 2026 09:15-09:31 IST; counts and timings only).** Made by a
standalone probe and by the recorder's own dry run (`python -m fno intraday run --until 09:47 --dry-run <folder
outside the repository>`; no Drive, no Slack, no commit):
- **Groww gives no time for the index during the session either:** `last_trade_time` was empty in 3 of 3 index quotes
  read at 09:18:23, 09:18:43 and 09:19:04 (answered in 0.57-0.72 s). So the candle fallback is the rule in practice;
  the quote branch stays built for the day Groww fills it. Strong evidence for this day (direct reads); whether it
  ever fills it, unknown.
- **1-minute candles arrive in time:** the candle answer at 09:19:25 already held the forming 09:19 candle. At the
  09:30 mark the candle call (sent 0.7 s after the mark, answered 1.5 s after) held 09:25-09:30, so the latest
  finished candle ended exactly at 09:30:00 and the mark was `good`, source age 0.7 s.
- **The 09:15 mark exposed a gap in the passed rule:** at 09:15:01.5 the answer held only the forming 09:15 candle (no
  session candle has finished at the first mark), so "the latest finished candle" gave no time and the mark was
  `stale`. Under the passed text the 09:15 level would be stale every day, which voids every session's RV (both
  parts need 09:15). **Rule change proposed (for the judge's check):** when the latest finished candle ends before the
  mark and the candle that starts at the mark is in the answer, the level is that candle's **open** and its source
  time the mark (an open is fixed by the candle's first trade, at or after the mark; it does not change while the
  candle forms), basis `candle_1m_open`. In practice this applies only at 09:15; at every later mark the close of the
  candle ending at the mark is used as before. The 09:15 level is the first value of continuous trading, at or after
  09:15:00. **It is not NSE's official open** (amendment 3, below): the official open is the pre-open call auction's
  result, which Groww shows as the close of the last pre-open 1-minute candle (09:14 on recent sessions, 09:07 on
  older ones). So the overnight part runs from the
  previous session's last close before 15:30 to the first continuous-trading value at 09:15, and it includes the
  auction-to-first-trade move.
- **One snapshot, measured (09:30 mark):** 2 chains (19 and 27 Oct), 220 contracts within 6%, 220 recorded, 220
  two-sided; the whole snapshot took 53 s at the 5-a-second pace; the gzip document is about 71 kB (09:15 mark).
  Host clock: within 0.5 s of **Slack only**; GitHub was never checked in that run (its API root answers 400 with no
  `Date` through this environment's proxy; judge 108 addendum 3). With the shared clock (amendment 2), a live check
  the same morning found GitHub (repository path) and Slack both within 0.0 s. At 09:15: 216 of 216 recorded, 204
  two-sided, 57 s.
- **Condition on the source (judge 108 addendum 3; corrected by amendment 3, orchestrator decision 53):** in the
  criterion 15 trial and in every weekly post-mortem, each session's **close of the last pre-open 1-minute candle**
  (the last Groww index candle starting before 09:15; 09:14 on recent sessions, 09:07 on older ones; read-only) is
  compared with NSE's official NIFTY 50 open (the "Open Index Value" of A1's archived index-close file for that day),
  and every difference above 0.05 points is reported. **A session with no pre-open candle at all is reported as "no
  pre-open value"**, never filled from the 09:15 open or any other value. A systematic difference means
  a new version (design 5.2), not a silent adjustment. This checks that Groww's index candles carry NSE's own figures;
  the 09:15 level is not compared with the official open, because it is a different number by design.
- **Amendment 3 (15 Oct 2026, why the comparison moved to the last pre-open candle).** The first condition compared the 09:15
  `candle_1m_open` with NSE's official open. NSE's official open is the pre-open call auction's result (09:00-09:08),
  and the 09:15 open is the first value of continuous trading, so the two differ on many sessions by design and the
  check would flag most sessions. Evidence (strong, two independent read-only checks):
  - The A16b builder's recount (its 0adc455, orchestrator decision 53): the close of the last pre-open 1-minute
    candle equalled NSE's official open on **114 of 114** sessions (40 random 2020-2026 sessions plus every session
    from 1 Jul to 14 Oct 2026); only 8 of the 40 random sessions have a 09:14 candle at all (older sessions end the
    pre-open at 09:07). On recent days the 09:15 open differed from the official open on **67 of 74** sessions and was
    within 0.05 on 7.
  - My own check: 6 random regular sessions 2 Jul-5 Oct 2026 (last pre-open candle 09:14) and 6 random sessions
    2021-2023 (the only pre-open candle 09:07): the last pre-open close minus the official open was 0.00 on 12 of 12;
    the 09:15 open differed on 10 of 12 (by -8.30 to +10.65 points) and was equal on 2 of 12, consistent with 67 of 74.
  So a fixed 09:14 would find no value on older sessions, and the 09:15 open cannot tell a bad source from the normal
  auction-to-first-trade move; the last pre-open close can. No code changes: the recorder never computed this
  comparison (the trial and the post-mortem compute it).

## Scope

**In:** Groww read-only snapshots at the 26 marks of every recorded session; raw files to Drive under A9's store with
A11's revision rule; a per-slot ledger, a per-session realised variance and a heartbeat in the repository; gaps
recorded and never filled; the alert after two bad slots in a row; the heartbeat-silence check; the clock contract;
a CLI for one snapshot, a session loop, the realised variance and the silence check; a dry-run mode; the routine prompt
as a proposal.

**Out (each with its reason):**
- **Scheduling** (owner sets up the routine; a scheduled task is created by no builder). The proposal is below.
- **The 2020-2026 candle back-fill.** A different measure (candle closes, not quote snapshots) that protocol v4 (G6)
  must decide whether to use and how to label; proposed as story **A16b** (one read per 90 days, about 30 calls,
  every day checked against the calendar, holes recorded, raw to Drive, derived RV labelled `candle_close`).
- **Agreement with NSE's close and the weekly publication** of completeness, lateness, agreement and revisions
  (design 2.1 "Evaluation metric"): the post-mortem's job (layer 8). A16 writes what they need: per slot the lateness
  and status, per session the completeness, and the revision index.
- **Using the quotes** (bid/ask validity, the monitor's checks, V1/V4 forecasts): LM1, G6/G7. A16 records raw books
  and counts only.
- **A third chain for V4** ("nearest weekly at least 5 sessions out"): A16 records the nearest expiry and the nearest
  monthly (two chains, as design 2.1 says); V4's expiry is covered only when it is one of them. Adding the next weekly
  costs about 22 s more per snapshot; G6 asks for it if V4 needs it.
- **Cost measurement** of the routine (F8).

## Definitions

- **Slots (marks):** `T_k = 09:15 + 15k minutes IST, k = 0..25`: 09:15, 09:30, 09:45, ..., 15:00, 15:15, 15:30. 26 a
  session. A slot is due once its mark has passed.
- **Recorded sessions:** the calendar (A7) decides: `regular` and `special` sessions are recorded at all 26 marks;
  `muhurat` (one evening hour), `holiday` and weekends record nothing ("not a trading day"), as A4. A day outside the
  calendar's years stops loudly with an alert (as A4). A special session shorter than 09:15-15:30 (as on 2 Mar and
  18 May 2024) gets its missing marks recorded as gaps, and its RV is void: the calendar has no hours.
- **On time:** a slot's snapshot counts only if its index request is sent at or after the mark and its response is
  received within **120 s** after the mark. A run that starts more than 120 s after a mark does not take that slot: the
  slot is `missed` and is never taken later (never filled). A run started before a mark waits for it (at most 15
  minutes).
- **Snapshot content (raw, Drive only):** one JSON document per slot: the index quote, the near future's quote, the
  chains of the nearest listed expiry and of the nearest monthly expiry (A5's point-in-time rule, as A4; if they are the
  same expiry, the next listed expiry is the second chain), and one quote (bid, ask, depth, last trade time) per contract
  of those chains with a strike within 6% of the index level, each with Groww's raw answer, its SHA-256, our request
  and response times, and the failure name of any call that failed.
- **Index source time (judge 108, should-fix 1).** The index level's source time is Groww's own time for it, never
  our clock, chosen in this order:
  1. **Primary:** the index quote's `last_trade_time` (epoch seconds, or milliseconds when above 10^11), when present.
  2. **Fallback, when Groww leaves it empty for the index:** one more read-only call right after the index quote,
     `get_historical_candles(NSE-NIFTY, CASH, 1minute)` over the 5 minutes up to the response. In fallback **the level
     and its time come from the same record** (judge 108 addendum 1, should-fix A): the level is the **close of the
     latest finished 1-minute candle** and its source time is that candle's **end** (its start plus 60 s). The quote's
     `last_price` stays in the raw document but is not used as the level, so a frozen quote beside a live candle feed
     can never read as fresh. A candle is finished only when its end is at or before our response time; one still
     forming is never used. At the 09:30 mark the latest finished candle is normally 09:29-09:30, so the level is
     sampled at the minute mark and its age is about the call's latency.
     **Candle times:** step 0 showed them as IST wall-clock text with no offset (`2026-10-14T09:15:00`); they are
     parsed as a naive ISO time and given +05:30 explicitly (India has no daylight saving), never the host's time
     zone; a text that carries an offset, or does not parse, is `index_parse` (failed, by name).
     **At the first mark (amendment 1):** when the latest finished candle ends before the mark and the candle that
     starts at the mark is in the answer (09:15: no session candle has finished yet), the level is that candle's
     **open** and its source time the mark; basis `candle_1m_open`. This is the first continuous-trading value, not
     NSE's official open (the pre-open auction's result; amendment 3).
     The `index_basis` field of the document and the ledger says which rule gave the level and time
     (`quote_last_trade_time`, `candle_1m_close` or `candle_1m_open`); the RV row counts the marks of each basis, so a
     session that mixes them is visible.
  3. **Neither:** no source time; the level is stale (`index_time_missing`), never assumed fresh.
  Pre-market on 15 Oct the index `last_trade_time` was empty; the in-session check (amendment below) says which rule
  applies in the session. Both rules are built and tested, so the recorder does not depend on the answer.
- **Fresh index level:** fresh when its source time is at most **120 s** older than our response time (design 5.2:
  "more than 2 minutes old is stale"), and stale otherwise (`index_time_old`). An unreadable time is `index_parse`
  (failed, by name).
- **A repeated level is a flag, not staleness (judge 108, should-fix 2).** NIFTY ticks in 0.05 steps and calm
  15-minute intervals exist (reasoning only: about 2% of sessions could have one), so equality with the previous
  mark's level is recorded as the flag `index_repeated` on the row and voids nothing; only an old or missing source
  time makes a level stale. Voiding calm intervals would bias the kept RV upward and spend the 5% void budget on calm
  days.
- **Good slot:** taken on time, fresh index level, every call answered, both chains answered with at least one
  contract in the band each (counted per chain, so an empty chain is never hidden by the other one and never good: it
  would hide an API change), and every expected contract quoted. Any other slot is **bad**, with a named status
  (below). What failed before the mark but was retried (sign-in, the expiry plan) is kept as a note and changes no
  status.
- **Realised variance (protocol v4's `RV_s`, design 5.2), units:** with `S_k` the index level of slot `k` of session
  `d` and `S_prev` the 15:30 level of the previous recorded (regular or special) session (a muhurat evening hour is
  skipped: it has no 15:30 mark, and its move falls inside the next overnight return),
  - intraday part `RV_intraday = sum over k=1..25 of (ln(S_k / S_(k-1)))^2` (25 intervals);
  - overnight part `RV_overnight = (ln(S_0 / S_prev))^2`;
  - `RV_s = RV_overnight + RV_intraday`.
  Units: squared natural-log return of one session (dimensionless, a daily variance, not annualised). Shown also as
  `vol_pct = 100 * sqrt(RV_s)`, the session's volatility in percent; for example `RV_s = 0.0001` is 1.00%. Each part is
  **void** (never interpolated) when any slot it needs has no usable index level (missing, late, stale or failed
  index quote; missing option quotes do not void it); `RV_s` is void when either part is. The usable-level rule is one
  function used both when a snapshot is taken (its ledger status) and when the RV is computed from Drive. Labelled
  `quote_snapshot` (not a traded-price measure) with method version `rv-quote-15m-v1`, computed by a strategy class so a
  new sampling rule is a new version, never an edit.

## Expected design

New package `fno/intraday/` (each file under 350 lines):
- `IntradayQuoteSource` (interface, design 2.1): `take(day, slot) -> SnapshotDocument`; one adapter
  `GrowwIntradaySource` (read-only SDK calls `get_quote`, `get_option_chain` plus the existing `GrowwProvider` sign-in
  and expiries; parallel quotes at most 4 workers, about 5 a second).
- `ReadOnlyGroww` (allow-list wrapper, criterion 10): the only Groww object the source holds. The index source time
  uses the quote's `last_trade_time`, else the end of the latest 1-minute index candle (Definitions).
- `ExpiryPlan`: which two expiries (nearest listed; nearest monthly by `PointInTimeMonthlies` with A4's NSE-file
  fallback, flagged when unverified).
- `IntradayRecorder`: slot timing, session decision, store, ledger, alerts, heartbeat; never knows Groww.
- Store (amendment 2, judge 108 addendum 3 should-fix 1, orchestrator decision 39): the owner's Drive `raw` area
  (`build_owner_drive`, A9) under
  `groww/derivatives/intraday-snapshots/<YYYY>/<MM>/<DD>/nifty_<YYYYMMDD>_<HHMM>_<SHA-256 first 16>.json.gz` (gzip
  with no time in its header, so the same document always gives the same bytes). **Every copy has its own,
  content-addressed name**, so two runs taking one mark never write one name: Drive's look-up-then-create can never
  race into two files of one name (which would make every later read of that name fail), and nothing is ever
  written over (A9/A11). `SnapshotFiles` saves copies and resolves reads: **a mark's copy is the one its ledger row
  names**; readers (the next mark's settlement, the realised variance) never read a bare name. The first-version
  store and the revisions index of the earlier text are dropped: with unique names there is no overwrite to divert.
- `IntradayRealisedVol` (strategy, design 2.1) with `QuoteSnapshotRv15m` (`rv-quote-15m-v1`), computed from the
  stored snapshots.
- `ServerClock` (interface) with GitHub's and Slack's HTTP `Date` headers; `ClockCheck`.
- `AlertSender` (existing) for alerts; `NoAlertSender` in dry runs and tests.
- Repository files under `research/data/intraday/` (derived only, no prices), **one file per record** so two runs in
  two checkouts never append to the same file: `slots/<YYYY>/<MM>/<DD>/nifty_<YYYYMMDD>_<HHMM>.csv` (header plus the
  one row of that mark), `rv/<YYYY>/nifty_rv_<YYYYMMDD>.csv` (header plus the session's one row), `heartbeat.json`. After every mark the recorder commits and pushes its own paths in this folder (`slots/`, `rv/`,
  `heartbeat.json`; nothing else, A16e) itself (the existing
  `GitManifestRecorder`, given its own commit message; hooks run, never bypassed), so GitHub's copy of the heartbeat
  is at most about 15 minutes old.
- **Two checkouts, one ledger (judge 108 addendum 1, should-fix B).** Each fire is its own container with its own
  clone, and at every hour boundary two runs are live. The rules:
  1. A run that took a mark writes a row naming its own copy. If two runs both took it, both rows are the same path
     in the two checkouts, and rule 3 keeps **the row first pushed to GitHub**; the other run's copy stays in Drive
     under its own name, unused and harmless. A due mark with no row but copies in Drive (a run saved its copy, then
     died before its row) gets a row naming **the copy with the smallest name**, a fixed rule so every settlement picks
     the same one; a store that cannot list a folder leaves that mark `missed`.
  2. Before it settles marks, a run pulls `main` (`git pull --no-rebase`), so it sees the rows the other run pushed and
     does not write a second `missed` row for a mark that already has one.
  3. Two runs can still settle the same due mark at the same moment (both write its `missed` row, or both write the
     heartbeat). Those are the same path in both checkouts, so the commit's pull merges with the copy already on
     GitHub winning a conflict (`git pull --no-rebase -X theirs`, only in this committer, which commits only this
     folder): the first-pushed row is kept, exactly one row per mark, and the push is never blocked by its own data.
  4. Rows and RV files are written once and never edited (a second write of a row file is refused); the merge rule
     only chooses between two first versions of the same file.
- Composition root `fno/intraday/wiring.py` (added to CLAUDE.md's list); CLI `python -m fno intraday ...`.
- Named constants for every status and failure name (`fno/intraday/` module constants; env names stay in
  `fno/constants.py`).

**Slot statuses:** `good`; `missed` (no snapshot by mark + 120 s: host absent or started late); `late` (taken, but
the index answer came more than 120 s after the mark); `stale` (index source time more than 120 s old, or none);
`failed` (the index call failed or could not be read, or the snapshot could not be taken, or the Drive write failed:
`drive_write: <error type>`, judge 108 should-fix 5; then the mark has a row and no file, the raw document is dropped,
never written to the repository and never spooled anywhere in the checkout, and the mark is never retaken; it counts
as bad for criterion 7's streak alert; failure names are exception class names only);
`incomplete` (index fine, but a chain empty, failed or missing, or a contract quote missing; failed contract quotes
are counted as `quotes_failed:N` in the row, the document keeps every name). **Clock failures** (recorded on the
row, not slot statuses): `clock_skew` (more than 5 s against a server), `clock_partial` (one server not checked),
`clock_unchecked` (no server answered),
`source_ahead_of_host` (Groww's time more than 5 s after our receive time).

## Acceptance criteria

0. **Step 0 is recorded** in this file (above) with the in-session check, counts and timings only.
1. **26 marks.** Given a recorded session, the session loop takes exactly the slots 09:15, 09:30, ..., 15:30 IST and no
   others; `snapshot` takes the next mark (waiting at most 15 minutes) and records "already recorded" for a slot that
   has a ledger row. Two overlapping runs (the trigger design) give each mark exactly one ledger row on GitHub (the
   first pushed), each copy under its own name. Tests: **two git clones of one bare repository** and one shared Drive,
   two recorders overlapping at a boundary mark and both settling the same missed mark (after both push, `origin/main`
   has exactly one row per mark, the first pushed, no conflict markers, both commit lines say committed, Drive holds
   both copies and the row names one); and **a fake Drive that interleaves two runs' look-up and create calls** at one
   mark (both copies stored under different names, every later read of the mark works; with one shared name, the
   reads fail, as on a471f44).
2. **Calendar.** Regular and special sessions are recorded; a muhurat-only day, a holiday and a weekend record nothing
   and print "not a trading day"; a day outside the calendar stops with exit 1 and an alert (A7's message).
3. **Raw to Drive, never overwritten.** Each snapshot taken is one JSON file in the owner's Drive `raw` area under its
   own content-addressed name; the same bytes again change nothing, and two copies of one mark never share a name; the
   ledger row names the copy readers and the RV use. **Drive write failure (judge 108, should-fix 5):**
   the mark is `failed` with `drive_write: <error type>`, the document is dropped (never written to the repository or
   spooled in the checkout), the loop goes on to the next mark, and the streak rule alerts (test with a store that
   raises).
4. **Content.** A snapshot holds the index quote, the near future's quote, two chains (nearest listed and nearest
   monthly; the next listed if they coincide) and one quote per contract within 6% of the index level, each with raw
   SHA-256, request and response times; the expected and recorded contract counts are in the document and the ledger.
5. **Gaps recorded, never filled.** Every due slot gets exactly one ledger row (one file per mark, written once; with
   two checkouts, by the rules of "Two checkouts, one ledger"); a slot not taken by mark + 120 s is `missed` (written by
   the next run or by `rv`), never taken later and never interpolated; stale, failed and incomplete slots carry their
   status and failure names.
6. **Realised variance.** `rv` writes one row per session with `rv_intraday`, `rv_overnight`, `rv_session`, `vol_pct`,
   `status` (`ok`/`void`), `void_reason`, `good_slots`, `due_slots`, `basis_counts`, `source`,
   `as_of` (the session's 15:30 IST),
   `first_seen_at`, `method`, and `inputs_sha256` (SHA-256 of the input files' SHA-256s in slot order); values equal a
   hand computation; any missing or stale index level voids the part that needs it; `rv` prints the share of void
   sessions and flags it above 5% (design 5.2). The row is written once per session (a rerun with the same inputs
   changes nothing; different inputs are refused, reported and alerted, and never stop the heartbeat or the commit).
   `rv` refuses a day that is not a recorded session or whose 15:30 window has not closed; without `--day` it settles
   the latest finished session. Once the recorder has a history, each session's first run also settles a previous
   session left unfinished (missed rows and its RV), so a host that died mid-session never leaves a day open.
7. **Alert after two bad slots in a row.** When two due slots in a row are bad, one SYSTEM alert goes through
   `AlertSender`, its first line saying what to do; one alert per streak (sent when the streak reaches two, also when
   several marks are settled at once) and at most one an hour (a new streak exactly 60 minutes after the last sent
   alert is alerted; one under is held and sent at the first settlement after the hour, even if the streak has ended);
   only a sent alert counts: a failed send ("alert NOT sent") is retried at the next settlement, with at most one send
   attempt per settlement (judge 108 addendum 3, minor 1); the outcome line
   ("alert sent" / "alert NOT sent: ...") is printed and kept in the ledger. Dry run: nothing sent.
8. **Clock contract (design 4.4).** Every stored time is UTC with its offset (ISO 8601) and printed in IST; Groww's
   source time is kept apart from our `request_sent_at`, `response_received_at` and `first_seen_at`; the host clock is
   checked against GitHub's and Slack's server times on each run through **one clock module shared with T1**
   (`fno/server_clock.py`, moved there unchanged from T1's fixed `fno/cards/clock.py`; amendment 2, judge 108 addendum
   3 should-fix 2): only a 2xx or 3xx answer's `Date` is trusted (an error answer may be a proxy's), and GitHub is asked
   at the repository path (`api.github.com/repos/<owner>/<name>`; the API root answers 400 here). Skew above 5 s (plus
   the one-second resolution) is `clock_skew` and printed as a WARNING; one server answering and the other not is
   `clock_partial`, with the unchecked server's reason printed; no answer is `clock_unchecked`; a source time more than
   5 s after our receive time is `source_ahead_of_host`. Tests: an error answer carrying a `Date` is ignored, and
   GitHub is asked at the repository path.
9. **Heartbeat.** Each run writes `heartbeat.json` (last run start and finish; the last slot, its status and skew,
   kept as they were by a run that took nothing); the `heartbeat-check` command reads GitHub's copy (`git fetch`, then
   `origin/main`), never the host's own working tree, so a host whose pushes fail does not look alive; during a
   recorded session from 09:45 to 15:45 IST it reports "silent" with exit 1 and a WARNING alert when the last finish is
   more than 30 minutes old or the copy cannot be read (design 4.2), and "ok" otherwise.
10. **Read-only and secret-safe (judge 108, should-fix 4).** The Groww client the SDK returns can trade (design 6.6),
    so the intraday source never holds it: it gets a `ReadOnlyGroww` allow-list wrapper that exposes only `get_quote`,
    `get_option_chain`, `get_expiries`, `get_contracts`, `get_historical_candles` and the SDK's exchange, segment and
    interval constants; any other attribute (every order, position, holdings, margin, funds or socket call) raises
    `ReadOnlyViolation` before reaching the SDK. Sign-in stays in `GrowwProvider`, which builds the client; the wrapper
    is built around it in the composition root only. Tests: (a) the wrapper refuses every other attribute of the real
    SDK class's public names (read from `growwapi` when installed, else from a fixed list of its 1.5.0 names) and lets
    the allowed ones through; (b) the source's only path to the client is the wrapper (a fake whose order methods fail
    the test, run through a whole session); (c) a grep over the **whole import closure** of `fno/intraday/` (every
    `fno` module it imports, directly or not) finds no order, modify, cancel, position, holdings or margin call name.
    Credentials only from the environment, never written to a file, the ledger, a log line or an alert (test plants
    fake secret values and greps every output).
11. **No raw quotes in the repository.** The repository files hold no price, bid, ask or level: only times, counts,
    statuses, SHA-256 values and the realised variance (test over the written files).
12. **Interfaces and wiring.** Source, store, clock, realised variance and alerts are behind interfaces, wired only in
    `fno/intraday/wiring.py`; swapping the source is one class plus one line there.
13. **CLI.** `python -m fno intraday snapshot [--dry-run FOLDER]`, `run [--until HH:MM] [--dry-run FOLDER]`,
    `rv [--day YYYY-MM-DD]`, `heartbeat-check`; exit 0 for good, already recorded, no mark now or not a trading day;
    1 otherwise. Any unexpected error stops the command with its class name only, an alert and exit 1. `--dry-run`
    reads Groww live but writes every file under a folder outside the repository (refused inside it), sends no alert
    (not even a calendar stop) and commits nothing. The NSE listing used for expiries is read only in every run (never
    archived to Drive or the repository's manifests from here). The commit refuses to run without `core.hooksPath`
    (the record scan is never skipped) and aborts a failed pull's merge.
14. **Gates:** pytest, ruff, imports, code size; no file or class over 350 lines.
15. **Trial before live.** No session counts as recorded history until the 5-session trial of the trigger design
    (below) is reported, with the void share and the consequence above 5% stated, and per session the pre-open
    comparison (the difference, or "no pre-open value"; amendment 3).

## Gap list (design requirement -> criterion, or out of scope)

| Requirement (source) | Covered by |
|---|---|
| Step 0: candles; spot, near future, weekly and monthly chains within 6%; counts and timings only (REPLAN A16; 2.1) | 0 |
| 26 snapshots a session, 09:15-15:30 (A16; 2.1) | 1 |
| Session from NSE's calendar, special recorded, muhurat not (A16 brief; 4.4 clock contract) | 2 |
| Raw files to Drive (A16; 2.1 Outputs; 4.4) | 3 |
| Raw kept under A11's revision rule (4.4) | 3 |
| Bid/ask in the chain snapshot (2.1 table) | 4 |
| Gaps recorded, never filled (A16; 2.1 failure "host down") | 5 |
| Stale quote repeated (2.1 failure modes) | Definitions (source time decides staleness; a repeat is flagged `index_repeated`, judge 108), 5 |
| Derived per-session RV in the repository; definition of 5.2 incl. overnight, 25 intervals, 2-minute staleness, void, 5% rule | 6 |
| Every row: `source`, `as_of`, `first_seen_at`, raw SHA-256 (2.1 Outputs); look-ahead guard by `first_seen_at` (2.1) | 5, 6 |
| Completeness and lateness per session (2.1 metric) | 5, 6 (published weekly: out, layer 8) |
| Agreement with NSE close; weekly publication (2.1 metric) | Out of scope (layer 8) |
| Alert after two missed or stale in a row (A16) | 7 |
| Groww token or API change: alert, fail closed (2.1) | 5 (`failed`), 7 |
| Alert classes and first line, one per condition per hour (6.5) | 7, 9 |
| Clock contract: UTC with offset, IST shown, source vs `first_seen_at`, skew vs Slack and GitHub, >5 s WARNING (4.4) | 8 |
| Heartbeat; silent after 30 minutes (A16; 4.2; 6.5) | 9 |
| No order code; read-only key; key only in secrets (A16; 4.4; 6.6) | 10 |
| Groww terms checked first (4.4) | Owner decision 15 Oct 2026 (DESK_DECISIONS row), cited in Context |
| Public repository holds only derived figures (4.4) | 11 |
| `IntradayQuoteSource`, `IntradayRealisedVol` interfaces (2.1) | 12 |
| Wiring in a composition root (2.1 names storage and pipeline wiring) | 12: `fno/intraday/wiring.py` instead; `fno/storage/wiring.py` is at 345 of 350 lines, so A16's store is built from its `build_owner_drive` in the new root |
| Host: Claude routine (6.6) | Out of scope (scheduling); routine prompt proposed below |
| Historical candle back-fill (2.1 table) | Step 0 done; back-fill out of scope (A16b proposed) |
| Cost of the routine (6.6) | Out of scope (F8) |
| Trigger reliable enough for the 5% void ceiling (judge 108, should-fix 3; 5.2) | Trigger design (overlap), 1, 15 |
| Read-only guard on a client that can trade (judge 108, should-fix 4; 6.6) | 10 |
| Drive write failure (judge 108, should-fix 5) | 3 |
| V4 needs weekly ATM quotes (5.2 table) | Partly: nearest weekly recorded; V4's own expiry out of scope (above) |

## Test plan

Unit tests with a fake source, a fake clock, a local folder store and a fake alert sender: a normal session (26 good
slots, RV matches a hand computation), a late start (missed slot, next one taken), a host gap (two missed, one alert),
stale and repeated index levels, a failed sign-in, an incomplete chain, a rerun of a taken slot, different bytes at the
same path (revision), special Saturday, muhurat, holiday, outside the calendar, the 120 s boundary (at, 1 s under, 1 s
over), the 30-minute heartbeat boundary, clock skew at 5 s and 6 s, no clock answer, empty chains, an empty session
(no slot taken), first session with no previous 15:30 (overnight void), secrets planted and grepped, order methods that
fail, repository files scanned for prices. One dry run on live Groww data with counts and timings in the claims file.

**Judge verifies:** reruns the suite and the gates; plants mutations (the 120 s limit, the 25-interval sum, the void
rule, the streak count, the path conflict); runs one dry-run snapshot in session hours if the owner allows a live
Groww read in the judge's session (else says so); recomputes one session's RV by hand from a fixture.

## Trigger design (judge 108, should-fix 3; the owner sets the routine up, no builder creates a schedule)

**Facts and limits.** Scheduled tasks here have a minimum interval of about one hour (the scheduling tool's own note:
"Minimum interval is normally hourly"), so 26 separate 15-minute fires are not the design. The maximum length of one
routine session is **not documented** anywhere this builder could read (the environment's session-resources page
says nothing about it): unknown, so the trial below measures it before anything counts.

**Design: seven overlapping hourly fires.** One routine fires on recorded-session weekdays at **09:00, 10:00, ...,
15:00 IST** and runs `python -m fno intraday run --until <HH+1>:05` (the 15:00 fire runs to 15:35). Each fire covers
the four marks of its hour **plus** the next hour's first mark (the 09:00 fire takes 09:15, 09:30, 09:45 and 10:00;
the 10:00 fire takes 10:00, 10:15, 10:30, 10:45 and 11:00), so every hour boundary is covered by two runs and one
late, slow or failed fire loses at most the marks only it covered, not the boundary. A run that finds a mark already
stored or already in the ledger skips it ("already recorded") and waits for the next one; two runs racing for one mark
both store, each under its own name, and the row first pushed to GitHub names the copy the mark uses (criterion 1
tests this with two clones and with an interleaving Drive).
A run that starts late or dies leaves its marks to the next fire or, once their windows close, to `missed` rows
(never filled); two bad marks in a row alert (criterion 7).

**Arithmetic (reasoning only).** Without overlap, a fire failing loses 4 marks and voids the session: design 5.2's
5% ceiling would need each of 7 fires to fail under about 0.7% of the time. With overlap, only a fire's three middle
marks are covered once; the trial measures what share of sessions are still void.

**Install line (story A16c, 15 Oct 2026):** `pip install -q --use-pep517 -r requirements.txt -r requirements-groww.txt`.
Without `--use-pep517`, pip builds the SDK's two old source dependencies (`clint`, `args`) with the container's
Debian-patched setuptools, which fails (`AttributeError: install_layout`); with it they build in an isolated
environment. Tested into an empty folder in this container: everything installs and `growwapi` imports. (The
`--no-deps` workaround first written here is no longer needed.)

**Prerequisites in the routine's environment:** `GROWW_API_KEY` and `GROWW_TOTP_SECRET` (secrets only, never in a
file); `FNO_GDRIVE_FOLDER_ID`, `FNO_GDRIVE_OAUTH_CLIENT_ID`, `FNO_GDRIVE_OAUTH_CLIENT_SECRET`,
`FNO_GDRIVE_OAUTH_REFRESH_TOKEN` (the owner's Drive, A9; without them the command stops before the first mark, names
the missing settings and alerts, criterion 13); `FNO_SLACK_BOT_TOKEN` for alerts; push access to
`main`.

**Prompt (proposal):**

> Omenix F&O intraday recorder (story A16). Research data only: never place, modify or cancel orders; never print
> or store a secret. In `exepex/trading` on `main`: run the install line from story A16; `git config core.hooksPath
> .githooks`; `git pull --no-rebase origin main`; then run `python -m fno intraday run --until <HH+1>:05` in the
> background and wait for it (it waits for each mark, records the marks up to that time, and after each mark writes
> the ledger and heartbeat and commits and pushes its own files in `research/data/intraday/` itself; at the 15:30 mark it also writes
> the session's realised variance; on a non-session day it prints "not a trading day"). If a commit line says "NOT
> committed", commit and push only the recorder's own paths by hand (`git add -- research/data/intraday/slots
> research/data/intraday/rv research/data/intraday/heartbeat.json`, `git pull --no-rebase` first); never add the
> whole folder. Never bypass the record scan. If the
> command exits 1, post its lines to #fno-desk only if it printed "alert NOT sent". Note any failure in
> `conversations/<date>.md`.

**Trial before live (criterion 15).** The recorder counts as live only after a measured trial of at least **5
consecutive sessions** through the routine as set up: per session, marks good / missed / late / stale / failed /
incomplete, the void share, each fire's start delay and run length, any fire that did not run, and the pre-open
comparison (the last pre-open close minus NSE's official open, or "no pre-open value"; amendment 3). The result goes in
a claims addendum. **Consequence:** if the void share over the trial (and later over any 20 sessions) is above 5%,
design 5.2's "new version" rule applies (a new sampling rule or trigger) and the host question goes back to the owner;
design 6.6 allows Azure (b) only "if Groww offers a data-only key", so the alternatives are stated for the owner, not
chosen here: GitHub Actions cron is out (runs 4.5-5.5 hours late here, response 91, and no broker key in GitHub, owner
13 Oct), the owner's own computer (c), or accepting a higher void share.

The heartbeat-silence check (`python -m fno intraday heartbeat-check`) needs a second, independent runner (design
4.2). Proposal: the 3 pm recorder routine runs it once (a separate routine), and each hourly run runs it first for the
previous hour. Said plainly: both are Claude routines, so an outage of the routine platform itself silences the
checker too; the only off-platform witness is GitHub's push receipt of each `heartbeat.json` commit (judge 108,
minor 2), which the post-mortem (layer 8) reads to report the day's uptime, and which the owner or the dashboard can
read. A truly independent checker (another host) is a later decision, not in A16. Cost: seven routine sessions a
session-day of about 55 minutes each (F8 measures).

**Depends:** A7, A9, A11, owner's host and terms decisions (15 Oct 2026) · **Size:** M · **Status:** story text
revised after judge 108 (FAIL, 5 should-fix, all accepted: response 108 part 1b) and its addendum 1 (FAIL, A and
B accepted: part 1c); text PASSED (judge 108 addendum 2, 27f7b55). Amendment 1 (in-session check and the 09:15 open
rule, accepted with its NSE-open condition: judge 108 addendum 3) and amendment 2 (content-addressed copies, the shared
clock): for the judge

---

## A16c. Groww install fix and one clock module (follow-up, lane 1, 15 Oct 2026)

**Why:** (1) the plain install of both requirement files (no flag), the 3 pm recorder's and A16's install step, failed
in cloud containers; A16 worked around it with `--no-deps`. (2) A16 left `fno/cards/clock.py` as a re-export
of `fno/server_clock.py` so T1's tests stayed unchanged; the orchestrator asked to point T1 straight at the shared
module and remove the shim.

**Root cause of (1), reproduced:** the SDK depends on `clint` 0.5.1 and `args` 0.1.0, which exist only as old source
packages. With no `pyproject.toml`, pip builds them by running their `setup.py` with the container's system setuptools
(68.1.2, Debian-patched), which fails: `AttributeError: install_layout` ("Failed to build clint args"). In a fresh
virtual environment (pip 26, no Debian patch) they build fine. `--use-pep517` makes pip build them in an isolated
environment with a current setuptools, which works; pip refuses that flag inside a requirements file.

**Change:** the install command everywhere it is documented is `pip install -q --use-pep517 -r requirements.txt -r
requirements-groww.txt` (`CLAUDE.md` step 1 of the 3 pm recorder, `README.md`, A16's install line), and
`requirements-groww.txt` says so in its header. T1's `fno/cards/issue.py`, `fno/cards/wiring.py` and its two test
modules import `fno.server_clock` directly; `fno/cards/clock.py` is removed. No behaviour change in either.

**Acceptance criteria:**
1. The documented command installs both files into an empty folder in this container, and `growwapi` imports; the
   same command without the flag fails on `clint`/`args` (evidence in response 108 part 4).
2. A test fails if any documented install command of `requirements-groww.txt` lacks `--use-pep517`, and checks that the
   requirements file states the command.
3. A test fails if `fno/cards/clock.py` exists again, if T1 or A16 import their clock from anywhere but
   `fno/server_clock.py`, or if `HttpDateClock` is defined anywhere else.
4. T1's and A16's tests pass with only the import path changed in T1's two test modules; gates pass.

**Out of scope:** changing the SDK version, pinning `clint`/`args`, or the container's own setuptools (not this
repository's to change).

---

## A16e. The live committer commits only A16's own paths (follow-up, lane 1, 15 Oct 2026, orchestrator decision 63)

**Why:** A16's committer adds and commits the whole of `research/data/intraday/` (`git add -- <folder>`, then
`git commit -- <folder>`, `fno/storage/manifest_commit.py`). A16b writes `rv-candle/` in the same folder, with its
manifest rows in `research/data/manifests/groww-candles/`. On a shared checkout, A16's run would commit A16b's rows
without their manifests, or any other file someone leaves in the folder (the A16b builder's finding).

**A16's own paths (checked in the code, not assumed):** `slots/` (the ledger, `ledger.py`), `rv/` (the session
realised variance, `rv_table.py`) and `heartbeat.json` (`heartbeat.py`), all under `research/data/intraday/`.
**A16 writes no manifest rows**, so it has none to commit: its Drive store is the bare `AreaStore(drive, raw)`
(`fno/intraday/wiring.py`), not the fingerprinting store, because each copy's name carries its SHA-256 and the ledger
row names the copy (amendment 2). The brief's "its manifests" therefore names nothing; adding a manifest path would
only widen what the run can commit.

**Change (revised after judge 108 addendum 11, FAIL on a59b8be, both should-fix accepted and reproduced):**
1. The committer is given its owned paths: `slots/`, `rv/` and `heartbeat.json`, named once in
   `fno/intraday/wiring.py`. It adds, counts and commits only those pathspecs (`git add -- <owned>`, `git commit
   --only -- <owned>`). **Only owned paths that exist on disk or are tracked are passed**: Git refuses a whole
   `git add` when one pathspec matches nothing (`fatal: pathspec ... did not match any files`, exit 128, reproduced),
   and `rv/` does not exist until the first session's 15:30 mark, so naming it blindly would leave every mark of the
   first live session uncommitted. With no owned path present the outcome is "nothing new to commit". Git matches a
   pathspec by whole path components, so `rv/` never matches `rv-candle/` and `heartbeat.json` never matches
   `heartbeat.json.tmp` (checked: `git add -n` in a scratch repository); the tests keep it proven. Without owned paths
   the committer behaves as today (the manifest committer is unchanged).
2. **The staged check covers the whole index**, not only the folder: before every pull and every commit the run lists
   everything staged (`git diff --cached --name-only`, no pathspec). Anything staged that is not under an owned path
   means another writer is mid-commit on this checkout, and a staged file anywhere makes the pull's merge fail
   ("Your local changes ... would be overwritten by merge", reproduced with a staged manifest row outside the
   folder). The run then **refuses to pull and to commit** ("intraday files NOT committed: N file(s) staged that are
   not the recorder's: <paths>"), touches nothing in the index, and settles from its checkout as it is (the existing
   "pull failed" rule). Paths only, never file contents. Its own rows stay on disk (write-once), so nothing is lost;
   the first commit after the foreign staging is cleared carries them.
3. **One alert per run, never one per mark:** the first refusal in a run is sent to #fno-desk (`AlertSender`;
   `NoAlertSender` in dry runs and tests); later refusals in the same run are printed only, so a stuck checkout sends
   at most seven alerts a session (one per hourly fire).
4. Files that are not staged and not the recorder's (untracked or modified) are left alone: not added, not committed,
   no refusal. Stated plainly: an untracked file that a pull would bring in from GitHub at the same path still makes
   that pull fail; that is reported on the run's pull and commit lines as today, and the stale heartbeat on GitHub is
   what the silence check sees (no new rule here).
5. The routine prompt's hand-commit line names the three owned paths, never the whole folder (edited above).
6. This is the same root rule as E2b's guard (refuse foreign staged work before a pull). The shared push-guard story
   (orchestrator decision 64) will absorb this check later; until then it lives in A16's committer.

**Acceptance criteria:**
1. Real Git, two files in the folder besides A16's: an untracked `rv-candle/2026/nifty_rv_candle_20261015.csv` and an
   untracked `heartbeat.json.tmp`. A16's run commits and pushes its slot row, `rv/` file and heartbeat; the pushed
   commit holds exactly those, and both stray files are still untracked afterwards (boundary: `rv/` versus
   `rv-candle/`, `heartbeat.json` versus `heartbeat.json.tmp`).
2. **Fresh folder:** a fixture with no `rv/` (and, separately, an empty folder with no owned path at all). The first
   mark's slot row and heartbeat commit and push cleanly; the empty folder gives "nothing new to commit".
3. **Staged inside the folder:** `rv-candle/...csv` staged by "someone else". The run refuses to pull and to commit,
   the line names the staged path, one alert is sent, HEAD is unchanged, the stray file is still staged and the run's
   own files are still uncommitted on disk. After the stray file is unstaged, the next commit carries every pending
   A16 file.
4. **Staged outside the folder:** a manifest row in `research/data/manifests/groww-candles/` staged. Refused, one
   alert, HEAD unchanged, the row still staged.
5. **One alert per run:** a run of three marks with the foreign file staged throughout sends exactly one alert and
   prints three refusal lines.
6. Nothing to commit in the owned paths while a stray file sits untracked: "nothing new to commit", no refusal.
7. The manifest committer (no owned paths) still adds and commits its whole folder (existing tests unchanged).
8. Broken-code proof: the old whole-folder add makes criterion 1 fail; passing every owned path whether it exists or
   not makes criterion 2 fail; a staged check limited to the folder makes criterion 4 fail; dropping the staged check
   makes criteria 3 and 4 fail; alerting on every refusal makes criterion 5 fail.
9. Gates: pytest, ruff, imports, code size.

**Status:** text PASSED (judge 108 addendum 12); code on `story/a16e-commit-paths`, claims in response 108
part 6c: for the judge.

**Out of scope, stated:** (a) `git push origin HEAD` publishes every unpushed commit on the checkout, including one
another writer made locally (the class of decision 51 (b) for the desk). Each routine fire is a fresh clone that only
this recorder writes to, and A16b's backfill is a one-off command, so the risk is low (reasoning only); refusing
unpushed commits the run did not make would reuse `fno/desk/git_sync.py`'s `other_work` rule and is a separate
follow-up if the orchestrator wants it. (b) The `-X theirs` pull settles a conflict anywhere in the repository with
GitHub's copy, not only in A16's paths (judged and accepted in A16, amendment 2, rule 3); unchanged here.

---

## A16f. The first mark and the push target (fix, lane 1, 16 Oct 2026)

**Why (strong evidence, 16 Oct 2026):** two defects lost the session's opening marks and kept later rows off `main`.
1. **Early exit.** The routine fires at :52 IST so setup ends before the hour. The 08:52 fire started the recorder at
   08:53:17; 09:15 was 22 minutes ahead, more than `slots.MAX_WAIT` (15 minutes), so `snapshot()` returned
   `no mark now` and `run()` ended on it. `no mark now` is a good outcome, so nothing alerted (heartbeat of 08:53:18 on
   branch `claude/lucid-ptolemy-cn5z9n`). The 09:52 fire then wrote 09:15, 09:30 and 09:45 as `missed` / `not_taken`
   and the two-in-a-row alert fired; the session's realised variance is void. This would repeat every session.
2. **Push target.** `GitManifestRecorder` pulled and pushed the current branch. A routine container starts on a
   `claude/lucid-ptolemy-*` branch GitHub does not have, so every pull failed, every mark printed `NOT committed`, and
   the commits stayed in the container until the agent pushed by hand. Overlapping runs could not see each other's
   rows: both took 11:00 (an add/add conflict on push); 11:15 and 11:30 reached `main` only by a hand rescue.

**Fix.**
1. `run()` no longer ends on `no mark now` while a later mark up to `--until` exists: it sleeps until that mark is
   within `MAX_WAIT` and takes it. `snapshot()` is unchanged (a single snapshot still waits at most 15 minutes).
2. The committer fetches `origin main`, refuses (the outcome names the paths) while the checkout carries any change
   not on `main` outside the writer's own paths, then pulls `origin main` and pushes `HEAD:main`. A routine's session
   branch (main plus the writer's own data commits) publishes; a story branch with unjudged code never reaches `main`
   through a data push. Applies to every user of the committer (manifests, read-model inputs, A16).

**Criteria.** (a) A run started at 08:53:17 with `--until 10:05` takes 09:15, 09:30, 09:45 and 10:00, all good.
(b) A run whose `--until` is before the first mark ends without waiting. (c) A clone on a branch absent from origin
commits and the rows land on `main`; no session branch is created on origin. (d) A branch carrying another change is
refused, the outcome names the path, and `main` is untouched. (e) Every existing recorder and committer test passes.

**Routine prompt (owner edits; agents cannot edit API-created routines):** a step 0 that puts the checkout on `main`
(`git fetch origin main && git checkout -B main origin/main`), and a last step that checks nothing recorded is left
unpushed. With fix 2 the step 0 is belt-and-braces; it is needed until A16f merges.

## A16h. A read-only probe of Groww's streaming feed (lane 1, 22 Oct 2026; owner decision of 23 Oct, orchestrator's go)

**Owner and builder:** the A16 builder (session 01VK88LxJvV1Gi7Wbr3D4fzp). **Judge:** I (`session_01MvZneCLZqBuiGyNxawdVee`),
text first, then the code. **Research note:** `research/school/probes/2026-10-23-live-data-feeds.md` (the owner's
decision: buy nothing; probe the Groww feed already paid for, from Tue 27 Oct, never on v4's clean days 23 and 26 Oct).

**Description:** As the statistician and the Groww intraday owner, I want four facts about Groww's websocket feed
(`growwapi.GrowwFeed`) measured in market hours, read-only, so that the owner can decide whether polling every 15
minutes can be replaced without a second paid source.

**Questions the probe answers (in a dated probe note, each with an evidence label):**
1. **Coverage:** do LTP and market depth stream for the four indices' (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY) monthly
   near-money options (±10 strikes around ATM), NIFTY's weekly near-money options, the current, next and far futures,
   and the four index values?
2. **Subscription limit:** the docs say 1,000, Groww's blog 3,000. A ramp of 500, 1,000, 1,500, 2,000 and 3,000 stops at
   the first refusal or error and records the count reached and the error's class name.
3. **Separate budget:** is the feed apart from the REST limits (10 a second, 300 a minute)? The probe runs while A16's
   marks and the 3 pm recorders run; that day's A16 ledger and A4, A4c and A4f sidecars are compared for 429s and
   missing quotes against the clean days, 23 and 26 Oct.
4. **Rate and latency:** messages per second per instrument; latency = our receipt time minus the tick's own exchange
   time where the tick carries one (median and 95th percentile), else "no exchange time in the tick".

**Design:**
- **`ReadOnlyFeed`** (`fno/intraday/read_only_feed.py`, new), built like `ReadOnlyGroww`: it holds the feed and lets
  through only the market-data names `subscribe_ltp`, `subscribe_market_depth`, `subscribe_index_value`, `get_ltp`,
  `get_market_depth`, `get_index_value`, `get_all_feed`, `consume`, `unsubscribe_ltp`, `unsubscribe_market_depth` and
  `unsubscribe_index_value`. It refuses everything else before it reaches the SDK, including the account-reading
  methods `subscribe_fno_order_updates`, `subscribe_fno_position_updates`, `subscribe_equity_order_updates`,
  `get_fno_order_update`, `get_fno_position_update`, `get_equity_order_update` and their `unsubscribe_` pairs (each
  named in a test), and any `place_`, `modify_`, `cancel_` or `create_` name. `GrowwFeed(groww_api)` takes the full
  trading client, so it is built and wrapped only in the composition root (`fno/intraday/feed_wiring.py`, new); the
  probe holds only the wrapper.
- **Which instruments:** the feed subscribes by `exchange`, `segment` and `exchange_token`, which the option chain does
  not carry (checked 22 Oct: a chain leg holds `trading_symbol`, `ltp`, `open_interest`, `volume`, `greeks` only). The
  tokens come from Groww's public instrument list (the SDK's own `INSTRUMENT_CSV_URL`, about 143,000 rows: index
  values, futures and options with expiry, strike and type), downloaded once per run, read-only; the ATM strike of each
  index comes from one `get_quote` of its index value through A16's existing `ReadOnlyGroww` (no allow-list change).
- **`python -m fno intraday feed-probe --plan <coverage|ramp|alongside> --minutes N`**: a probe, not a recorder. It
  keeps counts and times only (per instrument: ticks, first and last receipt time, latency figures); no tick value is
  printed, committed or posted. The probe note is written by hand from its printed summary.
- **Plans and limits** (every plan unsubscribes everything and stops at once, with one named line, when its own
  sign-in or any call answers 429 or the plan's hard end time is reached):
  - `coverage`: about 400 instruments, 10:20-10:40. It overlaps A16's 10:30 mark on purpose: that mark is the first
    market-hours test of two sign-ins on one key (judge 499).
  - `ramp`: **50**, 500, 1,000, 1,500, 2,000, 3,000 (judge 499 addendum 3: 50 first, so a closed market and a limit
    under 500 can be told apart; coverage holds about 440 topics). A step is refused when a call raises (a 429 stops the
    run instead) or the feed creates fewer topics than asked; a refused batch is released at once. After the close, a
    refusal at 50 twice means a closed market; between marks, a first refusal is a limit; once 50 is accepted, a refused
    step is a limit and the ramp halves its way down to it, to within 50 subscriptions. **The after-close ramp starts
    only once that day's A16b candle catch-up (same Groww key, from 15:33) is recorded finished in
    `journal/runs/<date>.json`** (judge 499 addendum 2; pull `main` first); otherwise no ramp that day, one named line.
    **Never overlapping an A16 mark**
    (judge 499, orchestrator: a mark with no usable level voids the session's RV, which feeds v4 and G14). **First choice:
    after the close**, from 15:45 IST once A16's last mark (15:30, committed about 15:35) is on `main`: accepting a
    subscription needs no live ticks. If Groww refuses subscriptions after hours (a refusal already at the first step,
    500, with the same error at 500 on a retry, is read as "closed market", not as the limit), the probe note says so
    and the ramp runs on a later session between A16's marks only, **10:50:00 to a hard stop at 10:58:00**, one or two
    steps per 8-minute chunk, until done.
  - `alongside`: **at most 1,000 instruments whatever the ramp showed** (orchestrator: the 3 pm data feeds G13, so
    losing it costs a day), behind a **go/no-go gate** (judge 499): it runs only if that day's `coverage` run left A16's
    10:30 and 10:45 marks clean (ledger status good, no 429 failure, no missing quote); it signs in and subscribes before
    14:50 and makes no new sign-in between 14:55 and 15:13 (the 3 pm recorders' window); any condition missed means no
    `alongside` that day, noted in the probe note with the reason. Its instrument list and index quotes are taken after
    the sign-in and before 14:50 (judge 499 addendum 4).
- **The instrument list's URL** is read only in the composition root (`feed_wiring.py`, from the SDK's own constant);
  no other module names `GrowwAPI` or `GrowwFeed` (judge 499 addendum 4).
- **Schedule (IST, from Tue 27 Oct; 28 Oct if the code is not passed by then):** `coverage` 10:20-10:40, `ramp`
  from 15:45 (or 10:50-10:58 chunks), `alongside` from before 14:50 to 15:20 (gate permitting). Run by the builder by hand; no schedule or
  workflow is created.

**Acceptance criteria:**
1. `ReadOnlyFeed` passes exactly the eleven market-data names; each account-reading name above, and trading names the
   test supplies itself (`place_order`, `modify_order`, `cancel_order`, `create_smart_order`; today's `dir(GrowwFeed)`
   has none, judge 499), are refused with nothing reaching the feed; the wrapper cannot be changed after it is built.
2. No module outside the composition root names `GrowwFeed` or `GrowwAPI` (the import-closure test A16 already has).
3. `alongside` refuses more than 1,000 instruments and refuses to start when the gate is not met (a fake ledger with a
   429 or a missing 10:30 or 10:45 mark; a start after 14:50); every plan, on a fake feed answering 429 or at its hard
   end time, unsubscribes all and stops with one named line.
4. `ramp` stops at the first error and reports the count reached; `coverage` reports whether ticks came by class (index
   value, future, and per index, expiry and option type), with the counts per class (judge 499).
5. Nothing the probe prints holds a token, a key or a tick value (a test over its summary lines).
6. Gates: the full suite, ruff, imports, code size.

**Known limits (one line each):** the probe signs in from its own process, so two sign-ins share one key (they
coexisted outside market hours on 15 Oct; the probe tests it in market hours); a ramp to 3,000 may draw throttling on
Groww's side, so it stops at the first error; Groww's terms do not clearly allow read-only use (owner chose not to
ask, 22 Oct); the probe says nothing about how a feed-based recorder would be built (a later story, if the owner wants
one).

**Depends:** A16 (ReadOnlyGroww's pattern, the import-closure test), the Groww SDK as installed by `routine_setup.sh
--groww` · **Size:** S · **Status:** story text round 2 for judge I (judge 499's two should-fixes and two minors, 23 Oct 2026)

### Claims (TLS fix, 23 Oct 2026: orchestrator's go, lane 1, judge I; branch story/a16h-feed-tls)
- **Root cause (strong evidence):** the one-minute dry run of 23 Oct (11:02-11:04 IST) failed with
  CERTIFICATE_VERIFY_FAILED at socket-api.groww.in:443, then NoServersError after about 2 minutes of SDK retries; 0
  ticks, nothing stored. `growwapi/groww/nats_client.py` builds its context with
  `ssl.create_default_context(cafile=certifi.where())`, so it ignores `SSL_CERT_FILE`, while this container's proxy
  re-signs TLS with its own CA. A bare live handshake: certifi alone fails ("self-signed certificate in chain");
  certifi plus the `SSL_CERT_FILE` bundle: "handshake ok (TLSv1.3)".
- **Condition 1, add, never replace:** `feed_wiring.feed_ca_file` writes certifi's roots followed by the
  `SSL_CERT_FILE` bundle to one temporary file; `trust_for_feed` points only the SDK's `nats_client` module's
  `certifi.where` at it (the real `certifi` module and every other caller are untouched). No bundle set or missing:
  nothing changes. Verification stays on: `tests/intraday/test_feed_tls.py` runs real localhost TLS handshakes with the
  SDK's own call: a certificate signed by the added CA verifies; an untrusted self-signed one is refused; certifi alone
  refuses the proxy-signed one; `verify_mode` is CERT_REQUIRED and `check_hostname` is on.
- **Condition 2, own connect timeout:** `open_feed` builds the feed in a daemon thread and waits at most
  `FEED_CONNECT_SECONDS` (30 s); a timeout or an error raises `FeedNotConnected` with one plain line (the error named
  by class only, never its text). `feed_cli` prints `feed probe <plan>: stopped: <line>` and exits 1. Tests: the
  timeout ends in about 0.2 s with a short limit; an error is named by class; the command prints one line.
- **Round 2 (judge 499 addendum 8, should-fix):** `build_feed_probe` itself is now tested with a fake provider and a
  fake `GrowwFeed` that records `nats_client.certifi.where()` at construction (connect time): with `SSL_CERT_FILE` it
  is the combined file (certifi's roots first, then the bundle); without it the module still holds the real `certifi`.
  The module is restored after the test (monkeypatch). Planted removal of the `trust_for_feed` call: the test fails.
- **Scope:** `fno/intraday/feed_wiring.py` and `feed_cli.py` only, plus the new test file; no other module, no
  setting, no TLS check turned off, `HTTPS_PROXY` untouched. Gates on round 2's tree: 14,335 passed, 16 xfailed; ruff,
  format and check_imports clean.

### Claims (code round 2, 23 Oct 2026: judge 499 addendum 5)
- **Should-fixes 1 and 2** were already met at 4abcf179f, pushed after the reviewed ef896e21: the catch-up gate and the
  ramp from 50 with halving. The tests and lines are in "Claims (code round 1 update)" below.
- **Should-fix 3:** `feed_probe.window_refusal(plan, day, now)` is checked by the command **first**, before the gates,
  any sign-in or any quote; the probe checks again after the sign-in and before the instrument list, and once more in
  `run`. Test: clocks at 14:56 (alongside), 10:26 (coverage) and 16:01 (ramp) refuse with one line, and the gate, the
  sign-in and the quotes are never reached (each stub fails the test if called).
- **Minor 1:** `wait` returns False when no time is left, and the watch loop then returns, so a plant on its condition
  ends instead of spinning (test).
- **Addendum 6's minor:** the catch-up gate also requires the candles step's `result.status == "ok"`, since a failed
  catch-up may run again the same day on the same key. Tests: ended failed, and ended without a status.
- **Minor 2:** when alongside cuts to 1,000 it prints which instruments it kept: index values, futures, then options,
  and the last kept class. With today's ±10 strikes there are 226, so the cut does not happen.

### Claims (code round 1 update, 23 Oct 2026: judge 499 addenda 2-4)
- **Ramp** (`fno/intraday/feed_ramp.py`, new): steps from 50; refusal means a raised call (not 429) or fewer topics
  created; refused batches released; after-close double refusal at 50 means `CLOSED`; between marks a first refusal is
  a limit; halving to within 50. Tests: a feed refusing everything (after close: 50 twice, then "closed market"; between
  marks: "0 accepted, 50 refused"), a feed capped at 450 (limit found with low <= 450 < high, gap <= 50, all
  released), a 429 mid-ramp (stops, all released), no limit (3,000 reached), the hard end time (exactly 10:58:00).
- **Catch-up gate** (`feed_gate.catch_up_gate`): no run log, no candles step or an unfinished one refuses with one
  line naming the cause; the command checks it before any sign-in (test).
- **Alongside before 14:50:** the command calls `check_start` after the sign-in and before the instrument list and
  the index quotes; `run` checks again.
- **URL:** read only in `feed_wiring.py` from `GrowwAPI.INSTRUMENT_CSV_URL`.

### Claims (code round 1, 23 Oct 2026)
- **Files:**
  - `fno/intraday/read_only_feed.py`: `ReadOnlyFeed`, `FEED_CALLS` (11) and `ACCOUNT_CALLS` (9, named).
  - `feed_universe.py`: which instruments.
  - `feed_ticks.py`: counts, times and latency.
  - `feed_probe.py`: plans, windows, caps, the stop on any error or the hard end time.
  - `feed_gate.py`: the alongside gate.
  - `feed_cli.py`: `intraday feed-probe`.
  - `feed_wiring.py`: the composition root, the only module that names `GrowwFeed` or builds the client.
  - `cli.py`: one parser line and one dispatch line.
  - `tests/intraday/test_safety.py`: the composition-root list gains `feed_wiring.py`.
- **Criterion 1** (`tests/intraday/test_feed_guard.py`):
  - the eleven names pass and only they reach the feed;
  - each of the 9 account names, plus `place_order`, `modify_order`, `cancel_order` and `create_smart_order`
    supplied by the test, is refused with nothing read from the feed;
  - the SDK's public names equal the allowed plus the refused (a new SDK name fails until it is classified);
  - the guard cannot be changed.
- **Criterion 2:** no module but `feed_wiring.py` names `GrowwFeed`; A16's composition-root test covers
  `GrowwProvider`.
- **Criterion 3** (`tests/intraday/test_feed_probe.py`):
  - each plan starts only inside its window: coverage 10:20-10:25, alongside 14:30-14:50, ramp 15:45-16:00, ramp-day
    10:50-10:51 (boundaries one second either side);
  - alongside refuses 1,001 instruments and accepts 1,000;
  - a fake 429 stops coverage and alongside at once, unsubscribes everything and names it ("rate limited (429):
    RateLimited");
  - the hard end time is reached and never waited past (ramp-day with 120-second steps ends at exactly 10:58:00);
  - the gate refuses on a failed, failing, short or missing 10:30 or 10:45 row;
  - the command checks the gate before any sign-in.
- **Criterion 4:**
  - the ramp stops at the first error with the count reached (1,000);
  - it releases what the failing call asked for, because a call that raises may already have subscribed some;
  - coverage reports by class and feed type (ltp, market_depth, index_value).
- **Criterion 5:** the summary holds neither the fake secret nor the fake tick value; errors are named by class only.
- **Found while building (fixed):**
  - the chain carries no exchange token, so tokens come from Groww's public instrument list (text line, 214bdeb77);
  - MIDCPNIFTY's index value is listed as `NIFTYMIDSELECT`;
  - the nearest NIFTY expiry on 23 Oct (27 Oct) is the monthly, so "NIFTY's weekly" is the nearest non-monthly
    expiry (3 Nov);
  - two probe bugs the tests caught: a failing call's subscriptions were not released, and a wait could pass the hard
    end time.
- **Real counts, 23 Oct:** Groww's instrument list, plus one read-only index quote each, outside market hours; no feed
  was connected.
  - coverage: 226 instruments (4 index values, 12 futures, ±10 strikes of the four monthlies and NIFTY's weekly), about
    440 feed topics with depth;
  - ramp: 3,248 instruments at ±50 strikes on every expiry up to about 3 months.
- **Gates:** 11,705 passed; ruff, format and imports clean; every new file is at most 166 lines.
- **Not done before the judge:** no live feed connection. The probe's first run is Tue 27 Oct.


## A16i: no single lost fire may void a session (owner, 23 Oct 2026: "do whatever it takes")

**What happened (23 Oct).** The 13:52 fire left no commit and no heartbeat. Marks 14:15, 14:30 and 14:45 had one fire
each (a fire runs H:52 to (H+2):05, so only the on-the-hour marks have two), so the day's RV was void, the 5% void rule
broke (1 of 4 sessions) and nothing alerted until the 14:52 fire wrote the gaps at 15:00. Probable cause (timing and a
reproduced error, not proven; the fire's own transcript is not visible): `requirements.txt` gained `cryptography>=42`
at 13:39 IST, and `routine_setup.sh` stopped on Debian's `cryptography 41.0.7` (pip cannot uninstall it), before the
recorder, before any alert. The 14:52 fire hit the same error.

**Change.** (1) `tools/routine_setup.sh` repeats the install over system packages when the plain install fails
(O7b, on `main`). (2) `fno/intraday/cover.py`: each fire runs one hour past its `--until`, capped at 15:35, so
every mark from 10:00 has two fires; the claims keep one taker per mark. Not covered: 09:15, 09:30 and 09:45 (no
fire before 08:52): **owner action, add a second fire at 08:22** (cron `22 8 * * *` with the same prompt).
(3) `.github/workflows/recorder-watch.yml`: `intraday heartbeat-check` twice an hour, 09:47-16:17 IST; GitHub's
schedule is best effort, so this is the second witness. (4) O8's evening check lists "A16 15-minute marks" from
19 Oct (it was `None`, i.e. unchecked).

**Limits.** A fire now lasts about 2h13m; the platform's session limit is unmeasured (a fire killed early leaves the
cover as before). The witness is a GitHub job: if GitHub drops its slot, it is silent.
