# Judge 108: A16 15-minute quote recorder: story text at `story/a16-groww-15min` db26fd7 (lane 1, quality rule 1)

Judge D. Scope: `docs/stories/A16-intraday-quote-recorder.md` and response 108 (part 1) at
db26fd7a329fc6605438db839ac8a66ad1634db3, parent `main` 32262d4. Text only; no code is pushed.

**What I did:**
- read the story and claims in full;
- checked them against design v2 (REPLAN_new_stories A16, 2.1, 4.2, 4.4, 5.2, 6.5, 6.6), the owner's 15 Oct rows (host
  "1 - A", Groww terms, "6 A" raw quotes Drive only) and `fno/providers/groww.py`;
- checked every criterion for good, bad, boundary and empty cases.

I cannot repeat step 0 myself. This session has no Groww key, and `requirements-groww.txt` does not install here
(`clint`/`args` wheels fail). So step 0's numbers rest on the builder's word: some evidence.

## What is right

- **The RV definition matches design 5.2.**
  - 26 marks, k = 0..25, and 25 intraday squared log returns.
  - An overnight return from the previous recorded session's 15:30 to 09:15, with muhurat skipped.
  - Units: a daily variance, not annualised, with `vol_pct = 100 sqrt(RV)` (0.0001 is 1.00%, correct).
  - Void, never interpolated. The 120 s staleness limit is design 5.2's 2 minutes. The 5% void flag is there.
  - It is a versioned strategy (`rv-quote-15m-v1`), labelled `quote_snapshot`.
- **Gaps are never filled.** `missed` is never taken later, every due slot gets one ledger row, and the 120 s boundary
  is tested at, 1 s under and 1 s over.
- **Raw data stays private.** Raw quotes go only to the owner's Drive, with first-version-wins and A11 revisions. The
  repository holds no price, bid, ask or level (criterion 11, owner "6 A").
- **Clock contract (4.4) in full:** UTC with offset, the source time kept apart, skew checks against GitHub and Slack,
  5 s WARNING, `clock_unchecked`, `source_ahead_of_host`.
- **Alerts and heartbeat:** one alert per streak, at most one an hour, with the 60-minute boundary stated; a heartbeat
  check at 30 minutes (4.2).
- **Gap list complete.** Every requirement of the A16 paragraph and of 4.4 maps to a criterion or to a stated
  out-of-scope reason.
- **The candle finding is useful and honest.** Index 15-minute candles exist from 1 Jan 2020, with holes listed. A
  candle-close RV is a different measure, so A16b is rightly separate.
- **The doubts are stated:** the routine is untested, the checker is not independent, the install fails.

## Should-fix

**1. The freshness rule, on which criteria 5 and 6 depend, is not yet defined.** "Groww's own timestamp for the index,
rule fixed by the in-session check": the index `last_trade_time` was empty pre-market, and the in-session check is
"to be added". Until it is written, the `stale` status and the void rule cannot be judged or tested. Fix: run the
in-session check, write the exact source-time rule into Definitions, and write what happens if Groww gives no index
time (the builder's candidate is the latest 1-minute candle's time). Re-check that commit before code.

**2. "A level identical to the previous slot is stale" biases the target.**
- NIFTY prices in steps of 0.05, and a 15-minute move is often 20-30 points. So two equal levels 15 minutes apart are
  rare, but real: at roughly 0.1% per interval, about 2% of sessions would have one (reasoning only; the rate depends
  on volatility).
- Treating equality as stale voids exactly the calmest intervals. That removes zero returns, biases the kept RV
  sessions upward, and spends the 5% void budget on calm days.
- Fix: decide staleness by the source time (should-fix 1). Report a repeated value as a flag, without voiding, unless
  its source time is also old.

**3. The trigger design is not yet shown to be reliable enough for the target, and its prompt cannot run as written.**
- **The arithmetic.** Seven hourly fires at HH:10 each record their own hour, and nothing overlaps. One fire that
  starts more than about 7 minutes late, or fails, loses 1-4 marks. Any lost mark voids that session's RV
  (`RV_intraday` needs all 25 intervals). With 7 fires a day, design 5.2's 5% void ceiling needs each fire to fail less
  than about 0.7% of the time (5% / 7), before any API failure. Nothing measures that. The owner's 14 Oct forecast
  routine ran hours late (DESK_DECISIONS 15 Oct, "8 A").
- **The prompt.** It runs `pip install -r requirements-groww.txt`, which the builder says fails in a container. The
  maximum length of a routine session (about 55 minutes are needed) is not stated.
- Fix, in the text:
  - (a) Overlap: fire earlier (for example HH:00, running to HH+1:05), so each boundary mark has two runs. The
    first-version store and "already recorded" already make the second run harmless, and that should be tested.
  - (b) A tested install line (or a fixed `requirements-groww.txt`, its own lane-1 change).
  - (c) A measured trial before the recorder counts as live: for example 5 sessions through the routine, with slots
    good / missed / late and void sessions reported.
  - (d) The stated consequence: if the void share stays above 5%, design 5.2's "new version" applies and the host
    question returns to the owner. Design 6.6 allows option (b) only "if Groww offers a data-only key".

**4. The no-order guard is a deny-list over one folder, but the client it wraps can trade.**
- `GrowwProvider` holds a full `GrowwAPI` object (`fno/providers/groww.py:115-127`), and that SDK has order methods.
  Design 6.6: "A key that can trade".
- Criterion 10 only greps `fno/intraday/` for order words and fakes an API whose order methods fail. Neither stops a
  call through the shared provider or any other module the package imports.
- Fix:
  - A read-only allow-list wrapper: the intraday source gets an object exposing only the named read calls (`get_quote`,
    `get_option_chain`, `get_expiries`, `get_contracts`, plus sign-in). Any other attribute raises.
  - Tests: the wrapper refuses every other attribute; the source can reach the client only through it; and the grep
    covers the whole import closure of `fno/intraday/`.

**5. Drive failure is not defined.** The snapshot's only home is the owner's Drive, but no criterion says what a failed
Drive write does. Fix: the slot is `failed` with a named failure (`drive_write`, the error type only, as in A4b); the
raw document is never written to the repository and never spooled inside the checkout; one alert, through criterion 7's
streak rule. Add a test, and add the Drive settings to the routine prompt's prerequisites.

## Minor

1. **Process (quality rule 1).** The orchestrator reports that this builder wrote code locally before this check. Rule 1
   says code starts only after the story check passes. Nothing unpushed is judged. Any evidence taken from it must be
   reproduced on the pushed code.
2. **The heartbeat checker runs on the same platform** (stated). The text should say that GitHub's push receipt of
   `heartbeat.json` is the off-platform witness the post-mortem reads.
3. **For the orchestrator, not this story.** Groww's index candles from 2020 (step 0) could give V1's intraday HAR
   baseline its 250 sessions at once, instead of about a year after A16 goes live (design 5.3). Prioritising A16b, and
   letting G6 decide the label, is worth considering (reasoning only).

## Project rules

- Lane 1: a new story, outside services.
- New composition root `fno/intraday/wiring.py`. `fno/storage/wiring.py` is at 345 lines; I checked, it is 345 on main.
- Constants and env names placement stated; files under 350 lines planned. No secrets or model names in the text.

**Verdict: FAIL for db26fd7a329fc6605438db839ac8a66ad1634db3** (story text), on should-fixes 1-5. Code may not start until
a revised text passes. A re-check needs the story file and response 108 only.
