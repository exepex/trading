# G13b. NIFTY and BANKNIFTY price ranges, and every contract valued at end of day

**Repository:** trading · **Lane:** 1 (new story; forecast and evaluation records) · **Judge:** E · **Builder:**
session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/g13b-price-ranges` · **Depends on:** G13 (`fno/price_distribution/`; judge 310.1 PASS) · **Status:** story text
for the judge. Revision 2: the owner's 21 Oct scope and phasing, FL1's and G7's agreements (judge 406.1 PASS).
Revision 3: `S_ref` at 15:45 is the 3 pm chain's spot, because the official close is not out yet; judge 406's two
minors are written in; the scope freeze (DESK 21 Oct) builds part A only. Revision 4 (the build's self-review,
`reviews/claude/response_290_g13b-price-ranges.md`): the text now says what the code does in A1-A8 (implied's share,
regular sessions only, the bhavcopy's three nearest expiries and settlement, seals stored once, the close table's
rescan, back-fill dedupe, scores per row and by method, the scores file's name, FL1's tail rule per judge 403).

**Description.** As the owner, I want:
- an honest price range for NIFTY's and BANKNIFTY's next-session and third-session close after each day's close, and
  later one before the open;
- every NIFTY and BANKNIFTY contract valued at the end of the day;
- each forecast sealed before its outcome and scored against simple baselines.

Then I can judge in trading days whether the ranges deserve trust, and the lab can price its paper positions.

## Context and why

**Owner, 21 Oct 2026** (`docs/DESK_DECISIONS.md`):
- **"Focus: an honest N+1 and N+3 forecasting engine":**
  - ranges as 5/25/50/75/95% quantiles, with the direction derived;
  - NIFTY and BANKNIFTY at N+0, N+1 and N+3;
  - sealed before the outcome and scored against baselines (no change, option-implied) with proper scores;
  - trust is judged in trading days, about 60 for calibration.
- **"Lab universe, report times and phasing":**
  - every NIFTY and BANKNIFTY contract (all expiries, calls, puts, futures) is tracked and scored at end of day from
    NSE's bhavcopy;
  - reports at 09:15 (the pre-open forecast from NSE's 09:00-09:08 pre-open price, GIFT Nifty, US closes and
    yesterday's chain) and 15:45 (the match report and the next-day forecast);
  - phase 1, about 28-30 Oct, is the 15:45 report; phase 2, about 3-5 Nov, is the 09:15 report (needs A22);
  - BANKNIFTY has had monthly options only since SEBI's Nov 2024 rule.

**Orchestrator's answers (21 Oct):**
- 15:45 is an O1 step after G13's `price_distribution`; there is no 09:15 issue until A22 is live.
- A separate 09:30 issue is optional, "only if it's cheap and scored apart".
- BANKNIFTY's intraday marks belong to A16's builder.
- BANKNIFTY's end-of-day back-fill from NSE's F&O files comes into phase 1 if it is cheap: "years of exploratory
  evidence for both instruments help the owner judge sooner".
- A GIFT Nifty reference is a second version, scored apart.

**Agreements:**
- **FL1's builder (21 Oct)** reads G13b through a reader port, never paths. It needs:
  - `sealed_at` beside `issued_at`;
  - an `Outcomes.close` that both FL1 and G13b use;
  - its scores read and never recomputed;
  - `no_change`'s width defined.
- **G7's builder (21 Oct):** one scorer per question (G13b never re-scores a v4 record); G7's methods are shared by
  import only; an `ewma_t4` range forecaster; a reported, unscored P(|r| >= 2%) line beside V6a.

**Evidence so far, said plainly:**
- No live forecaster has beaten its base rate yet, and next-day index direction is near a coin flip (strong).
- G13's NIFTY end-of-day back-fill (response 262, exploratory) found the implied range the best of three at every
  horizon. Its 90% band held the close 88-91% of the time. That is the one lead this story turns into a sealed live
  test.

**Does this change a trade or stop decision?** Not directly. The rows are evidence for the owner and inputs for FL1's
paper positions. Nothing here sizes, enters or blocks a trade.

## What the data allows (checked on main 3216f937)

| Need | State | Evidence |
|---|---|---|
| NIFTY / BANKNIFTY 3 pm chains (two nearest monthlies, bid/ask) | since 14 Oct / 19 Oct | A4, A4c; G13's `SnapshotChains` |
| Every NIFTY and BANKNIFTY contract at end of day (close, settlement, OI, volume, underlying) | NSE's daily F&O file, archived: legacy format to 5 Jul 2024, UDiFF from Jan 2024 | `fno/fo_bhavcopy.py:137 read_fo_file`; `storage.wiring.build_nse_fo_library`, `build_nse_legacy_fo_library` |
| NIFTY / BANKNIFTY official closes | NIFTY in `warmup_closes.csv`; BANKNIFTY in every archived index-close file ("Nifty Bank"), no table yet | `fo_bhavcopy.INDEX_NAMES`, `read_index_closes`; `storage.wiring.build_index_close_files` |
| Overnight share of NIFTY's daily variance | **39.3%** of 1,469 sessions 2020-2025 (28% in 2024 to 45% in 2022) | A16b candle RV `research/data/intraday/rv-candle/` (summed `rv_overnight / rv_session`), measured for this text |
| EWMA one-session variance | `Ewma.variance(d)`: the last session before `d` | `fno/forecast_v4_rules/baselines.py:55` (imported, never edited) |
| NSE pre-open price, GIFT Nifty | **not built** (A22) | phase 2 |
| Push time of a committed file | GitHub's activity log, never a commit date | `fno/health/evidence.py:46 file_pushed_at` (O8) |
| Proper scores | G13's pinball/QS, G4's Brier and block bootstrap | `fno/price_distribution/scoring.py`, `fno/forecast_scoring/` |

## Design

**Package layout.**
- New package `fno/price_ranges/` (each file well under 350 lines), composition root `fno/price_ranges/wiring.py`.
- Reused by import: G13's chain sources, distribution, forecaster arithmetic, Drive store and scoring functions;
  G7's `Ewma`; O8's `Evidence`.
- No G13, G7 or frozen file is edited. A G13 helper that must become public is a one-line change, named in the claims.

### Part A (phase 1): the 15:45 ranges, sealed and scored

**A1. Issue, horizons, reference.**
- **Issue:** `1545` on each regular session `d` (a special or muhurat session is not issued and not back-filled), for `NIFTY` and `BANKNIFTY`. The issue enum also holds `0915`
  (part C) and `0930` (optional, not built; question 1), so records never change schema.
- **Horizons:** `N1` and `N3`, the close of the first and third regular session after `d` (A7 calendar; past the
  calendar's end: `not_eligible`). At 15:45 there is no `N0` row, because the day has closed.
- **`S_ref`** (revision 3: the official close is not out at 15:45). NSE's index-close file is archived in the evening:
  `warmup_closes.csv` rows land 17:29-20:43 UTC, i.e. 23:00-02:13 IST, 13-16 Oct (git log). So `S_ref` is the spot
  recorded with `d`'s canonical 3 pm chain:
  - NIFTY: A4's 14:55-15:10 capture;
  - BANKNIFTY: A4c's 15:01-15:13 capture.
  - The chain's time is kept as `s_ref_at`, and `S_ref` is synchronous with the chain the `implied` forecaster reads.
  - No chain means `missing`.
  - The outcome is still the official close (A4). The move from the capture to `d`'s close is part of every
    forecaster's uncertainty, through `τ`.
- **`τ`** (sessions of variance, reasoning only): from the capture to the k-th close after `d`,
  `τ = k + (1 - 0.393) x 30/375 = k + 0.049`.
  - 0.393 is the measured overnight share (A16b candles, 2020-2025).
  - 30 of the session's 375 minutes remain after about 15:00, and the intraday variance is taken as even in time.
  - The constant is frozen in the method and printed beside the coverage in every report (judge 406 minor 1).

**A2. Forecasters** (ids in `fno/price_ranges/constants.py`).
- **`implied`:** G13's distribution of `d`'s 3 pm chain.
  - The expiry is the shortest with at least `k` sessions left after `d`. Its log quantiles are re-centred and scaled
    as G13's `h1`/`h5`, with `share = (k + tail) / (n + tail)`: centring by `share`, spread around the median by
    `sqrt(share)`, re-referenced to `S_ref`. Live (`CAPTURE` basis) `tail = 0.049`, the rest of `d`'s session;
    end of day (`CLOSE` basis, `S_ref` = `d`'s close) `tail = 0`, so `share = k/n` exactly as G13.
  - The chain is 35 minutes older than `S_ref`: the scaling counts sessions from `d`'s close, and the 14:55-15:30
    move is in `S_ref` (reasoning only).
  - Back-fill uses `d`'s bhavcopy chain (A3).
- **`rv20`:** lognormal, zero log drift, at the B1 realised volatility of the last 20 regular closes before `d` (`d`'s
  close is not known at 15:45), over `τ`.
- **`hist750`:** the empirical quantiles of the `k`-session close-to-close log returns in the last 750 sessions before
  `d`, applied to `S_ref`. The small extra 0.049 is ignored (reasoning only; said).
- **`ewma_t4`** (G7's builder, 21 Oct): `X = s T / sqrt(2)` with `T ~ t(4)` and `s² = Ewma.variance(d)` (the last
  session before `d`), as v4's `v6_ewma_t4`, over `τ`.
  - N3 uses `sqrt(3) s` (the independence caveat of V6b, reasoning only).
  - t(4)'s quantile is in closed form: `t = sign(p - 1/2) x 2 sqrt(q - 1)`, `q = cos(arccos(sqrt(α))/3) / sqrt(α)`,
    `α = 4p(1-p)`.
- **`no_change`:** a point mass at `S_ref`: all five quantiles equal `S_ref`, and `P(up) = 0.5`.
  - It is scored by the quantile score (for a point, that is its absolute log error) and by Brier.
  - Its band coverage is reported "n/a", never 0% (FL1's request).
- **Slots, with no rows and no start date:** the v4 rule forecasters, `book2_hybrid` and `book3_ai`. The story that
  fills a slot sets its start (G11's owner, 16 Oct).

**A3. Rows and records.**
- **One record per (underlying, day, issue):** `data/price_ranges/v1/<label>/<YYYY>/<MM>/<underlying>_<day>_<issue>.json`
  in Drive, write-once (O9), with its receipt.
- **Header:** `schema, underlying, day, issue, issued_at, label` (live, backfill_eod, backfill_3pm),
  `method_version, method_sha256, inputs_sha256`, and `inputs` (the close, its file and first-seen time, the chain's
  snapshot id or bhavcopy file).
- **One row per (forecaster, horizon):**
  - `target_day, tau, s_ref`, the quantiles `q05 q25 q50 q75 q95` as levels and log returns, and `p_up`;
  - `status` (ok, missing, not_eligible) and `reason`.
- **`p_up = P(close at target > S_ref)`:**
  - `implied`: `1 - CDF(S_ref)` on the scaled distribution;
  - `rv20`: 0.5 by construction (zero log drift). Its Brier is therefore always 0.25, like `no_change`'s, and tests
    nothing about direction; the report says so (judge 406 minor 2);
  - `hist750`: the share of positive returns;
  - `ewma_t4`: 0.5 (symmetric);
  - `no_change`: 0.5.
  - Said plainly: only `implied` and `hist750` take a view on direction.
- **Record check:** quantiles strictly increasing, except `no_change`'s equal ones; unknown forecaster, horizon or
  issue refused.
- **Interpolation:** G13b publishes only the five quantiles. FL1 prices positions on them piecewise-linear inside
  5-95% and with anchored lognormal tails beyond them (judge 403, replacing the flat tails of revision 3). That is
  FL1's modelling choice, quoted here, not G13b's.
- **`p_big_move`** (implied only): `P(|log return| >= 2%)`, the 2% line in log terms, for G7's consistency line.

**A4. Outcomes.**
- `Outcomes.close(underlying, day)` is NSE's official index close: "Nifty 50" and "Nifty Bank" in the archived
  index-close file of that day, read through the raw archive.
- For NIFTY it equals `warmup_closes.csv`; a test checks they agree. A missing file is an unresolved outcome, never
  filled.
- BANKNIFTY's close history (2017 on) is derived once from the same files into Drive (O9), never committed as values.
  Each update rescans every regular session the table lacks, so a late-archived file fills its day; a new table file
  is named by its last day and row count, so the latest always sorts last.
- FL1 and G13b's scorer use this one reader (FL1's request).

**A5. Sealing** (owner: "sealed before its outcome").
- A live record's receipt is committed and pushed by O1's step.
- **`sealed_at`** is that receipt's first push to `origin/main`, from GitHub's activity log through O8's
  `Evidence.file_pushed_at`.
- Pushed-back on FL1's "git commit time": a commit date is set by the committer's clock and proves nothing. GitHub's
  receipt does.
- **Sealed:** `sealed_at` is at or before the issue's deadline: 09:15 of the next session for `1545`, 09:15 of `d`
  for `0915` (part C).
- An unsealed or late live row is counted as `late` and never scored; push evidence that is unavailable means `late`,
  never assumed sealed. Back-fill rows are never live evidence. The late count counts `ok` rows only.
- **Stored once:** GitHub's activity log reaches back one week, so each seal is read while it exists and kept as a
  write-once seal file (`data/price_ranges/v1/seals/...`, with its receipt). A known push time, on time or late, is
  final at once; unknown evidence is retried each day and, once the record is more than 7 days old, stored `late`.
  Readers use the stored seal. In a shallow clone the last 10 days of `main` are fetched first, because git's first
  commit adding a receipt is otherwise the clone's boundary commit.

**A6. Scores** (reusing G13's and G4's code). For each (label, underlying, issue, horizon, forecaster):
- **QS** over the five levels, `(2/5) x Σ pinball` in log units. That is a coarse CRPS approximation, said in the
  report.
- **Coverage** of the 50% band (q25-q75) and the 90% band (q05-q95).
- **Brier** of `p_up` against "close above `S_ref`" (equal is not up).
- **Per row too:** one score row per scored forecast row (label, underlying, issue, issue day, forecaster, horizon,
  target day, outcome close and log return, QS, inside 50%, inside 90%, Brier), for FL1 and audits.
- **Groups** add the method's SHA-256: two methods are never pooled.
- **Comparisons:**
  - `implied` against each baseline, by G4's block bootstrap (seed from the comparison's key, as G13);
  - descriptive only: no protocol, no claim;
  - every number printed next to its count of sealed live trading days and the owner's 60-day calibration mark.
- **G7's consistency line** (reported, never scored): `implied`'s N1 `P(|r| >= 2%)` beside v4's V6a forecast of the
  same day.
- **Scores files** go to `data/price_ranges/v1/scores/`, named by their IST making time (`YYYY-MM-DDTHHMMSS`).
  The scorer stores due seals first. FL1 reads them through the reader port and never recomputes
  them.

**A7. Back-fill** (the orchestrator's "if cheap"; it is, through one shared chain source).
- `BhavcopyChains` (a new `ChainSource`): every NIFTY or BANKNIFTY option of a day's archived F&O file, the three
  nearest expiries (as G13's chains).
  - It gives the same-expiry future's settlement price (`SttlmPric`, not its last trade) as the forward check.
  - Its quote filter is G13's `TradedCloseFilter` (traded that day, at least Rs 0.50).
  - It serves both the `backfill_eod` ranges (2019 on for NIFTY; BANKNIFTY from the first archived file it appears
    in) and part B.
- `backfill_3pm` from A4's and A4c's chains.
- G13's rules apply:
  - labelled and never pooled;
  - stops before the first live day;
  - byte-identical on a rerun, with a new path for new inputs;
  - a build failure skips its day, counted;
  - regular sessions only;
  - overlapping or rerun back-fill files count once per (label, method, underlying, day, issue): the file whose range
    ends latest wins.

**A8. Reader port for FL1.**
- `RangeForecasts.sealed(underlying, day, issue) -> SealedRanges | None`: the record, `sealed_at`, and `late` when it
  is not sealed.
- `RangeScores.latest()` returns the score files.
- `Outcomes.close` as above.
- All are read through the verified Drive cache; FL1 never builds a path.

**A9. Run and failures.**
- A close-table, seal or closes failure is contained: it is a problem line (exit 1), and the other underlying is still
  issued.
- **Step:** `python -m fno pricerange issue --at 1545 --day D --live`, as O1's step `price_ranges` after
  `price_distribution`, wired like G13's step (`Alerted(LiveFrom(CommandStep))`, `daily.live_from.price_ranges` null,
  G13b's receipts as its only pathspecs).
- **Exits:** as G13's.
  - A written day with problems: exit 1, `written with problems: ...`.
  - Nothing captured: `nothing written: ...`, exit 0.
  - An unreadable input writes no file.
  - A rerun keeps stored problems.
  - The command never alerts itself.
- **Commands:** `pricerange issue`, `backfill`, `closes` (BANKNIFTY's table by hand) and `score` (stores due seals,
  then writes the scores file and its report). The report is JSON for FL1, and its notes carry the honest headline
  (below).
- G13b posts nothing to Slack; FL1 owns #fno-forecast.

### Part B (stopped by the scope freeze, DESK 21 Oct: not phase 1's list): every NIFTY and BANKNIFTY contract valued at end of day

- **When:** for each session's archived F&O file, run by O1's 15:45 step once NSE has published it, else by the next
  run. The file's first-seen time is recorded. Its back-fill is the same path as A7.
- **Per contract** (every expiry, call, put and future of NIFTY and BANKNIFTY):
  - close, settlement, open interest and its change, volume, underlying value;
  - for options: IV at the settlement price and at the close (Black-76, `implied_vol.Black76`, on the same-expiry
    future's settlement; rate from config, labelled);
  - delta;
  - G13's smile value from that expiry's quadratic smile;
  - `smile_value - settlement` in rupees and IV points.
- **Per expiry:** G13's forward check (parity against the future), ATM IV, delta points, risk reversal and butterfly,
  and the implied distribution when the expiry has at least 8 CDF points.
- **Said plainly:** "fair value" is G13's smile value, a smoothness residual against the same day's prices, not a
  claim that a contract is cheap (G13's `smile_value_note`). Settlement prices of illiquid options are NSE's own
  estimates, so a large gap there says little.
- **Record:** `data/valuation_eod/v1/<YYYY>/<MM>/<underlying>_<day>.json`, write-once with a receipt, in the format
  agreed with FL1, read through a `EodValuations.for_day(underlying, day)` port.
- Scoring a valuation means FL1's paper positions marked at the next settlement. That is FL1's, not G13b's.

### Part C (phase 2, when A22 lands): the 09:15 pre-open issue

- **Issue `0915`:** `N0`, `N1` and `N3`.
- **`S_ref`:**
  - version `preopen`: NSE's 09:00-09:08 pre-open equilibrium price;
  - version `gift`: the GIFT Nifty level converted to a NIFTY level by A22's rule. It is NIFTY only and scored apart
    (orchestrator, Q4).
- **`τ`:** `N0 = (1 - 0.393) = 0.607` (the overnight move is already in the pre-open price), `N1 = 1.607`,
  `N3 = 3.607`.
  - The constant 0.393 is the measured overnight share above, frozen in the method.
  - BANKNIFTY uses NIFTY's share until its own candles are measured (reasoning only; said).
- **Forecasters:** as A2.
  - The chain is `d-1`'s 3 pm chain, scaled from its own time.
  - `hist750` is `not_eligible` for N0 (no pre-open history baseline in v1).
- **US closes:** recorded in the issue's inputs and used by no forecaster in v1. An untested adjustment is a guess; a
  US-gap version is a later, scored-apart method version.
- **Sealing:** a deadline of 09:15 of `d` (A5).

## Acceptance criteria (each with a test: positive, negative, boundary, empty)

**Part A**
1. **Point in time:** a 1545 issue reads only `d`'s canonical chain (its spot is `S_ref`, its time `s_ref_at`) and the
   closes before `d`. A planted `d` close, a later chain or a later close changes nothing; no chain makes the issue
   `missing`.
2. **Horizons:**
   - N1 and N3 targets on the A7 calendar, with a holiday inside the range;
   - τ = 1.049 and 3.049, and the report prints the 0.393 constant beside the coverage;
   - no N0 row at 1545;
   - the calendar's end is `not_eligible`.
3. **Forecasters:**
   - `implied` equals G13's scaled distribution at the hand-computed `k/n`;
   - `rv20` and `hist750` match hand values;
   - `ewma_t4` equals `s T/√2` with `s²` from G7's `Ewma` (imported) and the closed-form t(4) quantile;
   - the closed form matches tabled t(4) values to 1e-6 (2.1318 at 95%, 0.7407 at 75%);
   - `no_change` is a point mass with `p_up = 0.5`;
   - `implied`'s `p_up = 1 - CDF(S_ref)` by hand;
   - the AI and v4 slots are accepted ids with no rows.
4. **Record check:** strictly increasing quantiles except `no_change`; an unknown forecaster, horizon or issue is
   refused.
5. **Outcomes:**
   - `Outcomes.close` reads "Nifty 50" and "Nifty Bank" from the archived index-close file;
   - NIFTY agrees with `warmup_closes.csv` on every day both have;
   - a missing file is unresolved, never filled;
   - BANKNIFTY's derived table matches three hand-checked files.
6. **Sealing:**
   - a live row pushed at its deadline is sealed; one second later it is `late` and unscored;
   - no push evidence is `late`;
   - a back-fill row is never live;
   - `sealed_at` comes from GitHub's receipt, never a commit date.
7. **Scores:**
   - QS, coverage and Brier match hand values (an outcome below, inside, above and at a quantile; a close equal to
     `S_ref` is not up);
   - `no_change`'s QS equals its absolute log error and its coverage is "n/a";
   - comparisons equal G4's bootstrap called directly (under 40 paired days "not tested");
   - labels, issues and underlyings are never pooled;
   - the consistency line is in the report and in no score.
8. **Back-fill:**
   - `BhavcopyChains` gives a day's every NIFTY or BANKNIFTY option from a legacy-format and a UDiFF fixture file;
   - G13's back-fill rules hold;
   - BANKNIFTY back-fill rows exist from its first archived day.
9. **Reader port:** FL1's `sealed`, `latest` and `close` return the stored values through the Drive cache; a late
   record carries `late`; no path is built outside G13b.
10. **Step and failures:** as G13's criteria 9-12 (not live with a null date, failed with one alert, refused, a rerun
    of a problem day still fails), with only G13b's receipts committed.

**Part B**

11. **Every contract:**
    - a fixture F&O file with every expiry of NIFTY and BANKNIFTY (weeklies included for NIFTY) gives one valuation
      row per contract, futures included;
    - IV at settlement matches a hand Black-76 value;
    - a contract whose price has no IV in 1%-200% is kept with IV `None` and the reason;
    - an expiry with under 8 CDF points has no distribution, with its reason.
12. **Point in time:** a day's valuation reads only that day's file and the closes before it, and records the file's
    first-seen time.

**Part C** (judged with its code, after A22)

13. **0915 issue:**
    - `S_ref` from A22's pre-open price, and the `gift` version scored apart;
    - τ = 0.607 / 1.607 / 3.607;
    - the deadline is 09:15 of `d`;
    - US closes recorded and used by no forecaster.

**All parts**

14. No frozen file, G7 file or G13 file changes beyond a named public helper; no Slack post; no schedule created.
15. **Real output sample:**
    - the claims file shows a NIFTY and a BANKNIFTY 1545 record rebuilt by the committed code as a dry run;
    - one part B valuation of a real archived day;
    - the first end-of-day back-fill scores for both indices, labelled exploratory.

## Gap list

| Requirement (source) | Covered by |
|---|---|
| 5/25/50/75/95% quantiles; direction derived (DESK 21 Oct) | A2-A3, criteria 3-4 |
| NIFTY and BANKNIFTY (DESK 21 Oct) | A, B; criteria 5, 8, 11 |
| N+0, N+1, N+3 (DESK 21 Oct) | N1/N3 at 1545 (A1); N0 at 0915 (C) |
| 15:45 report first, 09:15 in phase 2 (DESK "Lab universe") | parts A and C |
| Every NIFTY and BANKNIFTY contract valued at end of day from the bhavcopy: fair value against settlement, IV by strike and expiry, OI and volume (DESK "Lab universe"; orchestrator 21 Oct) | part B, criteria 11-12 |
| Option-implied, realised-vol and no-change forecasters; v4 and AI slots (brief) | A2 (plus `ewma_t4`, G7's agreement) |
| Pinball/CRPS and band coverage; sealed before the outcome, a late record never scored (brief) | A5-A6, criteria 6-7 |
| Reuse G4/G8 scoring and G13's back-fill (brief) | A6-A7 (G8 scores no G13b row: G7's agreement) |
| FL1: reader port, `sealed_at`, issues, one outcome source, `no_change` width, scores read not recomputed (FL1's builder) | A3, A5, A6, A8, A4; criteria 5, 6, 9 |
| BANKNIFTY end-of-day back-fill in phase 1 if cheap (orchestrator Q3) | A7 |
| GIFT Nifty as a separately scored version (orchestrator Q4) | C |
| US closes in the 09:15 inputs (DESK "Lab universe") | C: recorded; no forecaster uses them in v1, said |
| Every data file write-once in Drive with a receipt (owner, 16 Oct) | A3, A4, B |
| Failures alerted and recorded (owner, 16 Oct) | A9, criterion 10 |
| **Out:** the 09:30 issue | optional (orchestrator Q1); not built unless asked, question 1 |
| **Out:** paper positions, top 10 candidates, Slack reports, the match report's text | FL1's |
| **Out:** BANKNIFTY intraday marks | A16's builder (orchestrator Q2) |

## Questions (recommendation first)

1. **The 09:30 issue:** recommended **not built** in G13b v1. The owner's entries fill at 09:30 from the 09:15
   forecast. A 09:30 issue needs A16's observer port, a third sealing deadline and its own scores. It is not cheap
   (reasoning only). The enum keeps `0930`, so adding it later changes no schema.
2. **BANKNIFTY's overnight share at 09:15:** recommended NIFTY's 0.393 until A16b-style BANKNIFTY candles exist, then
   a new method version (A16's builder owns BANKNIFTY intraday).
3. **Part B's first-seen rule:** NSE publishes the F&O file in the evening. If it is not in the archive by O1's 15:45
   step, the valuation runs in the next O1 run, and the record says so. Recommended. The alternative is a separate
   evening run, which is a schedule (not G13b's).

## Honest headline for the owner's first report notes (orchestrator, 21 Oct)

1. No forecaster in v1 uses the US closes. An untested adjustment is a guess.
2. At 09:15 (phase 2), the overnight move is already in the pre-open price, so the forecast of today's close has only
   about 61% of a normal session's variance left. Measured: 39% of NIFTY's daily variance is overnight. A range for
   today's close is therefore much narrower than a full day's.
3. Only `implied` and `hist750` take any view on direction. The rest say 50%. A range engine is not a direction
   engine, and next-day direction is near a coin flip (strong evidence).
