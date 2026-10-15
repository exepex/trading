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

**In-session check:** to be added as an amendment from a run after 09:15 IST on 15 Oct 2026 (index `last_trade_time`
during the session, which source-time rule applies, two-sided books share, snapshot duration at the chosen pace). The
source-time rule itself is fixed below (Definitions) with its fallback, so the amendment only confirms which branch
applies.

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
     `get_historical_candles(NSE-NIFTY, CASH, 1minute)` over the 5 minutes up to the response; the source time is the
     **end** of the latest 1-minute candle (its start time plus 60 s). That is minute resolution: at the 09:30 mark the
     latest finished candle is 09:29-09:30, so its end is the mark itself and the measured age is about the call's
     latency. The `index_time_basis` field of the document and the ledger says which rule gave the time
     (`last_trade_time` or `candle_1m_end`).
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
- Store: the owner's Drive `raw` area (`build_owner_drive`, A9) under
  `groww/derivatives/intraday-snapshots/<YYYY>/<MM>/<DD>/nifty_<YYYYMMDD>_<HHMM>.json.gz` (gzip with no time in its
  header, so the same document always gives the same bytes; step 0's sizes: about 216 quotes and two chains a mark),
  wrapped by `FirstVersionStore`: different bytes at an existing path (two hosts taking one mark) are never written
  over (A9/A11); they go to the `revisions` area at A11's path (`<raw path>/<found_at>_<sha256>.json.gz`) with a row
  in `research/data/intraday/revisions.csv` (beside the ledger, so one folder is committed); readers use the first
  version (point in time).
- `IntradayRealisedVol` (strategy, design 2.1) with `QuoteSnapshotRv15m` (`rv-quote-15m-v1`), computed from the
  stored snapshots.
- `ServerClock` (interface) with GitHub's and Slack's HTTP `Date` headers; `ClockCheck`.
- `AlertSender` (existing) for alerts; `NoAlertSender` in dry runs and tests.
- Repository files under `research/data/intraday/` (derived only, no prices): `slots/<YYYY>/<MM>/nifty_<YYYYMMDD>.csv`
  (one row per slot), `rv/nifty_rv.csv` (one row per session), `heartbeat.json`, `revisions.csv`. After every mark
  the recorder commits and pushes this folder itself (the existing `GitManifestRecorder`, given its own commit
  message; hooks run, never bypassed), so GitHub's copy of the heartbeat is at most about 15 minutes old.
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
row, not slot statuses): `clock_skew` (more than 5 s against a server), `clock_unchecked` (no server answered),
`source_ahead_of_host` (Groww's time more than 5 s after our receive time).

## Acceptance criteria

0. **Step 0 is recorded** in this file (above) with the in-session check, counts and timings only.
1. **26 marks.** Given a recorded session, the session loop takes exactly the slots 09:15, 09:30, ..., 15:30 IST and no
   others; `snapshot` takes the next mark (waiting at most 15 minutes) and records "already recorded" for a slot that
   has a file or a ledger row. Two overlapping runs (the trigger design) give each mark exactly one ledger row, keep
   the first stored version, and put the other's different bytes under `revisions/` (test with two recorders on one
   store and ledger).
2. **Calendar.** Regular and special sessions are recorded; a muhurat-only day, a holiday and a weekend record nothing
   and print "not a trading day"; a day outside the calendar stops with exit 1 and an alert (A7's message).
3. **Raw to Drive, never overwritten.** Each snapshot taken is one JSON file at the path above in the owner's Drive
   `raw` area; the same bytes again change nothing; different bytes at the same path (two overlapping runs taking one
   mark) are saved under `revisions/` with an index row and the raw file is unchanged (A11); the ledger row describes
   the first version stored, which is what readers and the RV use. **Drive write failure (judge 108, should-fix 5):**
   the mark is `failed` with `drive_write: <error type>`, the document is dropped (never written to the repository or
   spooled in the checkout), the loop goes on to the next mark, and the streak rule alerts (test with a store that
   raises).
4. **Content.** A snapshot holds the index quote, the near future's quote, two chains (nearest listed and nearest
   monthly; the next listed if they coincide) and one quote per contract within 6% of the index level, each with raw
   SHA-256, request and response times; the expected and recorded contract counts are in the document and the ledger.
5. **Gaps recorded, never filled.** Every due slot gets exactly one ledger row; a slot not taken by mark + 120 s is
   `missed` (written by the next run or by `rv`), never taken later and never interpolated; stale, failed and incomplete
   slots carry their status and failure names.
6. **Realised variance.** `rv` writes one row per session with `rv_intraday`, `rv_overnight`, `rv_session`, `vol_pct`,
   `status` (`ok`/`void`), `void_reason`, `good_slots`, `due_slots`, `source`, `as_of` (the session's 15:30 IST),
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
   only a sent alert counts: a failed send ("alert NOT sent") is retried at the next settlement; the outcome line
   ("alert sent" / "alert NOT sent: ...") is printed and kept in the ledger. Dry run: nothing sent.
8. **Clock contract (design 4.4).** Every stored time is UTC with its offset (ISO 8601) and printed in IST; Groww's
   source time is kept apart from our `request_sent_at`, `response_received_at` and `first_seen_at`; the host clock is
   checked against GitHub's and Slack's server times on each run; skew above 5 s is recorded as `clock_skew` and printed
   as a WARNING; no answer is `clock_unchecked`; a source time more than 5 s after our receive time is
   `source_ahead_of_host`.
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
    (below) is reported, with the void share and the consequence above 5% stated.

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
both store, the second's different bytes go to `revisions/`, and the ledger keeps one row (criterion 1 tests this).
A run that starts late or dies leaves its marks to the next fire or, once their windows close, to `missed` rows
(never filled); two bad marks in a row alert (criterion 7).

**Arithmetic (reasoning only).** Without overlap, a fire failing loses 4 marks and voids the session: design 5.2's
5% ceiling would need each of 7 fires to fail under about 0.7% of the time. With overlap, only a fire's three middle
marks are covered once; the trial measures what share of sessions are still void.

**Install line (tested in this container on 15 Oct 2026; `pip install -r requirements-groww.txt` fails here because
the SDK's old dependencies `clint` and `args` do not build):**
`pip install -q -r requirements.txt && pip install -q --no-deps growwapi==1.5.0 && pip install -q aiohttp colorama
"google>=3,<4" nats-py "nkeys<0.3" pandas "protobuf>=5.29,<6" pydantic pynacl "pyotp>=2.9"`. Fixing
`requirements-groww.txt` itself is its own lane-1 change (open item, not in A16).

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
> the ledger and heartbeat and commits and pushes `research/data/intraday/` itself; at the 15:30 mark it also writes
> the session's realised variance; on a non-session day it prints "not a trading day"). If a commit line says "NOT
> committed", commit and push that folder by hand (`git pull --no-rebase` first). Never bypass the record scan. If the
> command exits 1, post its lines to #fno-desk only if it printed "alert NOT sent". Note any failure in
> `conversations/<date>.md`.

**Trial before live (criterion 15).** The recorder counts as live only after a measured trial of at least **5
consecutive sessions** through the routine as set up: per session, marks good / missed / late / stale / failed /
incomplete, the void share, each fire's start delay and run length, and any fire that did not run. The result goes in
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
revised after judge 108 (FAIL, 5 should-fix, all accepted: response 108 part 1b), for the judge's re-check
