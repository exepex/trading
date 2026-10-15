# A16b. NIFTY 15-minute candle back-fill (2020 on): a candle-close realised variance, labelled back-filled

**Repository:** trading · **Lane:** 1 (new story; outside services Groww and Drive) · **Branch:**
`story/a16b-candle-backfill` · **Claims file:** `reviews/claude/response_122_a16b-candle-backfill.md` (the number is
the orchestrator's to confirm)

**Description:** As the statistician and the volatility trader, I want NIFTY's per-session realised variance from
Groww's 15-minute index candles since 2020, built by the same arithmetic as A16's live series and labelled as
back-filled, so that V1's intraday HAR baseline (design 5.3) can be fitted now instead of about a year after A16 goes
live, and no back-filled number is ever mistaken for something known at the time.

**Context and why:**
- Design v2: `02_layers_data_forecast_weather.md` 2.1, row "Groww historical candles ... one-time back-fill" ("if
  15-minute index history exists, intraday realised volatility can be back-filled"); `05_volatility_research.md` 5.2
  (`RV_s` and its void rule) and 5.3 ("HAR on intraday data needs at least 250 sessions ... the best intraday model
  arrives late").
- A16 step 0 found the candles and proposed this story (A16's "Out of scope"). Judge 108 suggested prioritising it
  (minor 3). The orchestrator queued it as decision 15 in response 113, and decision 52 chose it next.
- Binding owner decisions (`docs/DESK_DECISIONS.md`): Groww calls are read-only; storing Groww data is allowed under
  the paid subscription; raw Groww data goes to Drive only, and the public repository holds derived figures only.
- The orchestrator's conditions for this story: back-filled rows are labelled `backfilled` and never count as live
  forecasts; A16's data layout is read, not changed.

## Step 0: feasibility (live, read-only, 15 Oct 2026; counts, timings and differences only, never a level)

These are this builder's own reads. They used `growwapi` 1.5.0 with A16's install line, signed in through the existing
`GrowwProvider`, and went through A16's `ReadOnlyGroww` wrapper. The only call was `get_historical_candles` for
`NSE-NIFTY`, segment CASH. NSE's values came from the A1/A10 index-close archive in the owner's Drive. The scripts are
not committed.

**Coverage, 15-minute candles, 1 Jan 2020 to 14 Oct 2026:**
- 28 calls of 90 days took 34.7 s and returned 45,667 candles on 1,685 days.
- Every day with candles is a calendar session (A7); there are 0 others.
- The calendar has 1,680 regular and special sessions in the range and 6 muhurat sessions. All 6 muhurat days have
  candles, which this story ignores.
- 8 sessions lack some of the 25 candles that start 09:15 ... 15:15:
  - 13 Mar 2020: 23 (a market-wide halt day);
  - 23 Mar 2020: 23 (a halt day);
  - 24 Feb 2021: 5 (NSE's outage);
  - 2 Mar 2024: 10 (a short special session);
  - 18 May 2024: 10 (a short special session);
  - 26 Sep 2025: 22;
  - 10 Oct 2025: 0;
  - 29 Sep 2026: 20.
  Strong evidence (direct reads).
- Candles outside 09:15-15:15 on sessions:
  - 09:00 (pre-open) on 1,678 sessions;
  - 15:30 on 1,674;
  - 15:45 on 358 (from 2025);
  - a few after 16:00 on one day.
- Each candle has 7 fields: start time (IST text, no offset), open, high, low, close, volume, OI. Volume and OI are
  empty for the index.

**1-minute candles also exist from 2020.** Days sampled in 2020-2026 gave 377-420 candles each, about 0.8 s per day.

**15-minute candles carry exactly A16's live levels.**
- Days checked: 14 Oct, 13 Oct and 1 Sep 2026.
- The close of the 15-minute candle that ends at each mark equals the close of the 1-minute candle that ends there:
  75 of 75 marks, largest difference 0.00 points.
- The open of the 09:15 15-minute candle equals the open of the 09:15 1-minute candle: 3 of 3.
- These are A16's live rules (`candle_1m_close` at 09:30 ... 15:30, `candle_1m_open` at 09:15). A16 uses them on every
  live mark, because Groww leaves the index quote's time empty.
- So the back-fill measures the same levels as A16's live series, with about 60 times fewer calls (one per 90 days,
  not one per day).
- Some evidence: 3 days, equality is checked again in the run (criterion 5).

**Against NSE's official open, high and low** (A1/A10 index-close files; 40 random regular sessions 2020-2026):
- **NSE's official open equals the close of Groww's last pre-open 1-minute candle (09:14) on 40 of 40 sessions**, to
  0.00 points.
- The 09:15 candle's open differs from NSE's open on 40 of 40, by up to 51.65 points. NSE's open is the pre-open
  auction's result; the 09:15 open is the first trade after it. Both are correct for what they are.
- **A finding for A16, which this story does not change:** A16's condition "compare the 09:15 `candle_1m_open` with
  NSE's official open and report every difference above 0.05" will report every session by construction. The
  comparable value is the pre-open close. This is reported to the orchestrator for A16's owner and judge.
- High and low: 26-28 of 40 agree within 0.05 points.
  - Most of the rest are small, with Groww's range inside NSE's: from 0.05 to 6.25 points. Reasoning only: Groww's
    candles sample the index less often than NSE's own computation.
  - Two sessions have NSE's low equal to its open (the pre-open value), off by 10.15 and 46.80 points. NSE's daily
    range includes the pre-open value; the candle range from 09:15 does not.
  - One outlier: **23 Mar 2020, Groww's high 196.30 points above NSE's high**, on a halt day. That is a value outside
    NSE's official range, so a check against NSE's range is needed before any level is used. This session is void
    anyway (23 candles).

## Scope

**In:**
- A one-time back-fill command over any range from 1 Jan 2020.
- Raw candle answers to Drive, with manifest rows.
- 26 levels per recorded session, and a candle-close realised variance per session, computed by a new class behind
  A16's `IntradayRealisedVol` with A16's arithmetic.
- A check against NSE's official range and open.
- A provenance label on every row (`backfilled`, or `live` by A17's rule).
- A verify command that recomputes every row from the Drive copies.
- A dry run.
- The same command run later for new sessions extends the series. Scheduling it is the owner's choice (out).

**Out (each with its reason):**
- **Using the series:** fitting HAR or any V1 model, and how a forecast built on back-filled inputs is labelled. That
  is G6/G7's job, under G6's protocol. This story gives every row `measure`, `method`, `provenance` and `first_seen_at`
  so G6 can apply its own rule.
- **Mixing with A16:** a candle row never fills, replaces or edits an A16 row. The two series live in separate files.
  Comparing them on sessions where both exist is the post-mortem's job (layer 8).
- **1-minute back-fill:** not needed. At the marks it gives the same levels (step 0) at about 60 times the calls.
- **Futures and option candles:** different questions (A16's chains, LM1), not V1's target.
- **Changing A16:** its RV files, ledger, heartbeat and NSE-open condition stay as they are. The NSE-open finding goes
  to the orchestrator.
- **Scheduling a daily extension:** no builder creates a scheduled task.

## Definitions

- **Recorded sessions:** the A7 calendar's `regular` and `special` sessions (as A16). Muhurat, holidays and weekends
  are skipped, even when Groww has candles for them. A day outside the calendar's years stops loudly (as A16).
- **Candle time:** the start-time text is parsed as a naive ISO time and given +05:30 (India has no daylight saving,
  as A16). Text with an offset, or text that does not parse, is `candle_parse`, a named failure for its window.
- **Levels (26 a session, A16's marks `T_k = 09:15 + 15k min`, k = 0..25):**
  - `k = 0` (09:15): the **open** of the 15-minute candle starting 09:15, basis `candle_15m_open`;
  - `k = 1..25` (09:30 ... 15:30): the **close** of the 15-minute candle starting at `T_k` minus 15 minutes, basis
    `candle_15m_close`.
  So a session uses the 25 candles that start 09:15 ... 15:15. Candles starting 09:00, 15:30, 15:45 or later are not
  levels; they are counted in the row's `outside_candles`. A missing candle leaves its level `None`; never filled.
- **Previous close:** the 15:30 level of the previous recorded session (muhurat skipped, as A16), or `None` for the
  first session in the data.
- **NSE range check (step 0):** for each session, from the index-close file of A1/A10 (Drive, read through the
  existing `build_nse_index_close_library`):
  - **void `outside_nse_range`** when any of the 26 levels is below NSE's low minus 0.05 or above NSE's high plus
    0.05. A level NSE says never happened cannot be used;
  - **reported, not void:** the pre-open check (`|close of the 09:00 candle - NSE open| > 0.05`, expected equal) and
    the range gap (`NSE high - max candle high`, `min candle low - NSE low`), in points. These stay in the row
    (`nse_open_gap`, `nse_high_gap`, `nse_low_gap`): differences of NSE's figures, never a level;
  - NSE's file missing or unreadable: `nse_check = unchecked`, named, and the session is **void** (`nse_unchecked`).
    Its levels cannot be shown to be inside NSE's range. Reasoning only: an unchecked session is safer out than in;
    the void share shows the cost.
- **Realised variance:** A16's definition and units exactly (`rv_intraday` over 25 intervals, `rv_overnight`,
  `rv_session`, `vol_pct`, the void rules, never interpolated). It is computed by `CandleCloseRv15m`, a new class
  behind A16's `IntradayRealisedVol`, sharing A16's arithmetic (one function, not a copy). `method` is
  `rv-candle-15m-v1` and `measure` is `candle_close`.
- **Provenance (A17's rule):**
  - `first_seen_at` is the fetch time of the raw copy the levels came from;
  - `provenance` is `live` when that time is before 09:15 IST of the session after the row's session, else
    `backfilled`;
  - every row of the first back-fill is `backfilled`;
  - a row's `as_of` is the session's 15:30 IST, as A16's.

## Expected design

- `IntradayCandleSource` (interface): `candles(start, end) -> CandleAnswer` (raw bytes, parsed candles, request and
  response times). It has one adapter, `GrowwCandleSource`, which holds only A16's `ReadOnlyGroww`. The wrapper's
  allow-list gains one constant, `CANDLE_INTERVAL_MIN_15`: no call is added. That is the only line of A16's code this
  story touches, and it is stated in the claims.
- `CandleArchive`:
  - each answer is one gzip JSON document (no time in the gzip header) in the owner's Drive `raw` area, under its own
    content-addressed name: `groww/indices/nifty-candles-15m/<YYYY>/nifty_15m_<start>_<end>_<SHA-256 first 16>.json.gz`;
  - each is logged in `research/data/manifests/groww-candles/nifty-15m.csv` (path, window, request time, fetch time,
    SHA-256, size);
  - nothing is ever written over;
  - a later fetch of a window already held, with other bytes, is kept beside the first, and every changed session is
    named;
  - the table keeps the first version (A11's rule as A17 applies it).
- `SessionLevels`: candles in, 26 levels, bases and counts out. It is pure, with no I/O.
- `NseRangeCheck`: levels and NSE's file in, flags and gaps out.
- `CandleRvTable`: one file per session, `research/data/intraday/rv-candle/<YYYY>/nifty_rv_candle_<YYYYMMDD>.csv`,
  written once, in a folder of its own beside A16's `rv/` (A16's files are never touched). It has A16's RV columns plus
  `provenance`, `nse_check`, `nse_open_gap`, `nse_high_gap`, `nse_low_gap` and `outside_candles`.
- Composition root `fno/intraday/backfill_wiring.py`, added to CLAUDE.md's list. A16's `wiring.py` is not edited.
- CLI:
  - `python -m fno intraday backfill [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--dry-run FOLDER]`. The default range is 1
    Jan 2020 to the latest finished session, in 90-day windows. Windows already archived and fully derived are not
    fetched again (resumable);
  - `python -m fno intraday backfill-verify`, read-only: recomputes every row from the Drive copies its manifest names.

## Acceptance criteria

1. **Read-only, raw to Drive first.**
   - Each window is one `get_historical_candles` call through `ReadOnlyGroww`.
   - Its answer is archived (Drive, manifest row) before any row is derived from it.
   - A failed call or an unreadable answer names the window and the error class, archives nothing, derives nothing
     for that window, and the run goes on to the next window, then exits 1.
   - A rerun fetches only windows not yet fully derived.
   - Tests: a fake source and store; a store that raises (nothing derived); an interrupted run resumed.
2. **Levels.**
   - The 26 levels are exactly the 09:15 open and the 25 closes defined above. Candles at 09:00, 15:30 and 15:45 are
     never levels and are counted.
   - Time text with an offset, or text that does not parse, is `candle_parse`.
   - Tests: a full session; 09:00, 15:30 and 15:45 candles present; one candle missing (its level `None`, never
     filled); a candle at a time that is not a mark; the boundary candles 09:15 and 15:15; an empty answer.
3. **Calendar.**
   - Regular and special sessions get a row; muhurat, holiday and weekend get none, even with candles.
   - A session with no candles still gets a void row (`missing_candles:25`), never silence. 10 Oct 2025 is the real
     case.
   - A day outside the calendar stops with exit 1 and A7's message.
4. **Realised variance.**
   - `CandleCloseRv15m` gives A16's numbers for the same 26 levels. Tested against a hand computation and against
     `QuoteSnapshotRv15m` on the same input. They share one function; a mutation in it fails both.
   - A missing level voids the part that needs it.
   - The first session in the data has a void overnight part.
   - The row is written once: the same inputs again change nothing, different inputs are refused and named.
   - `vol_pct` is as A16's.
5. **NSE check.**
   - A level outside NSE's range by more than 0.05 voids the session (`outside_nse_range`). Tests at 0.05 and 0.06
     beyond.
   - A missing NSE file voids it (`nse_unchecked`).
   - The open, high and low gaps are in the row.
   - The run prints how many sessions have a pre-open gap above 0.05, and every such session by date.
   - It also re-checks step 0's equality on 5 sessions spread over the range: the 15-minute close equals the 1-minute
     close at every mark. That is 5 extra one-day 1-minute reads; the run prints how many marks are equal.
6. **Provenance and look-ahead.**
   - Every row has `first_seen_at` (the raw copy's fetch time) and `provenance` by A17's rule.
   - Tests: fetched after the next session's 09:15 gives `backfilled`; fetched at 18:00 the same day gives `live`;
     09:14:59 and 09:15:00 of the next session (boundary); the next session found by the calendar across a weekend
     and a holiday.
   - The README states plainly: a back-filled row is history fetched later; it was never known at the time by this
     tool.
7. **Void share.** The run prints sessions, `ok`, void by reason, and the void share, and flags it above 5% (design
   5.2). The real run's figures are in the claims.
8. **Verify.** `backfill-verify` recomputes every row from its manifest's Drive copies. A planted change to a row, a
   copy whose SHA-256 differs from its manifest, and a row with no copy are each named; exit 1.
9. **No prices in the repository.**
   - Repository files hold times, counts, statuses, SHA-256 values, the realised variance and NSE gaps (differences),
     never a level, open, high, low or close (a test scans every written file).
   - Raw answers stay in Drive only.
10. **Read-only and secret-safe** (as A16's criterion 10):
    - the source holds only `ReadOnlyGroww`, and a fake whose order methods fail is run through a whole back-fill;
    - the allow-list change is exactly one constant;
    - a grep over the import closure of the new modules finds no order, modify, cancel, position, holdings or margin
      call;
    - fake secrets are planted and grepped in every output.
11. **Separate from A16.** No A16 file under `research/data/intraday/` (rv, slots, heartbeat) is created, read for
    writing or changed by this story's commands (test). A16's `wiring.py` is unchanged (diff).
12. **Interfaces and wiring.** Source, archive, NSE check and realised variance are behind interfaces, wired only in
    `fno/intraday/backfill_wiring.py`.
13. **CLI and dry run.**
    - Exit 0 when every requested session has a row; exit 1 otherwise, after printing what is missing.
    - `--dry-run FOLDER` reads Groww and NSE's archive live, writes everything under the folder (refused inside the
      repository), and commits nothing.
    - Any unexpected error stops the command with its class name only and exit 1.
14. **Real run (rule 6).** The claims show the full back-fill, 1 Jan 2020 to the latest finished session, as counts:
    - windows and calls;
    - sessions, `ok`, void by reason, void share;
    - `backfilled` and `live` counts;
    - pre-open gaps above 0.05;
    - the equality re-check.
    Never a level.
15. **Gates and quality rules 1-9.**
    - Gates: pytest, ruff, imports, code size.
    - Rule 1: this text first.
    - Rule 2: the gap list below.
    - Rule 3: self-review by independent agents.
    - Rule 4: a broken-code proof per criterion.
    - Rule 5: good, bad, boundary and empty cases.
    - Rule 6: criterion 14.
    - Rule 7: the orchestrator's check.
    - Rule 8: after the merge, one real `backfill` of the latest finished session.
    - Rule 9: no money path, so no ChatGPT review (stated, not skipped).

## Gap list (requirement -> criterion, or out of scope)

| Requirement (source) | Covered by |
|---|---|
| One-time back-fill of 15-minute index history, if it exists (2.1 data table) | step 0 (it exists from 2020), 1, 14 |
| Intraday realised volatility from it (2.1) with 5.2's definition: overnight plus 25 intervals, void never interpolated, 5% rule | 2, 4, 7 |
| Labelled as a different measure (A16 Out of scope: "derived RV labelled `candle_close`"; 5.2: "labelled a quote-snapshot realised variance, not a traded-price measure") | Definitions (`measure = candle_close`, `method = rv-candle-15m-v1`), 4 |
| Every day checked against the calendar; holes recorded (A16 Out of scope) | 3 (8 holes known from step 0) |
| Raw to Drive, never in the repository (owner; 4.4) | 1, 9 |
| One read per 90 days, about 30 calls (A16 Out of scope) | 1 (28 calls measured) |
| Back-filled rows labelled `backfilled`, never live forecasts (orchestrator) | 6; the forecast label itself: G6 (out, with the fields it needs) |
| Point in time: inputs only from rows with `first_seen_at` before the cutoff (5.7 rule 6) | 6 |
| A16's layout read, not changed (orchestrator) | 11; the one allow-list constant stated |
| Groww read-only, secrets only in the environment (owner; 6.6) | 10 |
| V1's HAR needs 250 intraday sessions (5.3; judge 108 minor 3; decision 15) | the series itself (about 1,670 sessions); fitting: out (G6/G7) |
| A level outside NSE's official range (step 0's 23 Mar 2020) | 5 |
| A16's NSE-open condition flags every session (step 0 finding) | out of scope here; reported to the orchestrator for A16 |
| Interfaces plus a composition root (CLAUDE.md) | 12 |
| Scheduling a daily extension | out: the owner's |

**Judge verifies:**
- reruns the suite and the gates;
- plants mutations: the 09:15 open versus close, the 25-candle set, the NSE range tolerance, the provenance boundary,
  the void rule;
- runs `backfill --dry-run` for a short range if the owner allows a live Groww read in the judge's session (else says
  so);
- recomputes one session's RV by hand from a fixture.

**Depends:** A1, A7, A9, A10, A16, A17 (the provenance rule) · **Size:** M · **Status:** story text for the judge's
check (quality rule 1); no code yet
