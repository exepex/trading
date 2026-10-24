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
`sessions.py`, `stop_rule.py`, `power.py`, `regime.py`. G7 (baselines) and G8 (scoring) call them and never re-implement them.
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
`d` is the forecast day (a scored session, section 2); the cutoff is **every field observed by 14:40:00 IST on `d`,
captured from 14:30:00, each with its real `observed_at`** (section 1.6; G1 v2 keeps 15:00 for its own questions);
`d+n` is the n-th scored session after `d`.

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
P(realised volatility of `d+1..d+5` < the pack's ATM implied volatility (section 1.6) of the nearest weekly expiry at
least 5 scored sessions after `d`).
- **Expiry:** the nearest listed NIFTY expiry `e` with at least 5 scored sessions in `(d, e]`; `S_e` = that count,
  `C_e` = calendar days from `d` to `e`.
- **ATM:** the listed strike nearest the pack's spot (a tie goes to the lower strike, as G1). The call and the put need
  a live two-sided quote in the pack, each with its `observed_at`, with `(ask - bid) / mid <= 5%` each, priced at mid;
  otherwise the day is void. Some evidence for 5%: on 14 Oct 2026's 14:55 capture, the 10 strikes nearest spot of both
  monthly expiries had spreads of 0.14-0.99% of mid (one session, monthly only); G7 reports weekly spreads before the
  freeze.
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
- **Frozen from the pack of `d` (section 1.6):** `e` (the nearest monthly expiry strictly after `d`, from the pack's
  futures), `K` (the listed strike nearest the pack's spot, tie to the lower) and `P` (the pack's mids of the `e` K
  call plus the K put, each under the 5% spread limit of 1.4; else void).
- **Outcome (`settlement.py`):** inside when `abs(level - K) < P` (strict; break-even counts as outside). `level` is the
  index's **final settlement price of `e`**, read by E7's `NseFinalSettlement` from NSE's daily F&O file of the expiry
  day only (`SttlmPric`, every expiring NIFTY row agreeing; E7 checked it on 25 Jan 2024's file, strong evidence).
  Never a later daily close, never another expiry's level.
- **Frozen with the outcome:** the source path (`NseDailyFoSource.path_for(e)`), the file's SHA-256 and `first_seen_at`,
  the archive time of A11's first version; where no such time is recorded, the first sighting in A8's release-check
  log (`release_times.first_seen_times`), and a day with neither stays unresolved, never stamped "now" (G7b). A level
  first seen before 15:30 IST on `e` is refused. A missing file keeps
  the outcome unresolved; it is never filled from the index-close file.
- V5 is a **terminal intrinsic-payoff proxy**: "inside" means a buyer held to expiry lost before costs; "outside" does
  not mean the buyer won. **V5 is not evidence of money.**

### 1.6 The day's clock (story G10; owner decisions of 15 Oct 2026; A2 dropped 16 Oct)

| Time (IST, on `d`) | What happens |
|---|---|
| 14:30:00 | The pack's capture starts (A4e's named window: spot, the future of `e`, India VIX, the chains, IV30); an incomplete capture retries |
| 14:40:00 | **The pack's cutoff:** a field is in the pack only if its answer was received by 14:40:00 |
| right after the capture ends, by 14:45:00 | **One release:** one pack, one SHA-256, to every family at the same moment; a release record written after 14:45:00 makes the day `system_late` ("released late"; G10 completion, decision D1, owner decided 24 Oct (DESK_DECISIONS)) |
| 15:10:00 | **One deadline:** a commitment counts only if GitHub received its push by then (GitHub's receipt time, never a commit's own time) |
| 15:15 | **Common snapshot** (A16's 15:15 mark): the skill yardstick of every desk decision and the flag's end level |

- **Honest times:** every field keeps its real `observed_at`, the time its answer was received by this host's checked
  clock; `last_trade_time` is kept apart (the "traded today" check only) and is never the observation time. A capture
  whose clock was not checked ok before and after is not used.
- **Day-quality label, one per day, on every v4 report, and joined to every v4 record by its day:**
  `A`, every required field observed by 14:40:00 and released by 14:45:00; `system_late`, no complete pack by 14:40:00, a release
  after 14:45:00, or no release record at all. A scored session from the live date with no release record is
  `system_late` once its day has passed (the next release run writes that record, write-once; every reader applies the
  same rule meanwhile); the report's own date without a record is pending, never scored; a day before the live date
  has no label (the close-proxy cohort). A verdict uses `A` days; every report counts both labels, the pending day and
  the flagged days. (`A2`, A16's 14:30 mark as fallback,
  was dropped on 16 Oct: that mark has no India VIX, one monthly beside the weekly and no next monthly on an expiry
  day, so it can never hold a complete pack.)
- **One pack, one hash:** a forecaster that reads the pack names the released pack's SHA-256 in its record; another or
  an empty hash is refused. A forecaster that commits before the pack exists names none.
- **Moved after cutoff (a flag, never a block):** a day with `abs(ln(S_15:15 / S_14:30)) > X` is flagged and reported
  apart; nothing is dropped. `S` is A16's checked level at its 14:30 and 15:15 marks; a day without either has no flag
  value ("flag not computable"). **X = 0.006104597099330481**, the nearest-rank 95th percentile (the `ceil(0.95 n)`-th
  smallest move) over **1,661** of A16b's checked sessions, 2 Jan 2020 to 14 Oct 2026, source revision
  `1d68c4477ec2356ecc9a3c5583c5702152424b8f` (`tools/v4_moved_after_cutoff.py`). History's 5% does not promise 5% of
  future days.
- **Pack values stand in for the close:** every input of `d` itself is the pack's value, labelled live; back-filled rows
  use closes and stay `backfill_exploratory`; the live and the close-proxy cohorts are scored apart, never pooled.
  Outcomes do not move: V1-V3, V6 and V7 stay measured from official closes and A16's session RV (1.1-1.2).

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
  sessions; forecast `h x s2_d`. Eligible after 250 sessions. **For both trailing and EWMA, "ending at `d`" and
  `s2_d` are read as the last session before `d`:** `d`'s own close is not known at the cutoff (G7, G7b).
- **HAR (daily):** OLS, levels: mean per-session close-proxy RV over the next `h` sessions on an intercept and the mean
  RV of the last 1, 5 and 22 sessions; most recent 750 rows resolved before the refit (at least 500); refit on the first
  scored session of each month; forecast `h x prediction`. **HAR (intraday):** the same on intraday `RV_s`, from 250
  A16 sessions (all available up to 750); its 1-, 5- and 22-session means are taken over the usable (non-void)
  sessions, so a void session is skipped, never a reason for the day's value to be missing.
- **Raw implied:** `IV30(d)^2 x (calendar days from d to d+h) / 365`, IV30 from the pack (section 1.6; G1 v2's live
  estimator on the pack's quotes).
  **A flagged IV30** (single expiry, `AtmIv30.flagged`) gives no raw and no premium-adjusted value that day: missing
  and counted, never filled, as the ratio window below drops flagged days (G7b).
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
  minimum holds at the freeze (some evidence). Live forecasts multiply the **pack's** raw implied by that ratio; no
  14:30 IV30 history exists, so the window stays the EOD proxy and the pack / EOD mismatch enters the ratio's noise
  (reasoning only). Each live day's window point
  keeps the same EOD proxy, so one estimator runs through the window. **Forward diagnostic (ChatGPT review 99):**
  every report gives the paired pack / EOD IV30 ratio, its median over all live days and the latest 20, and their
  drift (`diagnostics.proxy_drift`); descriptive only, and the proxy is never claimed equivalent to the pack's IV30.
- **Option-implied probability (V5):** lognormal, `ln S_T ~ N(ln F - s^2 tau / 2, s^2 tau)`, `s` = the mean Black-76 IV of
  the K call and put, `tau = C_e / 365`, `F` = expiry `e`'s future in the pack;
  `p = N(z(K + P)) - N(z(K - P))` with `z(x) = (ln(x / F) + s^2 tau / 2) / (s sqrt(tau))`.
  Labelled "risk-neutral, not a real-world probability".
- **Base rate (every probability question):** as G1 (b): the share of 1s among the most recent 750 scored sessions
  before `d` whose outcome resolved before `d`'s cutoff and is not void; at least 500, else no value. **V4's and V5's
  base rates count live outcomes only:** no end-of-day history fills them (V5's traded closes carry no bid and ask, so
  1.5's spread rule cannot apply), so each has no value for about two years after its start (G7b).
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
- **Missed days (revision 9; owner decisions of 15 Oct 2026, responses 144-147, judge 138-139, ChatGPT review 112;
  `misses.py`).** Verdicts use observed days only; a missed day is never imputed, because a filled-in day gives d = 0
  while the futility test still adds the minimum effect, so a forecaster that never ran would be called futile. After
  the freeze, what the scored set leaves out is counted for each **registered** slot from its `effective_start`, the
  session named in its row of `research/forecasts/v4_slots.csv`: a session after the freeze and no later than the
  slot's first eligible session (the first live day after the freeze with a primary-baseline value). So every
  baseline-observable day from then on is observed or missed, even before the slot's first forecast (owner, 16 Oct
  2026, "from the declared start"; ChatGPT review 119). An **unregistered** slot is "not started": p = 1, never
  judged. Exploratory runs before the freeze count misses from the forecaster's first forecast:
  - a **miss** is a resolved, non-void day where the primary baseline forecast and the forecaster did not (a null
    answer is a miss);
  - an **input failure** is a resolved, non-void day where neither forecast (the common pack failed); it is counted
    apart and is never a miss;
  - a member is **"undecided, operations"** at a look when it missed more than **10%** of its baseline-observable days,
    or more than **10%** of the baseline-observable 2% days (the regime's 2% days, section 5); so with **fewer than 10**
    such days, missing **any** of them is already more than 10%. Such a member is not judged at that look: never a
    claim, never futile.
  - Every comparison and every look prints each member's misses, 2% days missed and input failures.
- **A `system_late` day** (section 1.6) is excluded for every member and counted apart; **a commitment received
  after 15:10:00** is no forecast that day (a miss). Every report states each label's day count and the flagged days.
- Both sets are fixed by these rules before any score. Revision 2's floor (1% of the trailing 250-session median) is
  dropped; it is reported only as a sensitivity (it would have changed 133 of 2,159 close-proxy one-day outcomes).

## 5. What "beats the baseline" means (`confirmatory.py`, `bootstrap.py`, `family.py`, `terms.py`)

1. **Statistic:** `d_t = loss(forecaster) - loss(baseline)` on the scored set; `D` = their mean; negative favours the
   forecaster; one-sided.
2. **Resampling.** For n pairs and block length L (table 1.2): B = 10,000 resamples, each drawing ceil(n / L) block
   starts uniformly from 0..n-L with replacement (`numpy.random.default_rng(SeedSequence(words))`, the words starting
   with the v4 seed 20261015; all starts in one draw of shape (B, ceil(n / L))), joined in draw order and cut to n.
   k is the member's place in the family (below); reported-only comparisons are numbered after 15.
3. **Confirmatory claim rule: E+D** (`confirmatory.calibrated_p`; revisions 2, 4, 5 and 6 of this draft). A member
   claims at a look only with **at least 12 whole batches** and a **batch-means t** p-value (Student t, batches - 1
   df) **at or below its worst-case calibrated threshold**, computed at the look for the member's n by the frozen
   tools. **Every member also needs at least 5 2% days in the scored window** (`confirmatory.judgeable`; V1 and V2
   from revision 8), else it is undecided at that look. **A window whose 2% days are more than 10% of its scored
   outcomes is not judgeable either, for every member** (`confirmatory.crash_dominated`; section 11 E, option 2): at
   n = 125 a judgeable window holds at most 12 such days, so the 13+ band starts at n = 130. V6a and V6b use the
   thresholds of the window's band (5-7, 8-12, 13+ days), V1 and V2 one threshold (measured: no band needed). A member
   that is "undecided, operations" (section 4, revision 9) is not judged at that look. **V7 is descriptive-only in
   v4** (revision 6: no measured rule holds its size across VIX regimes; its slots stay at p = 1, never a claim,
   never futile, not counted in Test A). Every threshold, the nulls behind it, the measured sizes and what
   "held-out" proves are in **`PROTOCOL_v4_calibration.md` (part of this protocol, frozen with it)**. The studentized
   bootstrap, revision 0's centred bootstrap and a Newey-West HAC t are reported sensitivities, **never used to choose
   a result**.
4. **Minimum effect, registered (owner's 3%, unit confirmed 15 Oct 2026):** on the gate set, the relative improvement
   `-mean(d) / mean(baseline loss)` must be **at least 0.03** for a point question, with the baseline's **textbook**
   QLIKE as the loss (so the gate reads "3% lower mean textbook QLIKE on the same RV > 0 dates"), and **at least 0.02**
   for a probability question with Brier (identical to a Brier skill score of 0.02). The primary test keeps every scored
   date, zeros included. These are forecast effects only, never evidence of money. Significant but smaller: "real but
   too small to use".
5. **Futility: F+D** (`confirmatory.futility_p`; a false "no" gets the false-"yes" standard). With e_t = d_t +
   margin x b_t, "improvement below the minimum effect" is mean(e) > 0. A member is **futile at a look only with at
   least 12 batches and a batch-means t p-value for it at or below its calibrated threshold**: 2.5% per look
   (Bonferroni 2 x 2.5%), on nulls shifted to a true improvement exactly equal to the minimum effect; futile at look 1
   is final. The 5-day gate and the Brier bands apply as in item 3. Measurements: `PROTOCOL_v4_calibration.md`. Across
   members, "every member futile" is an intersection-union claim (Berger 1982).
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
   (`FamilyDecision.lines()`), and every verdict
   prints its scored window's regime (`regime.window_regime`: mean India VIX, 2% days, band; revision 7).
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
  counted member with fewer than 12 batches or "undecided, operations" (section 4: a member that did not run is no
  evidence of no skill; a book that keeps failing is fixed or stopped by an operational or budget stop, recorded apart).
  Underpowered is never "no".
- **Test B** counts shadow strategies registered in the ledger before the review. **yes:** a one-sided 95% lower bound
  of net per trade after costs above zero. **no:** every counted strategy reached its registered sample and its upper
  bound is below its registered minimum useful net. **Zero counted shadows: `undecided/no_economic_test`, never "no".**
  A strategy without a resolved trade has no bound and is undecided.
- **Table:** B yes: continue. A no and B no: stop or pivot (owner chooses). A yes and B not yes: continue 6 months with
  the AI budget halved. Anything else: option 1 (continue to the projected settle date, a planning projection) when
  the best-powered question's projected settle date is at most 2 years after the review, else option 2 (code only).
  **No power report yet means no projected date: option 2** (reasoning only; section 11).
- **The table's result is advice to the owner, never an automatic step** (owner, 21 Oct 2026, response 299 item 2):
  the Innovation Lab decides what runs and with what budget; the review reports Test A, Test B and the table's option.

## 7. The 60-outcome power report (`power.py`): a planning projection only

After 60 scored outcomes of a member, the statistician measures `r = SD(d) / (margin x mean baseline loss on the gate
set)` and publishes the needed independent outcomes `n = ceil(((z(1 - 0.03 / 15) + z(0.80)) x r)^2)` (look 2's first
Holm step) and the years remaining, at 252 / horizon independent outcomes a year, counting the 60 overlapping outcomes
as 60 / horizon. If that is beyond 2 years, the card and the owner are told plainly that the question cannot settle in
useful time. **The report only states a date; it never changes a threshold, the family, a baseline, a block or a
look's rate. It promises no settle date:** the n / horizon count is a rough heuristic, not the block-dependent
sampling distribution (ChatGPT review 99). Arithmetic (strong evidence): r = 3 needs 114 outcomes at 0.05 / 15 (the
design's table, reproduced), 125 at look 2 and 134 at look 1; r = 5 needs 316 at 0.05 / 15. Under rule E+D the
calibrated threshold replaces rate / 15 in this formula, which needs far more outcomes (section 11, D).

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
- **Back-fills run before the freeze (exploratory, never counted, each row `backfill_exploratory`):** G7's baselines
  and rule forecasters from closes (`research/forecasts/v4/`: `base_rate`, `trailing`, `ewma_094`, `har_daily`,
  `v6_ewma_t4`, and G7b's `v2_close_blend`, `v3_close_blend`, `v7_vix_vs_mean20`); M1's weather (`weather`,
  `weather_vix_v1`, `weather_checklist_v0`); G8's exploratory reports (`research/forecasts/v4_scores/`) and demo
  look. The freeze record names each with its commit and date range.
- **Back-fill against live (G10):** the back-fill uses closes where live forecasts use the pack's values; no intraday
  implied-volatility history exists (the panel holds end-of-day chains only), so the two cohorts are never pooled.

## 9. Acceptance criteria and their tests (`tests/forecast_v4/`)

| Criterion | Test |
|---|---|
| QLIKE loss at zero, near-zero, missing RV; equal paired differences; the 3% day sets | `test_loss_and_pairs.py`, `test_bootstrap.py` |
| One-sided test, rules E+D and F+D, thresholds, size and futility studies, Brier regimes | `test_confirmatory.py`, `test_claim_rule.py`, `test_futility_rule.py`, `test_brier_regimes.py` |
| Family rule, p = 1 unjudged, membership and timestamp; stop-rule table (zero trials, missing, void) | `test_family_and_stop_rule.py` |
| Baseline eligibility; 60-outcome power report (planning only) | `test_eligibility_and_power.py` |
| V4's golden example; V5's settlement source and timestamp; session set and base rates | `test_units_settlement_sessions.py` |
| Protocol text and code agree | `test_protocol_text.py` |

## 10. The freeze (after the judge's PASS and ChatGPT's review only)

`research/forecasts/FREEZE_v4.md` will name the commit that adds this text in its final form and list the SHA-256 of
this file and `PROTOCOL_v4_calibration.md`, every file of `fno/forecast_v4/`, the calibration tools
(`tools/v4_*.py`) and their committed tables, `tests/fixtures/forecast_v4/v4_golden.json`, and every G7 and G8 file that
decides a v4 baseline, outcome or score. As S1's option A, **v4 is frozen only once that code exists**, so no counted
v4 forecast is made before its code is hashed. Recorded, not byte-checked (shared, changed by other stories, behaviour
locked by these tests): `fno/constants.py`, `fno/desk/settlement.py`, `fno/research_data/calendar.py`,
`fno/research_engine/implied_vol.py`. The ledger row (B4) is written with the freeze. A change after it is a new
version, never an edit.

**Preconditions of the freeze:** the judge's PASS; ChatGPT's review; G7 and G8's code exists; and the owner's written
confirmation of section 11's items A-C (given, 15 Oct 2026), D and E; X of section 1.6 frozen
(its value, sample count, source revision and quantile convention, as stated there); and the go-live date stated in
`FREEZE_v4.md` with its `Frozen on:` line (G8).

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
  / 316. Under E+D: V1 426 / 1,183 (about 1.7 / 4.7 years); V2 396 / 1,099 (about 8 / 22 years). Brier, by band
  (revision 5, at r = 3): V6a 221-631 at n = 125 and 586-1,047 at n = 250, with claim thresholds of 2.6e-14 to 2e-5
  (down to 1.4e-23 at n = 250, 5-7 days). **Such thresholds are effectively unreachable, so V6a, like V1 and V2,
  will almost surely never be claimed.** V6b: 149-206 at the assumed r = 3, only in windows with 5 or more 2% days.
  **These counts assume r = 3; the measured r is far larger (judge 128 addendum 5, on the 2017-26 back-fill): about
  62 for V6b and 87 for V6a**, because one day's Brier difference on a rare 0/1 outcome swings far more than 2% of a
  0.05-0.14 Brier. With the measured noise: **V6b needs about 14-22 years even if its full back-filled skill is real;
  V6a and V1 are effectively unreachable; V2's 8-22 years above are at the assumed r = 3-5, so with real noise it
  needs longer (its r is not measured: V2 has no primary baseline yet). Said plainly: no v4 member is provable in
  useful time; v4 is an honest daily yardstick, not a path to proof** (owner, 21 Oct 2026, response 299 item 9; this
  replaces the earlier "only V6b can be claimed, slowly"). V7 is descriptive-only (5.3; its own VIX null
  is measured in `PROTOCOL_v4_calibration.md` section 3). Other options: `v4_size_study.md`; futility as 5.5.
- **E. Regime dependence (revisions 6-8, judge 98 addenda 6-7; calibration section 4), for the owner.** The regime
  caveat covers **every member's claims and futility, and so the whole of Test A**: a "yes" or "no" from a
  crash-dominated or calm-dominated window measures that regime, not general skill. Revision 8 extends the 5-day gate
  to V1 and V2, so a calm window is undecided for every member (V1's calm-window errors are gone). Measured with the
  gate: every rule holds over 2019-26; the remaining genuine errors are all in the 2020-21 crash year (V6b false "no"
  3.43% and false claims 0.43%; V6a false "no" 2.69%). The owner's options, as the judge framed them:
  1. **Accept**, with every verdict worded "beat the baseline over the scored window" and the window's regime printed
     (mean VIX, 2% days, band).
  2. **Exclude crash windows**, cut frozen now on outcome-side data only. Measured against each kept set's own truth:
     the share cut (more than 10% 2% days) removes those crash-year errors, adds one small one on few series and costs
     13-16% of windows; the VIX cut (mean above 25) costs 8-9% but adds larger errors. Some evidence, one crash.
  3. **V6b descriptive** like V7: no claimable member is left in v4, so Test A could never say "yes".
  No recommendation from me between 1 and 2-share (the measured difference rests on one crash); 3 ends every claim.
  **Decided: option 2, the share cut** (owner, 15 Oct 2026, `docs/DESK_DECISIONS.md`, "G6 item E: option 2"): written
  in 5.3 (`confirmatory.crash_dominated`). Every verdict still prints its window's regime.

Also open to challenge: the family without V3-V5 (5.6), special sessions out (2), V2-V3 on `close_proxy` (1.1), the
5% spread limit and parity forward (1.4), strict "inside" for V5 (1.5).
