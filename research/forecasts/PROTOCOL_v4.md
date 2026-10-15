# Forecast protocol, version 4 (story G6): movement size, questions V1-V7

**Status: DRAFT, not frozen.** Written by Claude (G6 builder), 15 Oct 2026 IST, on branch `story/g6-protocol-v4`, from
design v2 section 5 (`docs/design_v2/05_volatility_research.md`), the stop rule of section 8.2, G6's acceptance
criteria (`docs/design_v2/REPLAN_new_stories.md`, `docs/stories/G-forecasts.md`), judge 96 and its addenda, and
ChatGPT reviews 95-98. It is frozen only after the judge's PASS and ChatGPT's review (orchestrator, 13 Oct 2026), by a
freeze record `research/forecasts/FREEZE_v4.md` (section 10). Until then nothing is counted under v4.

**Relation to versions 1-3.** v1 (`PROTOCOL.md`), v2 and v3 stay frozen, byte-identical and running: questions Q1-Q5,
their records, scores and families are untouched. v4 adds new questions with their own records, baselines, family and
freeze. v4 and v3 results are never pooled. Where v4 differs from v1-v3 on a shared idea, it says so.

**Reference code.** The rules below are executable in `fno/forecast_v4/` (pure functions, no I/O): `terms.py` (every
number), `loss.py`, `pairs.py`, `bootstrap.py`, `family.py`, `eligibility.py`, `units.py`, `settlement.py`,
`sessions.py`, `stop_rule.py`, `power.py`. G7 (baselines) and G8 (scoring) call them and never re-implement them.
Question and slot names are in `fno/constants.py`. Tests: `tests/forecast_v4/` (section 9).

Evidence labels as the project uses them: **strong evidence**, **some evidence**, **reasoning only**.

## 1. The questions and their exact targets

### 1.1 Session realised variance `RV_s`
- **Intraday (A16):** the squared overnight log return (previous regular session's 15:30 snapshot to this session's
  09:15 snapshot) plus the sum of the squared log returns over the 25 intervals between the 26 snapshots 09:15-15:30.
  A snapshot is the NIFTY index level with its source time; one more than 2 minutes old is stale. A session with any
  missing or stale snapshot has no intraday `RV_s` (void, never interpolated). If more than 5% of a quarter's sessions
  are void, a new version is proposed. Label: "quote-snapshot realised variance, not a traded-price measure".
- **Close proxy (`close_proxy`):** the squared close-to-close log return of the official NIFTY 50 closes
  (`research/data/nifty-panel/warmup_closes.csv`, O6), from the previous regular session's close.
- **RV is used exactly as observed:** never floored, rounded or replaced. Zero is a valid outcome.
- Units: dimensionless (squared log returns). A horizon's RV is the sum of its sessions' `RV_s`.
- **Series never pooled:** each record carries its measure. V1 is intraday only. V2 and V3 are scored on `close_proxy`
  for the whole of v4 (one measure, available now and unaffected by A16 outages); their intraday versions are a
  separate, reported series from A16's first full window (reasoning only: QLIKE ranks correctly under any conditionally
  unbiased proxy, Patton 2011, strong evidence, so the proxy costs power, not validity).

### 1.2 The questions
`d` is the forecast day (a scored session, section 2); the cutoff is 15:00:00 IST on `d`, as G1 v2; `d+n` is the n-th
scored session after `d`.

| Id | Name | Type | Outcome | Block L |
|---|---|---|---|---|
| V1 | `v1_rv_next_session` | point | intraday `RV_s` of `d+1` | 5 |
| V2 | `v2_rv_next_5_sessions` | point | sum of `RV_s` over `d+1..d+5` | 10 |
| V3 | `v3_rv_next_20_sessions` | point | sum of `RV_s` over `d+1..d+20` | 20 |
| V4 | `v4_rv5_below_weekly_atm_iv` | probability (diagnostic) | section 1.4 | 10 |
| V5 | `v5_close_inside_k_plus_minus_p` | probability (terminal intrinsic proxy) | section 1.5 | 20 |
| V6a | `v6_abs_move_2pct_next_session` | probability | `abs(ln(close(d+1) / close(d))) >= 0.02` | 5 |
| V6b | `v6_abs_move_2pct_within_5_sessions` | probability | any of the 5 session returns `d+1..d+5` has `abs >= 0.02` | 10 |
| V7 | `v7_vix_higher_in_5_sessions` | probability | `VIX(d+5) > VIX(d)` (strict; a tie is "no") | 10 |

V6's returns are close-to-close log returns between consecutive scored sessions; V7 uses India VIX closes from the same
official index-close files (A3/O6). Point forecasts are variances for the whole horizon, strictly positive.

### 1.3 Starts
V2, V3, V5, V6, V7: from the freeze (close proxy, A4 quotes, official closes). V1: when A16 has 20 non-void sessions.
V4: when A16 records weekly ATM quotes. A question that has not started shows "not enough data yet", never a failure.

### 1.4 V4, exact terms and units
P(realised volatility of `d+1..d+5` < the 15:00 ATM implied volatility of the nearest weekly expiry at least 5 scored
sessions after `d`).
- **Expiry:** the nearest listed NIFTY expiry `e` with at least 5 scored sessions in `(d, e]`; `S_e` = that count,
  `C_e` = calendar days from `d` to `e`.
- **ATM:** the listed strike nearest the 15:00 spot (a tie goes to the lower strike, as G1). The call and the put need a
  live two-sided quote at 15:00 with `(ask - bid) / mid <= 5%` each, priced at mid; otherwise the day is void. Some
  evidence for 5%: on 14 Oct 2026's 14:55 capture, the 10 strikes nearest spot of both monthly expiries had spreads of
  0.14-0.99% of mid (one session, monthly only); G7 reports weekly spreads before the freeze.
- **IV:** each leg's Black-76 IV (B1's `implied_vol.py`, rate 6.5%, calendar time `C_e / 365`) on the forward from put-call
  parity at K, `F = K + e^(r C_e / 365) (C_mid - P_mid)`, because weekly expiries have no future (reasoning only); the ATM
  IV is the mean of the two.
- **Units (`units.py`):** realised `sigma_RV = sqrt(sum(RV_s, d+1..d+5) x 252 / 5)`; implied on the same clock
  `sigma_IV = sqrt(IV^2 x (C_e / 365) / (S_e / 252))`. Outcome: `sigma_RV < sigma_IV`. Any void session voids the day.
- **Golden example (`tests/fixtures/forecast_v4/v4_golden.json`, by hand with 30-digit decimals):** session variances
  0.00006, 0.00008, 0.00007, 0.00009, 0.00007 sum to 0.00037, so `sigma_RV = sqrt(0.00037 x 252 / 5) = 13.656%`.
  IV 13.8%, 7 calendar days, 5 sessions: integrated implied variance `0.138^2 x 7 / 365 = 0.000365`, so
  `sigma_IV = 13.567%` and the outcome is **no**; comparing raw IV (13.8%) with session RV would wrongly say **yes**.
  With 9 calendar days (a holiday too), `sigma_IV = 15.384%`: **yes**. Dimension check: both sides squared, times 5/252,
  give the window's integrated variance (0.00037 and 0.000365).
- V4 is a **probabilistic diagnostic**: the variance risk premium is a difference of expected variances, and
  `P(RV < IV)` does not estimate it.

### 1.5 V5, exact terms and outcome source
P(NIFTY settles inside `K +/- P` at the nearest monthly expiry `e` after `d`).
- **Frozen at 15:00 on `d`:** `e` (the nearest monthly expiry strictly after `d`, from the 15:00 pack's futures), `K`
  (the listed strike nearest the 15:00 spot, tie to the lower) and `P` (the 15:00 mids of the `e` K call plus the K put,
  each under the 5% spread limit of 1.4; else void).
- **Outcome (`settlement.py`):** inside when `abs(level - K) < P` (strict; break-even counts as outside). `level` is the
  index's **final settlement price of `e`**, read by E7's `NseFinalSettlement` from NSE's daily F&O file of the expiry
  day only (`SttlmPric`, every expiring NIFTY row agreeing; E7 checked it on 25 Jan 2024's file, strong evidence).
  Never a later daily close, never another expiry's level.
- **Frozen with the outcome:** the source path (`NseDailyFoSource.path_for(e)`), the file's SHA-256 and `first_seen_at`,
  the archive time of A11's first version. A level first seen before 15:30 IST on `e` is refused. A missing file keeps
  the outcome unresolved; it is never filled from the index-close file.
- V5 is a **terminal intrinsic-payoff proxy**: "inside" means a buyer held to expiry lost before costs; "outside" does
  not mean the buyer won. **V5 is not evidence of money.**

## 2. The session set and void rules

- **Scored sessions are A7's `regular` sessions only** (`sessions.py`: `SessionCalendar.session_kind == "regular"`).
  Muhurat sessions (about an hour, in the evening) and weekend `special` sessions are never a forecast day, a horizon
  step or a base-rate return. A return runs from one regular close to the next, so a special session's move sits inside
  the next regular return and is never dropped.
- **This differs from G1 v1-v3**, which count special sessions as trading days. v4 excludes them so its outcomes, its
  base rates and the base rates disclosed in section 8 use one set (judge 96 addendum 2, should-fix 2). The cost,
  said plainly: of the 6 special sessions of 2017-2026, 2 were short DR-switch sessions (2 Mar and 18 May 2024) but 4
  had normal timings (three budget days and 20 Jan 2024), so 4 real sessions are not separate outcomes (reasoning
  only).
- **Void:** an outcome is void when a target session is beyond the calendar or the data, any value it needs is missing
  or stale (intraday), or a quote rule of 1.4 or 1.5 fails. Void dates are never scored; they are counted.

## 3. Baselines

### 3.1 Methods (frozen here, built by G7 like G2; point in time: only inputs first seen before `d`'s cutoff)
- **Trailing:** the same measure's RV over the last `h` scored sessions ending at `d`.
- **EWMA (RiskMetrics):** per-session variance `s2_t = 0.94 s2_(t-1) + 0.06 RV_t`, started from the mean of the first 250
  sessions; forecast `h x s2_d`. Eligible after 250 sessions.
- **HAR (daily):** OLS, levels: mean per-session close-proxy RV over the next `h` sessions on an intercept and the mean
  RV of the last 1, 5 and 22 sessions; most recent 750 rows resolved before the refit (at least 500); refit on the first
  scored session of each month; forecast `h x prediction`. **HAR (intraday):** the same on intraday `RV_s`, from 250
  A16 sessions (all available up to 750).
- **Raw implied:** `IV30(d)^2 x (calendar days from d to d+h) / 365`, IV30 from the 15:00 pack (G1 v2's estimator).
- **Premium-adjusted implied:** raw implied times the median of `RV_h(t) / raw implied_h(t)` over the most recent 750
  sessions resolved before the refit (at least 500), refit monthly as HAR (`eligibility.premium_ratio_window`).
  **Source of the window (judge 98 must-fix 1):** live 15:00 IV30 starts only on 13 Oct 2026, so on live data alone
  V2's primary would not be eligible until about late 2028. The window's `raw implied_h(t)` therefore uses a labelled
  proxy, `iv30_eod_close_proxy`: G1 v1's frozen estimator `PanelAtmIv30` (`fno/forecast/iv30.py`) on the A3 panel's
  first-archived end-of-day chains (traded closes, volume > 0, Black-76 on the traded future), unflagged days only.
  It is point in time by content (day t's chain is published on t's evening), not by archive time (2024-2026 files
  were archived in Oct 2026). **Window from 1 Jan 2024 only:** UDiFF files, and outside G1's 2019-2023 holdout. The
  panel has 685 regular sessions from 1 Jan 2024 to 14 Oct 2026 (strong evidence: manifest count); after the
  horizon's unresolved tail and flagged days (G1 measured 11-23 a year from 2021), about 620-680 remain, so the 500
  minimum holds at the freeze (some evidence). Live forecasts multiply the 15:00 raw implied by that ratio; the
  mismatch between 15:00 and end-of-day IV30 enters the ratio's noise (reasoning only). Each live day's window point
  keeps the same EOD proxy, so one estimator runs through the window. **Forward diagnostic (ChatGPT review 99):**
  every report gives the paired 15:00 / EOD IV30 ratio, its median over all live days and the latest 20, and their
  drift (`diagnostics.proxy_drift`); descriptive only, and the proxy is never claimed equivalent to 15:00 IV30.
- **Option-implied probability (V5):** lognormal, `ln S_T ~ N(ln F - s^2 tau / 2, s^2 tau)`, `s` = the mean Black-76 IV of
  the K call and put, `tau = C_e / 365`, `F` = expiry `e`'s future in the 15:00 pack;
  `p = N(z(K + P)) - N(z(K - P))` with `z(x) = (ln(x / F) + s^2 tau / 2) / (s sqrt(tau))`.
  Labelled "risk-neutral, not a real-world probability".
- **Base rate (every probability question):** as G1 (b): the share of 1s among the most recent 750 scored sessions
  before `d` whose outcome resolved before `d`'s cutoff and is not void; at least 500, else no value.
- **A baseline value that is not strictly positive (variance) or cannot be computed is missing that day, never
  floored or replaced.** V4's base rate needs 500 resolved A16 days, so V4 has no baseline comparison for about two
  years after A16 starts (said plainly; V4 is reported only).

### 3.2 Primary baselines (predeclared before any v4 score) and eligibility (`eligibility.py`)

| Question | Primary baseline | Also reported |
|---|---|---|
| V1 | HAR daily, then HAR intraday from its first eligible date (one way) | trailing, EWMA, premium-adjusted implied |
| V2, V3 | premium-adjusted implied | raw implied, HAR, trailing, EWMA |
| V4, V6a, V6b, V7 | base rate | none |
| V5 | option-implied probability (Brier) | base rate |

Premium-adjusted implied is the predeclared physical-variance benchmark because raw implied includes a risk premium
(strong evidence, design 5.1); superiority is not assumed (the trailing ratio adds estimation noise) and both are
scored. V5's baseline is a probability scored by Brier, never IV squared. **When the primary is not eligible that day,
the pair is missing and counted, never filled by another baseline.** After V1's switch, a day without intraday HAR is
missing; daily HAR never stands in again.

## 4. Scoring and the two date sets (`loss.py`, `pairs.py`)

- **Point questions: the QLIKE ranking loss `L(f, RV) = ln f + RV / f`, primary, with no floor.** It differs from the
  textbook `RV / f - ln(RV / f) - 1` only by `ln RV + 1`, free of the forecast, so paired differences are identical
  whenever RV > 0 (strong evidence: algebra; tested on 2,000 random cases). It is defined at RV = 0 (`ln f`). A
  forecast must be finite and > 0; an RV must be finite and >= 0.
- **Probability questions:** Brier (unclipped), primary; log score (clipped to [0.01, 0.99] as G1), the 10-bin
  reliability table, calibration slope and intercept, and the Brier skill score against the base rate, reported.
- **Secondary for point questions:** squared error on variance, and Mincer-Zarnowitz `RV = a + b f` for bias.
- **Scored set (the significance test):** dates in date order with the outcome resolved, not void, and both the
  forecaster and the primary baseline present. **Zero-RV dates and zero differences stay in.** Dropped and counted, in
  this precedence: unresolved, void, forecaster missing, baseline missing. Nothing is imputed; one row per date.
- **Gate set (the minimum effect of a point question):** the scored dates with RV > 0. Its zero-RV exclusions are
  counted on every report. For a probability question the gate set is the scored set.
- Both sets are fixed by these rules before any score. Revision 2's floor (1% of the trailing 250-session median) is
  dropped; it is reported only as a sensitivity (it would have changed 133 of 2,159 close-proxy one-day outcomes).

## 5. What "beats the baseline" means (`confirmatory.py`, `bootstrap.py`, `family.py`, `terms.py`)

1. **Statistic:** `d_t = loss(forecaster) - loss(baseline)` on the scored set; `D` = their mean; negative favours the
   forecaster; one-sided.
2. **Resampling.** For n pairs and block length L (table 1.2): B = 10,000 resamples, each drawing ceil(n / L) block
   starts uniformly from 0..n-L with replacement (`numpy.random.default_rng(SeedSequence(words))`, all starts in one
   draw of shape (B, ceil(n / L))), joined in draw order and cut to n. k is the member's place in the family (below);
   reported-only comparisons are numbered after 15.
3. **Confirmatory claim rule, revision 2: rule E+D** (owner decision "3 B", 15 Oct 2026; judge 98 addendum 2;
   `confirmatory.calibrated_p`, `tools/v4_claim_thresholds.py`). A member claims at a look only with **at least 12
   whole batches** and a **batch-means t** p-value (the latest floor(n / L) batches of L, Student t with batches - 1
   df) **at or below its worst-case calibrated threshold**. The threshold is computed at the look for the member's
   actual n by the frozen tool: the smallest, over the member's null group, of the p-quantile at rate / 15 (taken at
   its 95% lower confidence rank) from 100,000 seeded mean-zero series. Each group is Gaussian i.i.d., AR(1) 0.5 and
   overlapping nulls plus an **empirical null from exposed 2024-26 NIFTY data** (circular 20-session blocks of centred
   baseline-vs-baseline differences, right-skewed orientation). V1 and V2 use QLIKE nulls (trailing 5 vs 20 sessions),
   V6a and V6b Brier nulls (EWMA-normal vs base rate), and V7 borrows V6b's (no VIX null measured, reasoning only).
   **Why:** QLIKE differences on real data have a raw skew of -17 to +15 and a batch-mean skew of up to 7.5, against
   2.8 for the lognormal case (some evidence: exposed data, a few baseline pairs). Rare crash days dominate the mean,
   so most windows without one favour the forecaster that under-forecasts. On those nulls, revision 1's
   max(batch t, studentized bootstrap) rejected **6-18% at Holm's first step 0.0013** at n = 125 for L = 5 and 10,
   still 7.5-10% at n = 250. A divisor of 10 still gave 2-13%; Hall's skew correction did not help. The bootstrap's
   1 / 10,001 resolution cannot reach the thresholds needed, so it is dropped from the rule. **Measured size of E+D**
   (held-out seeds, 100,000 series): within nominal + 2 Monte Carlo SE in all 30 cells (5 questions, n = 2L, 125
   and 250, both looks); fewer than 12 batches gives no claim at all. Strong evidence for the measured null
   processes, some evidence that they represent future data. Tables: `research/forecasts/v4_size_study.md` (every
   option) and `v4_claim_thresholds.md`. Revision 1's 1,000-series calibration
   (`v4_null_calibration.md`) is superseded; its rates below 0.01 are some evidence only. The studentized bootstrap,
   revision 0's centred bootstrap and a Newey-West HAC t are reported sensitivities, **never used to choose a
   result**.
4. **Minimum effect, registered (owner's 3%, unit confirmed 15 Oct 2026):** on the gate set, the relative improvement
   `-mean(d) / mean(baseline loss)` must be **at least 0.03** for a point question, with the baseline's **textbook**
   QLIKE as the loss (so the gate reads "3% lower mean textbook QLIKE on the same RV > 0 dates"), and **at least 0.02**
   for a probability question with Brier (identical to a Brier skill score of 0.02). The primary test keeps every scored
   date, zeros included. These are forecast effects only, never evidence of money. Significant but smaller: "real but
   too small to use".
5. **Futility, with its own two-look budget (ChatGPT review 99, finding 2):** on the gate set, a one-sided **97.5%**
   upper bound of the relative improvement at each look (Bonferroni 2 x 2.5% = 5% per member over the two looks):
   the same resampling with seed words `[20261015, k, 1, look]` (look 1 or 2), pairs kept together, the ratio of means
   recomputed on each resample, the nearest-rank 97.5th percentile (the 9,750th of 10,000). **Futile when the bound is
   below the minimum effect.** Futile at look 1 is final; an open member uses its own 2.5% at look 2. Never declared
   with fewer than 2L gate pairs. Across members, "every member futile" is an intersection-union claim (Berger 1982).
6. **The confirmatory family (15 members, fixed now).** Targets V1, V2, V6a, V6b, V7, each with three forecaster slots:
   `rules` (the registered code forecaster: G7's rule forecaster, or M1's weather model for V6), `hybrid` (Book 2) and
   `ai_team` (Book 3), numbered k = 1..15 in the order of `terms.FAMILY`. Each slot holds the first forecaster version
   registered in the ledger for it before its first counted v4 forecast; a later variant is reported, never a member
   (it goes to a later version). **V3, V5 (20-session) and V4 (diagnostic) are scored and tested identically but are
   never members**: at about 12 independent outcomes a year they cannot settle in useful time (section 7), and as
   members they would make every other claim stricter (0.05 / 21 instead of 0.05 / 15). Reasoning only; this fixes the
   design's "m of about 15".
7. **The family decision: Bonferroni at rate / 15, with p = 1 for every member not judged (ChatGPT review 98).**
   Rule E+D calibrated only Holm's first step, so each member's calibrated p is compared with rate / 15; Holm's later
   steps are not used (a small power loss when several members claim at once). A member not judged at that look (no
   registered forecaster, fewer than 12 batches, or closed earlier) enters with p = 1. **Every report states the
   look, its family-wise rate, the decision timestamp (with time zone) and all 15 members, judged or not**
   (`FamilyDecision.lines()`).
8. **Two looks at most, alpha split (Bonferroni over looks, strong evidence for the bound):** look 1, the stop-rule
   review (design 8.2), at family-wise **0.02**; look 2, the re-run on the projected settle date (8.2 option 1), at
   **0.03**. Total at most 0.05 however the looks correlate. A claim or a futility "no" at look 1 is final (closed, p = 1
   at look 2). There is no other confirmatory look; monthly reports are descriptive. **This is new in G6** (design 5.5
   says Holm at 5% without naming looks); it is the "explicit sequential error-control contract" review 98 asks for.
9. A member **claims** only when significant under rule E+D at its look **and** it meets the minimum effect.
10. **Stability** (descriptive): the sign of `D` in the first and second half of the scored period. **Economic check:**
    a forecast counts for trading only through a factory idea's registered mapping and its shadow net after costs.

## 6. The stop rule's decision unit (`stop_rule.py`; design 8.2, owner decisions of 15 Oct 2026)

- **Test A** counts the family's members whose slot has a registered forecaster at the review (one per forecaster and
  question); G1 v3's family is reported beside it, never counted. Missing and void outcomes are excluded by section 4
  and counted. **yes:** a counted member claims at look 1. **no (futility):** every counted member is futile (a
  significant but too-small one included). **undecided:** anything else, including **zero counted members** and any
  counted member with fewer than 2L pairs. Underpowered is never "no".
- **Test B** counts shadow strategies registered in the ledger before the review. **yes:** a one-sided 95% lower bound
  of net per trade after costs above zero. **no:** every counted strategy reached its registered sample and its upper
  bound is below its registered minimum useful net. **Zero counted shadows: `undecided/no_economic_test`, never "no".**
  A strategy without a resolved trade has no bound and is undecided.
- **Table:** B yes: continue. A no and B no: stop or pivot (owner chooses). A yes and B not yes: continue 6 months with
  the AI budget halved. Anything else: option 1 (continue to the projected settle date, a planning projection) when the best-powered question's
  projected settle date is at most 2 years after the review, else option 2 (code only). **No power report yet means no
  projected date: option 2** (reasoning only; flagged in section 11).

## 7. The 60-outcome power report (`power.py`): a planning projection only

After 60 scored outcomes of a member, the statistician measures `r = SD(d) / (margin x mean baseline loss on the gate
set)` and publishes the needed independent outcomes `n = ceil(((z(1 - 0.03 / 15) + z(0.80)) x r)^2)` (look 2's first
Holm step) and the years remaining, at 252 / horizon independent outcomes a year, counting the 60 overlapping outcomes
as 60 / horizon. If that is beyond 2 years, the card and the owner are told plainly that the question cannot settle in
useful time. **The report only states a date; it never changes a threshold, the family, a baseline, a block or a
look's rate. It promises no settle date:** the n / horizon count is a rough heuristic, not the block-dependent
sampling distribution (ChatGPT review 99). Arithmetic (strong evidence): r = 3 needs 114 outcomes at 0.05 / 15 (the design's table, reproduced),
125 at look 2 and 134 at look 1; r = 5 needs 316 at 0.05 / 15.

## 8. Disclosure: what was seen before the freeze

- **Base rates measured on 2017-2026 outcomes before this protocol (revision 2, recomputed 15 Oct 2026 on regular
  sessions only):** NIFTY official closes `warmup_closes.csv`, 2 Jan 2017 to 14 Oct 2026, 2,410 regular sessions,
  **2,409 regular close-to-close log returns**. Absolute return at least 2%: **100 of 2,409 = 4.15%**. At least one such
  return within 5 sessions (windows of 5 consecutive returns): **331 of 2,405 = 13.76%**. Exact zero returns: 2 (31 Mar
  2017, 8 May 2024). Revision 2's floor would have bound 133 of 2,159 close-proxy one-day outcomes. These numbers set
  the weather floors (M1) and the QLIKE decision; `tests/forecast_v4/test_units_settlement_sessions.py` reproduces the
  first two from the committed file.
- **Also seen:** ATM implied above trailing 20-day realised on 74% (2019-23) and 82% (2024-26) of monthly entries
  (response 92); the 14 Oct 2026 quote capture's spreads (1.4).
- **Consequence:** 2017-2026 history is spent for V6 base rates and for any V-question tuned on it; it gives
  exploratory results only (`research/DATA_SPEND.md` once R1 writes it). **Only forecasts made after the freeze count.**
  Any G7 or G8 back-fill run before the freeze is labelled exploratory and is disclosed in the freeze record.

## 9. Acceptance criteria and their tests (`tests/forecast_v4/`)

| Criterion | Test |
|---|---|
| QLIKE ranking loss at zero, near-zero and missing RV | `test_loss_and_pairs.py`: zero, 1e-300, refusals; unresolved counted |
| Equal paired differences with the textbook form when RV > 0 | `test_paired_differences_are_equal_under_both_forms...` |
| The frozen day sets behind the 3% effect, zero-RV count | `test_scored_set_keeps_zero_rv...`, `test_gate_is_three_percent...` |
| One-sided test (seed, blocks, missing pairs), null-calibrated | `test_bootstrap.py`, `test_confirmatory.py`, the committed calibration |
| HAC as a sensitivity | `test_hac_matches_a_hand_newey_west...` |
| Family rule (Bonferroni at rate / 15), p = 1 unjudged, membership and timestamp | `test_family_and_stop_rule.py` |
| Rule E+D, its thresholds, size study and real-data skew | `test_claim_rule.py`, the committed tables |
| Baseline eligibility | `test_eligibility_and_power.py` |
| V4's dimensionally checked golden example | `test_units_settlement_sessions.py` with `v4_golden.json` |
| V5's outcome from the expiry's final settlement, source and timestamp | `test_v5_...` (wrong expiry, later file, early timestamp) |
| Futility against the minimum effect, 97.5% at each look | `test_futility_...` (both looks), `test_a_is_no_only_when...` |
| Stop rule A/B table with zero trials, missing and void outcomes | `test_the_review_table`, `test_a_with_zero...`, `test_b_...` |
| 60-outcome power report (planning only) | `test_power_report_...`, the design table reproduced |
| Session set and the disclosed base rates | `test_session_set_is_a7_regular...`, `test_disclosed_base_rates...` |

## 10. The freeze (after the judge's PASS and ChatGPT's review only)

`research/forecasts/FREEZE_v4.md` will name the commit that adds this text in its final form and list the SHA-256 of
this file, every file of `fno/forecast_v4/`, `tests/fixtures/forecast_v4/v4_golden.json`, and every G7 and G8 file that
decides a v4 baseline, outcome or score. As S1's option A, **v4 is frozen only once that code exists**, so no counted
v4 forecast is made before its code is hashed. Recorded, not byte-checked (shared, changed by other stories, behaviour
locked by these tests): `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`,
`fno/research_engine/implied_vol.py`. The ledger row (B4) is written with the freeze. A change after it is a new
version, never an edit.

**Preconditions of the freeze:** the judge's PASS; ChatGPT's review; G7 and G8's code exists; and the owner's written
confirmation of section 11's items A-C (given, 15 Oct 2026) and of item D.

## 11. Points for the judge and ChatGPT (decided in this draft, open to challenge)

**Confirmed by the owner, 15 Oct 2026** (`docs/DESK_DECISIONS.md`, "G6 protocol v4 choices A, B, C confirmed"):
- **A.** Test A "yes" at the stop review needs Holm at 0.02, not the design's 5%: at r = 3, 134 outcomes instead of
  114 (5.8).
- **B.** No power report at the review means option 2, code only (section 6).
- **C.** The premium-adjusted baseline's ratio window uses the labelled EOD IV30 proxy from 1 Jan 2024 (3.1). Without
  it, V2 has no eligible primary until about late 2028 and cannot be judged at the May 2027 review.

- **D. Owner chose a stricter rule (3 B, 15 Oct 2026); the exact rule is chosen by measured size:** rule E+D (5.3),
  the only measured option within tolerance in every cell. Its power cost, by normal approximation (planning only,
  optimistic under heavy tails), in independent outcomes at r = 3 / r = 5 with the n = 125 thresholds (at least this,
  since thresholds fall as n grows). The plain first step needs 134
  / 316. Under E+D: V1 426 / 1,183 (about 1.7 / 4.7 years); V2 396 / 1,099 (about 8 / 22 years); V6a 180 / 499
  (about 0.7 / 2 years); V6b and V7 151 / 419 (about 3 / 8 years). **Said plainly: the QLIKE questions V1 and V2
  cannot be claimed in useful time on realistic data**; the Brier questions can, slowly. The other options' sizes
  stay disclosed in `v4_size_study.md`. Untested: futility's percentile bound under the same nulls.

Also open to challenge: the 15-member family without V3, V5 and V4 (5.6); special sessions excluded (section 2); V2
and V3 on `close_proxy` (1.1); the 5% spread limit and parity forward (1.4); strict "inside" for V5 (1.5).
