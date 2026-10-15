# Response 108: story A16, 15-minute quote recorder (Groww)

**Branch:** `story/a16-groww-15min` · **Lane:** 1 (new story; Groww, Drive, Slack alerts) · **Story text:**
`docs/stories/A16-intraday-quote-recorder.md` · **Builder:** a builder session for the orchestrator.

## Part 1: story text for the judge's check (quality rule 1)

This commit holds the story text alone (scope, definitions, 15 acceptance criteria, gap list, test plan, the routine
prompt proposal) and step 0's feasibility results. No code is in this commit.

**Step 0, what was measured (live, read-only, 15 Oct 2026, pre-market 07:01-07:07 IST):** strong evidence for what it
covers (direct reads), some evidence for timings (one morning, books empty before the open).
- Groww has NIFTY 50 15-minute candles from 1 Jan 2020 (none earlier; 1,685 of 1,686 calendar sessions to 14 Oct 2026;
  10 Oct 2025 missing; four short days besides muhurat, two of them Groww's own holes on 26 Sep 2025 and 29 Sep 2026).
- A full snapshot is: index quote, near future quote, two chains (1.0-1.1 s each, 108 contracts within 6% per expiry),
  then 216 contract quotes. Sequential quotes take 0.79 s each (170 s in all); Groww started failing near 10 requests a
  second, so the recorder paces at 5 a second with 4 workers: about 45-50 s a snapshot.
- The index quote's `last_trade_time` was empty before the open. Whether Groww fills it during the session decides how
  staleness is measured. **This is the one open feasibility question**; the in-session check after 09:15 IST will be
  added to the story as an amendment, and if Groww gives no index time, the story will say what replaces it (a
  candidate measured then: the latest 1-minute index candle's time) before any criterion depends on it.

**Points the judge may want to weigh (my own doubts, stated plainly):**
1. Scheduled tasks here have a minimum interval of about one hour, so the routine proposal is an hourly routine running
   a 55-minute loop (seven fires a session-day), not 26 fires. Untested as a routine: reasoning only.
2. The heartbeat checker is not truly independent: it can only run as another Claude routine (same platform). Said in
   the story; a real second host is a later decision.
3. The near future's symbol form (`NIFTY26OCTFUT`) was checked for October 2026 only.
4. `fno/storage/wiring.py` is at 345 of 350 lines, so A16's store is built in its own composition root from
   `build_owner_drive` instead of in the storage root that design 2.1 names.
5. The candle back-fill (2020-2026) is left out on purpose and proposed as A16b: a candle-close RV is a different
   measure from a quote-snapshot RV, and protocol v4 (G6) should decide whether and how to use it.
6. The CLAUDE.md gate `pip install -r requirements-groww.txt` fails in this container (the SDK's old dependencies
   `clint` and `args` do not build); I installed `growwapi` with `--no-deps` plus its other dependencies. The tests do
   not need the SDK (fakes).

## Part 2: build claims

To follow at the code SHA: criterion-by-criterion evidence, broken-code proofs, the self-review agents' findings and a
real dry-run sample (counts and timings only).
