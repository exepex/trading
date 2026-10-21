# G13b. NIFTY and BANKNIFTY price ranges at N+0, N+1 and N+3, issued three times a day

**Repository:** trading · **Lane:** 1 (new story; forecast and evaluation records) · **Judge:** E · **Builder:**
session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/g13b-price-ranges` · **Depends on:** G13 (`fno/price_distribution/`, at judge 310's re-check) · **Status:** story
text for the judge (no code)

**Description.** As the owner, I want an honest price range for NIFTY and BANKNIFTY for today's close, the next
session's close and the third session's close, issued before the open, after the first 15 minutes and after the close,
each sealed before its outcome and scored against simple baselines, so that I can judge in trading days whether the
ranges deserve trust.

**Context and why.**
- Owner, 21 Oct 2026 (`docs/DESK_DECISIONS.md`, "Focus: an honest N+1 and N+3 forecasting engine"):
  - ranges as 5/25/50/75/95% quantiles, with the direction derived;
  - NIFTY and BANKNIFTY at N+0 close, N+1 and N+3;
  - three issues a day: 08:45 pre-open, 09:30 after the first 15 minutes, 15:45 after the close;
  - each sealed before its outcome and scored against baselines (no change, option-implied range) with proper scores;
  - "trust is judged in trading days (about 60 for calibration, 6-12 months for a trading edge), not positions";
  - reports go to FL1 (the lab and reports, O11's builder); runs at fixed times are Claude routines.
- The orchestrator's brief (21 Oct):
  - forecasters: option-implied (G13's), realised-vol baselines and a "no change" baseline, plus slots for the v4
    forecasters and the AI books;
  - scores: pinball/CRPS and band coverage, sealed before the outcome (a late record is never scored);
  - "Keep it simple; reuse G4/G8 scoring and your back-fill."
- What is already true (strong evidence, DESK row above): no live forecaster has beaten its base rate yet, and
  next-day index direction is near a coin flip. G13's end-of-day back-fill (response 262, exploratory) found the
  implied range the best of three at every horizon, with the 90% band holding the close 88-91% of the time. That is
  the one lead this story turns into a live, sealed test.

**Does this change a trade or stop decision?** Not directly. Its rows are evidence for the owner and inputs for FL1's
paper positions. Nothing here sizes, enters or blocks a trade.

## What the data allows (checked on main 3216f937)

| Need | State | Evidence |
|---|---|---|
| NIFTY 3 pm chain (two monthlies, bid/ask) | daily since 14 Oct | A4; G13's `SnapshotChains` |
| BANKNIFTY 3 pm chain | daily since 19 Oct | A4c `fno/quotes/indices.py`; same reader, stem `banknifty` |
| NIFTY daily closes | 2017 on | `research/data/nifty-panel/warmup_closes.csv` |
| BANKNIFTY daily closes | **no table**; the closing value sits in every archived NSE index-close file ("Nifty Bank") | `fno/fo_bhavcopy.py:66 read_index_closes`; `storage.wiring.build_index_close_files` (the files warmup_closes is built from) |
| NIFTY 09:15 and 09:30 marks (spot, near future, chain) | A16, NIFTY only | `fno/intraday/`; port `observer.MarkObserver.after_mark` (LM1 uses it) |
| BANKNIFTY intraday marks | **none** | A16 records NIFTY only |
| Overnight share of NIFTY's daily variance | **39.3%** of 1,469 sessions 2020-2025 (28% in 2024 to 45% in 2022) | A16b candle RV `research/data/intraday/rv-candle/` (`rv_overnight / rv_session`, summed); measured for this text |
| US closes (S&P 500, Nasdaq 100), first seen before 09:15 | A17, values in Drive only | `research/data/global-cues/README.md` |
| GIFT Nifty, NSE pre-open | **not built** (A22) | DESK row of 21 Oct |
| Proper scores | G13's pinball/QS, G4's Brier | `fno/price_distribution/scoring.py`, `fno/forecast_scoring/scores.py` |
| Push time of a committed file (sealing evidence) | yes | `fno/health/evidence.py:46 file_pushed_at` (GitHub's activity log, never a commit date) |

## Design

New package `fno/price_ranges/` (each file well under 350 lines), composition root `fno/price_ranges/wiring.py`. It
reuses G13's chain sources, distribution, forecaster arithmetic, Drive store and scoring functions by import. It
edits no G13 file except to make a G13 function public if needed, and edits no frozen file.

### 1. Issues, horizons and the reference price

- **Issues:** `0845`, `0930`, `1545` IST on each regular session `d`. An issue's inputs are only what was first seen
  before its time. Each issue is one write-once record per underlying.
- **Horizons:** `N0` = `d`'s close (08:45 and 09:30 only; at 15:45 it is known). `N1` and `N3` = the close of the
  first and third regular session after `d` (A7 calendar; past the calendar's end: `not_eligible`).
- **Reference price `S_ref`:**
  - 08:45: the last close (`d-1`). When A22 lands, its GIFT Nifty level becomes a second, labelled method version,
    never a silent change.
  - 09:30: A16's 09:30 NIFTY spot.
  - 15:45: `d`'s close, from the committed closes or NSE's index-close file of `d`. If it is not first seen by 15:45,
    the issue is `missing` (reason given), never a 15:00 price relabelled.
- **Time in session units `τ`** (variance accrues per session; reasoning only, one number measured):
  - from a close to the k-th close after it: `τ = k`;
  - from 09:30 to that day's close: `τ = (1 - 0.393) x 360/375 = 0.583`. The overnight part is spent by 09:30, and the
    intraday part is taken as even in time; the first 15 minutes' extra variance is not modelled. The constant 0.393
    is the measured overnight share above, frozen in the method;
  - N1 from 09:30 is `0.583 + 1`, and N3 is `0.583 + 3`.

### 2. Forecasters (ids in `fno/price_ranges/constants.py`)

- **`implied`** (G13's distribution).
  - The chain is the latest captured before the issue: `d-1`'s 3 pm chain at 08:45 and 09:30, `d`'s at 15:45.
  - The distribution of the expiry with at least the horizon's remaining sessions is re-centred and scaled exactly as
    G13's `h1`/`h5`: centring by `τ/n`, spread around the median by `sqrt(τ/n)`, with `n` the sessions from the
    chain's day to that expiry and `τ` counted from the chain's time.
  - At 09:30 the 15 minutes since the open are already spent: the 09:30 spot replaces `S_ref`, and `τ` is what is left
    (reasoning only: the chain is the day before's).
- **`rv20`:** lognormal, zero log drift, at the B1 realised volatility of the last 20 regular closes before `d`, over
  `τ`.
- **`hist750`:** the empirical quantiles of the `k`-session close-to-close log returns in the last 750 sessions.
  - Issued only where the target is a whole number of sessions from a close (08:45 and 15:45).
  - At 09:30 it is `not_eligible` (no intraday history baseline in v1; said in every row's reason).
- **`no_change`** (the coin-flip yardstick): every quantile at `S_ref`, `P(up) = 0.5`.
  - It is scored by the quantile score (twice the mean pinball, which for a point equals its absolute error) and by
    Brier.
  - Band coverage is not defined for it and is printed as "n/a".
- **Slots, no rows and no start date:**
  - the v4 rule forecasters (G7's ids, when a v4 story adds price ranges);
  - `book2_hybrid` and `book3_ai` (`fno/constants.py`);
  - the story that fills a slot sets its start (G11's owner, 16 Oct).

### 3. Each row

- **Fields:**
  - identity: `underlying, day, issue, issued_at, forecaster, horizon, target_day`;
  - the range: `tau, s_ref`, the quantiles `q05 q25 q50 q75 q95` (levels and log returns), and `p_up`;
  - status: `status` (ok, missing, not_eligible), `reason`, `label` (live, backfill_eod, backfill_3pm);
  - audit: `method_version, method_sha256, inputs_sha256`.
- **`p_up`** is `P(close at target > S_ref)`:
  - `implied`: `1 - CDF(S_ref)` on the scaled distribution;
  - `rv20`: 0.5 by construction (zero log drift; said);
  - `hist750`: the share of positive returns;
  - `no_change`: 0.5.
- **Record check:** quantiles strictly increasing, except `no_change`, where all five are equal.

### 4. Sealing (owner, 21 Oct: "sealed before its outcome")

- A live record is written to Drive, write-once (O9), and its receipt is committed and pushed by the issuing run.
- **Sealed:** the receipt's first push to `origin/main` (GitHub's activity log, through O8's `Evidence.file_pushed_at`)
  is at or before the issue's deadline: 09:15 for 08:45, 09:45 for 09:30, 09:15 of the next session for 15:45.
- The scorer scores a live row only when sealed. An unsealed or late live row is counted as `late` and never scored.
  It is never relabelled.
- Back-fill rows are labelled `backfill_*` and scored apart. They never count as live evidence.

### 5. Scores (reusing G13's and G4's code)

Per (label, underlying, issue, horizon, forecaster):
- **QS** over the five levels (`(2/5) x Σ pinball`, log units). With 5 levels it is an even coarser CRPS
  approximation, said in the report.
- **Coverage:** the 50% band (q25-q75) and the 90% band (q05-q95), against their nominal levels.
- **Brier** of `p_up` against the up/down outcome. A close equal to `S_ref` counts as not up.
- **Comparisons:**
  - `implied` against `rv20`, `hist750` and `no_change`, by G4's block bootstrap (imported; the seed derived from the
    comparison's key, as in G13);
  - descriptive only, no protocol, no claim;
  - the report prints the number of sealed live trading days next to every number, and the owner's 60-day
    calibration mark.

### 6. Back-fill

- **NIFTY, end of day 2019 on** (G13's panel source), `backfill_eod`, 08:45 and 15:45 issues only. The 15:45 back-fill
  uses `d`'s close as `S_ref`. The 08:45 back-fill uses `d-1`'s close and chain: the same as 15:45 of `d-1`, with N0 as
  its first horizon.
- **NIFTY 09:30 back-fill:** from A16b's 15-minute candles (the 09:30 level, 2020 on) with the `d-1` panel chain,
  `backfill_candle`. The candle archive is read through the Drive cache.
- **BANKNIFTY:**
  - closes: a derived close table from the archived index-close files (2017 on), written to Drive with its receipt
    (O9), never committed as values;
  - implied back-fill: from A4c's chains, 19 Oct on (`backfill_3pm`);
  - end-of-day implied back-fill from NSE's F&O files: **part c, later** (a bhavcopy chain source; question 3);
  - 09:30: none (question 2).

### 7. Runs and failures

- **Commands:** `python -m fno pricerange issue --at {0845,0930,1545} [--day D] --live`, plus `backfill`, `score` and
  `report`.
- **Exits:** the same contract as G13's:
  - a written day with problems exits 1 (`written with problems: ...`);
  - nothing captured anywhere prints `nothing written: ...` and exits 0;
  - an unreadable input writes no file, so a rerun can still issue;
  - a rerun keeps stored problems (judge 310);
  - the command never alerts itself; the run hosting it does (question 1).
- **Where each issue runs (question 1):**
  - 15:45: O1's daily run, a step after G13's `price_distribution`;
  - 09:30: A16's `MarkObserver` at the 09:30 mark (its receipts committed by A16's committer, which already pushes
    every mark);
  - 08:45: a Claude routine, or A22's pre-open job once it exists.
  - G13b never creates or edits a schedule.
- **FL1 output:** one JSON report per issue (`pricerange report`) with the rows, the inputs' times and the running
  scores, in the record format agreed with O11's builder (session_01FWkBH4zNAEFSEpjUzVEgnd, asked 21 Oct; their
  answer is quoted here before code).
- G13b writes nothing to Slack: the #fno-forecast and #fno-intraday posts are FL1's.

## Acceptance criteria (each with a test: positive, negative, boundary, empty)

1. **Point in time:** each issue reads only inputs first seen before its time:
   - a planted later chain, close, mark or US close changes nothing;
   - at 08:45 the chain is `d-1`'s;
   - at 15:45 a close not yet seen makes the issue `missing`.
2. **Horizons and τ:**
   - N0/N1/N3 targets on the A7 calendar, with a holiday inside the range;
   - τ = 0.583 / 1.583 / 3.583 at 09:30, and 1 / 2 / 4 at 08:45 from `d-1`'s close;
   - N0 is absent at 15:45;
   - the calendar's end is `not_eligible`.
3. **Forecasters:**
   - `implied` equals G13's scaled distribution at the hand-computed `τ/n`;
   - `rv20` and `hist750` match hand values;
   - `hist750` is `not_eligible` at 09:30;
   - `no_change` quantiles all equal `S_ref` and `p_up = 0.5`;
   - `p_up` of `implied` equals `1 - CDF(S_ref)` by hand;
   - the AI and v4 slots are accepted ids with no rows.
4. **Record check:**
   - non-increasing quantiles are refused, except `no_change`'s equal ones;
   - an unknown forecaster, horizon or issue is refused.
5. **Sealing:**
   - a live row pushed at the deadline is sealed; one second after it is `late` and not scored;
   - a receipt with no push evidence is `late` (never assumed sealed);
   - a back-fill row is never counted live.
6. **Scores:**
   - QS, coverage and Brier match hand values (an outcome below, inside, above and at a quantile; an outcome equal to
     `S_ref` is not up);
   - `no_change`'s QS equals its absolute log error;
   - comparisons equal G4's bootstrap called directly;
   - under 40 paired days is "not tested";
   - labels, issues and underlyings are never pooled.
7. **BANKNIFTY closes:**
   - the derived table matches the index-close files' "Nifty Bank" value on three hand-checked days;
   - a missing file is a counted gap, never filled.
8. **Back-fill:**
   - labels as section 6;
   - stops before each issue's first live day;
   - byte-identical on a rerun, and a new path for new inputs (G13's rule);
   - a build failure skips its day, counted.
9. **Failures and exits:** each case of section 7, as G13's criteria 9-12, including the rerun of a problem day.
10. **No frozen file changes, no Slack post, no schedule created:** the existing freeze tests pass unedited.
11. **Real output sample:**
    - the claims file shows the 16 Oct NIFTY issues rebuilt by the committed code as a dry run, and the first
      end-of-day back-fill scores, labelled exploratory;
    - BANKNIFTY's from A4c's first days.

## Gap list

| Requirement (source) | Covered by |
|---|---|
| 5/25/50/75/95% quantiles; direction derived (DESK 21 Oct) | design 3, criteria 3-4 |
| NIFTY and BANKNIFTY (DESK 21 Oct) | design 1-6, criterion 7 |
| N+0, N+1, N+3 (DESK 21 Oct; brief) | design 1, criterion 2 |
| 08:45, 09:30, 15:45 issues with their inputs (brief) | design 1-2, criterion 1, question 1 |
| GIFT Nifty and pre-open once A22 lands (brief) | design 1 (a new method version), question 4 |
| A17 US closes as an input (brief) | **Out of v1's forecasters, said:** none of the four uses them yet. They are recorded in each 08:45 record's inputs, and a US-gap-adjusted `implied` is a later version. Reasoning only: an untested adjustment is a guess |
| Option-implied, realised-vol and no-change forecasters; v4 and AI slots (brief) | design 2, criterion 3 |
| Pinball/CRPS and band coverage (brief) | design 5, criterion 6 |
| Sealed before the outcome; a late record never scored (brief) | design 4, criterion 5 |
| Reuse G4/G8 scoring and G13's back-fill (brief) | design 5-6 (G4's bootstrap and Brier, G13's QS and sources) |
| Report-ready output for FL1, format agreed (brief) | design 7, question 5 |
| Every data file write-once in Drive with a receipt (owner, 16 Oct) | design 4, 6 |
| Failures alerted and recorded (owner, 16 Oct) | design 7, criterion 9 |
| **Out:** paper positions, Slack posts, the lab | FL1's |
| **Out:** top 10 or 20 stock positions (DESK 21 Oct) | FL1's ranking; per-stock ranges would need per-stock chains (A4's all-F&O step, NF 8a) |
| **Out:** BANKNIFTY end-of-day implied back-fill | part c, question 3 |

## Questions (recommendation first)

1. **Where each issue runs** (orchestrator, with O1's, A16's and A22's owners):
   - 15:45 as an O1 step after `price_distribution`;
   - 09:30 as an A16 `MarkObserver`;
   - 08:45 as A22's pre-open job's step when A22 lands, and until then a Claude routine the owner creates.
   - Reasoning only: each issue rides a run that already exists at that time.
2. **BANKNIFTY at 09:30:** A16 records NIFTY only. Recommended: BANKNIFTY's 09:30 rows are `not_eligible` ("no
   BANKNIFTY intraday mark") until A16's owner adds a BANKNIFTY spot read at 09:30 (one quote call a mark). Ask A16's
   owner.
3. **BANKNIFTY end-of-day back-fill (part c):** recommended later, after the live rows start. Until then BANKNIFTY's
   evidence is live and 3 pm back-fill only, a few days at first. Said plainly: BANKNIFTY will have no back-fill
   history for months unless part c is built.
4. **The 08:45 reference after A22:** recommended both, as two method versions (`S_ref` = last close, and = the GIFT
   Nifty implied level), scored apart. The owner then sees whether GIFT helps, measured, not assumed.
5. **FL1's record format:** proposed to O11's builder on 21 Oct (one JSON per underlying, issue and day; fields as
   section 3; scores apart). Their answer is quoted here before code.
