# Judge 122: A16b story text, NIFTY 15-minute candle back-fill: `story/a16b-candle-backfill` d7bfd66a26d44ac0f6a69f3a0cb963045a68d2cc (quality rule 1, text only)

**Number:** 122, the story's claims number (`response_122`).

**What I checked:**
- the new story file, the only change from main 6320f0b;
- A16's `fno/intraday/read_only.py`;
- A17's `provenance` (`fno/global_cues/table.py:36`);
- the `growwapi` 1.5.0 wheel. I unpacked and read it, without installing or running it.

I made no live Groww or NSE read. Step 0's figures are the builder's, and I label them so.

## The orchestrator's questions

**(a) Is 3 days of 15-minute vs 1-minute equality enough? No, for two reasons (should-fix 1).**
- **The equality is structural, but only if Groww aggregates the same way in every year.** The 15-minute candle that
  starts at T-15 should close on the last trade of its last minute, which is the 1-minute close at T.
- **All 3 sampled days are in Sep-Oct 2026:** 1 Sep, 13 Oct and 14 Oct. About 95% of the back-fill is 2020-2025, where
  Groww's history may have been built from another feed or aggregation. So there is no direct evidence for the years
  that matter most. Label: some evidence for 2026, reasoning only for 2020-2025.
- **Criterion 5's re-check has no consequence.** It reads 5 sessions "spread over the range" and only prints how many
  marks are equal. A mismatch would still let every row be written as A16's levels.
- **Cost of checking.** The builder measured about 0.8 s per one-day 1-minute read, so all 1,680 sessions would take
  about 22 minutes and 1,680 calls. A per-session check therefore costs the same as a 1-minute back-fill. That is why a
  stratified sample with a stop rule is the right middle (reasoning only).

**(b) Which direction voids, and is the 23 Mar 2020 error caught? Not guaranteed as written (should-fix 2).**
- **What voids as written:** one of the 26 *levels* (the 09:15 open and the 25 closes) lying below NSE's low − 0.05 or
  above NSE's high + 0.05.
- **Groww's range inside NSE's:** it never voids. That is right: 12-14 of 40 sessions are that kind, and the two "NSE
  low = pre-open open" sessions are inside too.
- **23 Mar 2020 was a candle *high* 196.30 points above NSE's high.** A spike inside a candle need not move that
  candle's open or close. So the levels-only check can pass a session whose candles hold a value NSE says never
  happened. That session is void anyway (23 candles), but the same error on a full session would pass. It would show
  only as a negative `nse_high_gap`.
- **The story's own principle** is "a level NSE says never happened cannot be used". Data whose high is impossible is
  not trustworthy for its closes either.
- **Cost of voiding on it, from step 0's sample:** 0 of 40 sessions apart from 23 Mar 2020 had Groww's high or low
  outside NSE's range. So it is cheap (some evidence, 40 sessions).

**(c) Is one allow-list constant really no new call surface? YES.**
- `CANDLE_INTERVAL_MIN_15 = "15minute"` is a plain string attribute of `GrowwAPI` (`growwapi/groww/client.py:91`, beside
  `CANDLE_INTERVAL_MIN_1 = "1minute"` at :86).
- `get_historical_candles` is already in `READ_CALLS` (`read_only.py:15`). Adding the name to `CONSTANTS` lets one more
  string through `__getattr__` and no callable.
- Criterion 10 also pins "exactly one constant".

**(d) Rule 5 cases: mostly covered, with named gaps (minor 1, and should-fix 3 for the ordering).**
- **Covered:**
  - muhurat is ignored (criterion 3);
  - 10 Oct 2025 with no candles gets a void row `missing_candles:25` (criterion 3);
  - one missing candle (criterion 2);
  - the 09:15 and 15:15 boundaries;
  - an empty answer;
  - 0.05 / 0.06 at the NSE check;
  - the provenance boundary 09:14:59 / 09:15:00.
- **Not named:**
  - the two halt days, 13 and 23 Mar 2020 (23 candles);
  - 24 Feb 2021: 5 candles, and NSE extended trading to 17:00 that day, which is likely the "few after 16:00 on one
    day";
  - the 2024 short specials, 2 Mar and 18 May (10 candles each);
  - the session after 10 Oct 2025, whose previous close does not exist.
- **Should-fix 3 (ordering).** "The run goes on to the next window" (criterion 1) plus "the row is written once"
  (criterion 4) gives a real defect.
  - If window *n* fails, the first session of window *n+1* has no previous session derived yet. It is written once with
    a void overnight part.
  - When window *n* is fetched on the rerun, that row's inputs change. The rerun then either keeps a wrong void, or is
    refused as "different inputs".
  - A transient Groww failure would permanently damage a row.

**(e) Provenance and labelling: SOUND, with two points to pin (minors 2 and 3).**
- **A17's rule matches.** `live` when first seen before 09:15 IST of the first NSE session after the row's session, else
  `backfilled`. That equals `provenance()` in `fno/global_cues/table.py:36-39`.
- **`first_seen_at` is the raw copy's fetch time.** A later re-fetch with other bytes keeps the first version (A11's rule
  as A17 applies it). That is right.
- **`measure = candle_close` and `method = rv-candle-15m-v1`.** These keep the series apart from A16's quote-snapshot
  measure. Criterion 11 keeps the files apart.
- **"Never counts as a live forecast" is delegated to G6.** That is reasonable, since G6 owns the forecast label. But it
  says nowhere that G6 has been told. See minor 3.

## Other checks

- **The A16 finding is correct by construction.** NSE's official open is the pre-open auction price. The 09:15
  1-minute open is the first trade after it, so A16's "report every difference above 0.05" fires on every session.
  It is rightly kept out of this story; see minor 4.
- **The gaps are differences, as A16 set the precedent.** `nse_high_gap` plus NSE's public high gives Groww's maximum
  candle high, which is close to the public index level. It is the same kind of derived figure A16's open difference
  publishes (judge 108). Note only.
- **The orchestrator's conditions are respected:**
  - raw to Drive only;
  - written once;
  - nothing over A16's files;
  - its own composition root;
  - no scheduled task.
- **Rule 9 is stated, not skipped:** no money path.

## Should-fix (text)

1. **The equality evidence and its stop rule.** Replace criterion 5's 5-session print with a stratified re-check that
   has a consequence. For example:
   - at least 2 sessions per calendar year 2020-2026 (14 or more), plus every special session and the sessions next to
     the 8 holes;
   - every mark compared, 15-minute close against 1-minute close;
   - any mark differing by more than 0.05: that year's rows are not written, every differing session is named, and the
     run exits 1. The owner decides then.

   The orchestrator may instead choose a per-session check, about 22 min and 1,680 calls by the builder's own rate,
   voiding a session on mismatch. Either is acceptable; the choice and its reason go in the story. Also say in step 0
   that the 3 days are all 2026.
2. **Void on a candle high or low outside NSE's range.** Extend `outside_nse_range` to any of the 25 used candles'
   **high** above NSE's high + 0.05 or **low** below NSE's low − 0.05, not only the 26 levels. Add a test shaped like
   23 Mar 2020: a full session whose closes are inside NSE's range but one candle's high is 196.30 above, which must
   void. State the cost from step 0 (0 of 40 besides 23 Mar 2020).
   - Or keep levels-only, with a stated reason and the gap reported loudly. But then the story's own principle reads
     wrong.
3. **Order-dependent rows after a failed window.** A session whose previous recorded session has no derived row in this
   run, or before it, must not be written. It is deferred, and the run exits 1 naming it. The exception is a previous
   session that exists with a void 15:30 level, such as 10 Oct 2025, which gives a void overnight part. Tests:
   - a failed middle window, then a resume: the next session's overnight part is computed and nothing is refused;
   - the session after 10 Oct 2025: overnight void, intraday computed.

## Minor (text)

1. Name these rule-5 cases with their expected rows:
   - 13 and 23 Mar 2020 (23 candles);
   - 24 Feb 2021 (5 candles, and its candles after 15:30 are not levels and are counted in `outside_candles`);
   - 2 Mar and 18 May 2024 (10 candles each). Also say whether such structurally short specials count in criterion 7's
     5% void share or are shown apart;
   - 26 Sep 2025 (22) and 29 Sep 2026 (20): unexplained holes. Say whether NSE had a disruption, or that they are
     Groww's holes.
2. **Provenance: one function.** Compute `provenance` with A17's function, not a copy (DRY). If it must move to a
   shared module for both packages, say where, and keep A17's verify using it.
3. **"Never a live forecast":** name where G6 is told: a line in G6's story open questions, or a decision row. Then the
   condition does not live only in this story's "Out".
4. **A16's NSE-open finding:** name where it was reported, a decision or claims row, so it reaches A16's owner and
   judge.
5. **A 90-day window's answer:** if Groww truncates or caps an answer, the per-session `missing_candles` void catches it.
   Say so, and print each window's candle count against the expected 25 × sessions, so a cap shows as one line, not as
   scattered voids.

## Verdict: FAIL for d7bfd66a26d44ac0f6a69f3a0cb963045a68d2cc (story text)

- **What is sound:**
  - the scope, the separation from A16, the Drive-only raw data and the write-once table;
  - the provenance rule (equal to A17's);
  - the allow-list change, which is verified as a plain string constant with no new call.
- **Three should-fix, all text:**
  - the equality evidence covers 2026 only, and its re-check has no consequence;
  - the 23 Mar 2020 kind of error is not guaranteed to void;
  - a failed window can permanently damage the next session's row.
- **A re-check needs only the story file.**

## Addendum 1 (15 Oct 2026): a correction to my own text

**I withdraw "The A16 finding is correct by construction"** (section "Other checks").
- **What I said.** I wrote that A16's NSE-open condition "fires on every session". My only grounds were step 0's "40 of
  40" and the mechanism, not my own data.
- **Contrary evidence.** The orchestrator reports that the A16 builder's 6-session check found the 09:15 open equal to
  NSE's open on 2 of 6 sessions. The 09:14 pre-open close matched on 6 of 6.
- **Why the mechanism does not settle it.** The first trade after the auction can equal the auction price, so "every
  session" does not follow from it.

**Status of step 0's claims:**
- "differs on 40 of 40" and "fires on every session": **unverified, conflicting evidence**;
- "the pre-open close equals NSE's open": consistent in both samples, 40 of 40 and 6 of 6 (some evidence).

**What changes:**
- **Minor 4 now also asks** that step 0's open counts be rechecked and corrected, with the session list, before the
  re-check. The A16 report must state the reproduced figure, not 40/40.
- **The verdict is unchanged: FAIL.** None of the three should-fix findings depends on that count, because A16b's void
  rule does not use the 09:15-vs-NSE open.

## Addendum 2 (15 Oct 2026): revision at d7894440d8d3d7f466da676ffc701864594c7b00 (d7bfd66..d789444, story file only)

| Judge 122 finding | Status | Check |
|---|---|---|
| SF1: equality evidence and its stop rule | **MET (decision 55)** | Every session with 25 candles is checked against its own 1-minute candles at all 26 marks. A difference above 0.05 voids the session (`candle_mismatch:<marks>`). There is never a fall-back. Paced: one call at a time, at least 0.5 s between starts; 3 failures in a row stop the run. Tests at 0.05 / 0.06, empty, a missing minute, pacing. Step 0 now says the 3 days are all 2026 |
| SF2: candle high and low against NSE's range | MET | The void covers the 26 levels and the 25 used candles' highs and lows. There is a 23 Mar 2020-shaped test. The cost, 0 of 40, is stated (some evidence) |
| SF3: order after a failed window | MET as written, **but see new should-fix 1** | Deferred, named, exit 1. The session after 10 Oct 2025 gets a void overnight part and a computed intraday part. There is a test of a failed middle window then a resume |
| Minor 1: named cases | MET | Halt days, 24 Feb 2021, the 2024 specials, the two Groww holes and 10 Oct 2025, each with its expected `missing_candles:n`. The void share counts the short sessions and also lists them apart |
| Minor 2: one provenance function | MET (text) | `provenance()` moves to `fno/provenance.py`, and A17's table and verify import it. `global_cues/table.py` is in no freeze (I searched the manifests and JUDGE.md). In the code round I check that it is a pure move (the same body, A17's tests unchanged and green) and plant one mutation in the moved function that both A17's and A16b's tests must catch |
| Minor 3: G6 told | MET | Decision row 56 in response 113, plus an open item in response 122. I check that both exist in the code round |
| Minor 4: A16's NSE-open finding | MET | Recounted: 67 of 74 recent sessions differ, 7 within 0.05. The random sample was 40 of 40. The 40/40 is now limited to its sample and the correction is stated. The finding is recorded as decision 53, with the fix in A16d (judge D). This also settles my addendum 1 |
| Minor 5: per-window count | MET | Each window prints its candle count against 25 × sessions. Tested with a window one candle short |

**The orchestrator's question: are the 26 Sep 2025 and 29 Sep 2026 holes adequately marked as Groww's? YES.**
- They are labelled "reasoning only" with the evidence given: NSE's normal index-close file exists for both days, and
  the calendar has no disruption.
- The label is right. A normal close file does not by itself rule out an NSE trading interruption, so it is not strong
  evidence.
- Both sessions are void either way, so the label changes no row.

## New should-fix (text)

1. **A transient failure and a permanent absence are treated alike, and one of them blocks the series forever.**
   - **The cascade.** A session whose 1-minute answer arrives but lacks a needed minute is "not written ... `no_1m_check`,
     exit 1". By the Order rule, the next session is then deferred, because its previous session has no row. The one
     after that is deferred too, and so on.
     - If Groww simply has no such minute, a permanent 1-minute hole, every later run fetches the same answer, never
       writes that session, and defers **every session after it**.
     - The back-fill can never get past the first such hole, and every run exits 1 for ever.
     - Groww does have holes: the 15-minute holes of 26 Sep 2025 and 29 Sep 2026. So a 1-minute hole on a day with all
       25 15-minute candles is plausible (reasoning only; not measured).
   - **The same class in the NSE check.** "NSE's file missing **or unreadable**: void `nse_unchecked`" writes a
     write-once void row on what may be a transient Drive read error. When Drive recovers, the inputs differ and the row
     is refused. That is the very defect should-fix 3 removed for Groww windows.
   - **Expected fix:** separate the two cases.
     - **Transient** (a call or read failed, no answer): not written, deferred, exit 1, retried next run.
     - **Permanent** (an answer was received and archived, but the data is not there: the 1-minute answer lacks the
       minute, or NSE's archive has no file for that day): a **void row**, `no_1m_check` or `nse_unchecked`. It is
       written once, named, and listed apart. The next session then gets a void overnight part, as after 10 Oct 2025.
       This is still never a fall-back: the session is void, not trusted.
   - **Tests:**
     - a 1-minute answer missing one needed minute: void row, and the next session is written with a void overnight
       part;
     - a failing 1-minute call: deferred, then written on resume;
     - an NSE file absent: void row;
     - an NSE read error: deferred.

## Minor (text)

1. Name where `NseSessionCalendar.next_open` comes from for A16b. It lives in `fno/global_cues/cue_calendars.py`. Say
   whether A16b imports it from there or it moves beside `provenance()`, so the intraday package does not depend on the
   global-cues package for a calendar.

### Verdict: FAIL for d7894440d8d3d7f466da676ffc701864594c7b00 (story text)

- **All 3 earlier should-fix and all 5 minors are met.**
- **One new should-fix:** separating transient from permanent outcomes. It was caused by combining the new 1-minute
  check with the new Order rule, and it would stop the back-fill at the first permanent 1-minute hole.
- **A re-check needs only the story file.**
