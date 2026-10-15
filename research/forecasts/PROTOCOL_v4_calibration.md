# Forecast protocol v4, part 2: calibration of the claim and futility rules

**Part of `PROTOCOL_v4.md`** (split out at 350 lines, ChatGPT review 101); frozen with it, same status: **DRAFT, not
frozen**. Section numbers refer to `PROTOCOL_v4.md` section 5. Evidence labels as the project uses them.

**What "held-out" proves (judge 98 addendum 3):** fresh seeds measure Monte Carlo error only, on the same exposed days;
they prove nothing about other periods. Every empirical null here is built from **exposed** NIFTY data (disclosed in
`PROTOCOL_v4.md` section 8).

## 1. The claim rule (5.3), revisions 2, 4 and 5

**Rule E+D, revision 2** (owner decision "3 B", 15 Oct 2026; judge 98 addendum 2;
   `confirmatory.calibrated_p`, `tools/v4_claim_thresholds.py`). A member claims at a look only with **at least 12
   whole batches** and a **batch-means t** p-value (the latest floor(n / L) batches of L, Student t with batches - 1
   df) **at or below its worst-case calibrated threshold**. The threshold is computed at the look for the member's
   actual n by the frozen tool: the smallest, over the member's null group, of the p-quantile at rate / 15 (taken at
   its 95% lower confidence rank) from 100,000 seeded mean-zero series. Each group is Gaussian i.i.d., AR(1) 0.5 and
   overlapping nulls plus an **empirical null from exposed 2024-26 NIFTY data** (circular 20-session blocks of centred
   baseline-vs-baseline differences, right-skewed orientation). V1 and V2 use QLIKE nulls (trailing 5 vs 20 sessions),
   V6a and V6b Brier nulls (EWMA-normal vs base rate), and V7 borrowed V6b's (superseded by section 3: V7 is descriptive-only).
   **Why:** QLIKE differences on real data have a raw skew of -17 to +15 and a batch-mean skew of up to 7.5, against
   2.8 for the lognormal case (some evidence: exposed data, a few baseline pairs). Rare crash days dominate the mean,
   so most windows without one favour the forecaster that under-forecasts. On those nulls, revision 1's
   max(batch t, studentized bootstrap) rejected **6-18% at Holm's first step 0.0013** at n = 125 for L = 5 and 10,
   still 7.5-10% at n = 250. A divisor of 10 still gave 2-13%; Hall's skew correction did not help. The bootstrap's
   1 / 10,001 resolution cannot reach the thresholds needed, so it is dropped from the rule. **Measured size of E+D**
   (held-out seeds, 100,000 series): within nominal + 2 Monte Carlo SE in all 30 cells (5 questions, n = 2L, 125
   and 250, both looks); fewer than 12 batches gives no claim at all. **What "held-out" proves:** fresh seeds
   measure Monte Carlo error only, on the same 2024-26 days; they prove nothing about other periods. Tables:
   `research/forecasts/v4_size_study.md` (every option) and `v4_claim_thresholds.md`.
   **Brier members, revision 4 (judge 98 addendum 3; `tools/v4_brier_regimes.py`):** the 2024-26 Brier thresholds
   broke on 2019-26 data, because a low-probability forecaster "wins" every calm day with a tiny SE. V6a, V6b and V7
   are therefore calibrated on **every exposed regular session with a valid base rate (15 Jan 2019 to 14 Oct 2026)**.
   A **calm stress** adds the calmest 125 and 250 sessions (13 Apr - 12 Oct 2021 and 6 Oct 2022 - 10 Oct 2023, no 2%
   day in either). A Brier member is **judged (claim or futility) only when its scored window holds at least 5 2%
   days** (`confirmatory.brier_judgeable`); otherwise it is not judgeable at that look (p = 1, open, never "no").
   Without the gate V6b's claim size is up to 62-99%; with it every cell holds. Judgeable: 53% of 2019-26 windows at
   n = 125, 90% at n = 250, none in the calm stretches. **Revision 5 (judge 98 addendum 4;
   `tools/v4_brier_bands.py`, `confirmatory.event_band`):** one threshold per question over-rejected 2-4x in windows
   with only 5-7 2% days, because the count is known before the verdict. So each band (5-7, 8-12, 13+ days) has its own
   claim and futility thresholds, calibrated on nulls conditioned to that band (200,000 series). Every band holds:
   claims and false futility, n = 125 and 250, both looks (held-out). Revision 1's calibration
   (`v4_null_calibration.md`) is superseded (some evidence only below 0.01). The studentized bootstrap,
   revision 0's centred bootstrap and a Newey-West HAC t are reported sensitivities, **never used to choose a
   result**.

## 2. The futility rule (5.5), revision 3

**Rule F+D, revision 3** (`confirmatory.futility_p`, `tools/v4_futility_study.py`; a false "no" gets the
   false-"yes" standard). On the gate set, with e_t = d_t + margin x b_t, "improvement below the minimum effect" is
   mean(e) > 0. A member is **futile at a look only with at least 12 batches and a batch-means t p-value for it at or
   below its worst-case calibrated threshold**: the 2.5% quantile (at its 95% lower confidence rank) over both
   orientations of the empirical null shifted to a true improvement exactly equal to the minimum effect, computed at
   the look for the member's n. 2.5% per look (Bonferroni 2 x 2.5%); futile at look 1 is final. **Measured (held-out,
   100,000 series; `v4_futility_study.md`):** F+D's false-futility rate is 0.0-2.6% in all 16 cells (V1, V2, V6a,
   V6b; n = 125 and 250; both orientations; tolerance 2.60%). Revision 1's bootstrap bound (F0) said a false "no" in
   **23-32%** of cases for V1 and V2 and 7-17% for V6a and V6b, against 2.5%: it is reported only. Strong evidence for
   the measured nulls, some evidence for future data. V7 borrowed V6b's threshold (superseded by section 3). The Brier members
   use revision 4's gate and 2019-26 thresholds (5.3). Across members, "every member futile" is an
   intersection-union claim (Berger 1982). These rates are for a mixed 2019-26 window; inside one regime see section 4.

## 3. V7's own VIX null (revision 6, ChatGPT review 101; `tools/v4_vix_null.py`, `v4_vix_null.md`)

- **Null:** every exposed regular session with a valid base rate (18 Jan 2019 - 7 Oct 2026). V7's Brier difference of a
  rival is compared with the 750-session base rate. The rival is the base rate conditioned on VIX being above or below
  its 20-session mean, point in time. The loss differences are nearly symmetric (skew 0.26). Series are resampled in
  circular 20-session blocks, in both orientations, over the full period and inside the calmest and most volatile 125
  and 250 sessions by mean VIX (calmest: 16 Jul 2025 - 16 Jan 2026 and 21 Apr 2023 - 26 Apr 2024; most volatile:
  28 Feb - 31 Aug 2020 and 2 Mar 2020 - 2 Mar 2021). 200,000 series per null.
- **Rules measured, at n = 125 and 250 and both looks:**
  - R0: V6b's NIFTY 2%-day gate and bands, borrowed.
  - R1: V7's own threshold, with no gate.
  - R2: V7's own thresholds per mean-VIX band (below 13, 13-17, above 17).
- **Result: none holds.**
  - Worst claim size: R0 0.5-14%, R1 5.8-20%, R2 1.2-25%. Nominal is 0.13-0.20%.
  - Worst false futility: 13-80%.
  - R1 does hold on the full period: claims 0.11-0.12%, futility 2.4-2.5%. It fails only when the window sits in one
    regime. A calm year gives false claims of 5.8-16.8%; a volatile half-year gives a false "no" up to 65%.
  - So V7's skill comparison depends on the regime, and a 6-12 month window cannot settle it (strong evidence for the
    measured nulls).
- **Decision (ChatGPT review 101's alternative):** V7 is **descriptive-only in v4**. Its three family slots stay at
  p = 1: it never claims, is never futile, and is not counted in Test A, so it can neither claim nor block a "no"
  (`terms.DESCRIPTIVE_ONLY`). A later version may bring it back with a regime-robust rule.

## 4. Every member inside one regime (revisions 6 and 7; `v4_regime_stress.md`, `v4_crash_cut.md`)

**The caveat (judge 98 addendum 6), for every member's claims AND futility.** Inside one regime the full-period null's
local mean is far from zero (inside the 2020 crash V6b's is -0.33, larger than its full SD of 0.21), so the forecaster
really is better or worse there, and any consistent test follows that regime. **A verdict measures skill over its
scored window's regime, not general skill.** This covers V1, V2, V6a and V6b, claims and "no" alike, and so the whole
of Test A: a Test A "yes" or "no" from a crash-dominated or calm-dominated window measures that regime. Every verdict
therefore prints its window's regime (`regime.window_regime`: mean India VIX, 2% days, band; G8 criterion).

**Method (`tools/v4_regime_stress.py`).** Each member's null over every exposed 2019-26 regular session (from 15 Jan
2019) is resampled in circular 20-session blocks over the full period and inside the busiest and the calmest 125 and
250 sessions by 2% days: busy 16 Dec 2019 - 18 Jun 2020 (36 2% days, mean VIX 30.6) and 31 Jan 2020 - 2 Feb 2021 (44,
27.5); calm 13 Apr - 12 Oct 2021 (0, 16.0) and 6 Oct 2022 - 10 Oct 2023 (0, 13.2). Both orientations, n = 125 and 250,
100,000 series per cell, operative thresholds unchanged. "local" is the true relative improvement inside the stretch:
a "no" is false only where local is at least the minimum effect, a claim only where local is at most 0.

**Futility (the judge's must-fix (a)), worst rates, target 2.5% (tolerance 2.60%):**

| member | full 2019-26 | busy stretches: false "no" / regime truth | calm stretches: false "no" / regime truth |
|---|---|---|---|
| V1 | 0.00-2.25% | 0.00-0.46% / none above | **6.81%** (n = 125), **2.93%** (n = 250), calm 2021, local +0.21 / 4.51-11.44% (calm 2022-23, local -0.13) |
| V2 | 0.00-0.78% | 0.00-0.10% / none above | 0.00-1.96% / 13.71-41.42% (calm 2022-23, local -1.27) |
| V6a | 0.00-2.16% | **2.69%** (n = 125, busy 2020-21, local +0.24) / 10.27-35.97% | not judgeable (0% of windows) |
| V6b | 0.33-2.00% | **3.43%** (n = 125, busy 2020-21, local +0.31) / 12.65-99.88% | not judgeable (0% of windows) |

**Claims, worst false rates (local at most 0), nominal 0.133% (tolerance 0.156%):** V1 **0.85%** (n = 125) and
**0.66%** (n = 250) in calm 2021, where the forecaster is locally 18% worse; V6b **0.43%** and **0.20%** in busy
2020-21 (flipped, locally 30% worse); V2 and V6a within. The full period holds for every member (V1 and V2's 2024-26
thresholds hold on 2019-26: claims at most 0.05%, futility at most 2.25%).

**Read plainly (some evidence: exposed data, one crash, two calm stretches):**
- The rules are sound over a mixed 2019-26 window and not inside one regime. Most large rates are regime truth (the
  forecaster really is better or worse there); the bold ones are genuine errors even against that regime's truth.
- **V1 in a calm stretch is the worst genuine error:** a false "no" 6.81% against 2.5%, and false claims 0.85% per
  slot; three V1 slots could reach about 2.6% by the union bound, against look 1's 2% (reasoning only: slots are
  correlated, so the true union is lower).
- **Test A "no"** needs every counted member futile (intersection-union, 5.5). In the calm stretches the Brier members
  are never judgeable, so they block a "no"; in the busy stretches V1 and V2 say "no" at most 0.46%. So a false Test A
  "no" in these stretches is at most the smallest counted member's rate (reasoning on measured marginal rates; the
  joint rate is not measured). If only V1 and V2 were counted, calm 2021 would give at most 1.96%.

**Item E's option 2 measured (`tools/v4_crash_cut.py`, `v4_crash_cut.md`).** Two cuts, outcome-side only, that would
make a crash-dominated window not judgeable for every member: mean closing India VIX above 25 (2019-26 mean 17.1), or
more than 10% 2% days (base rate 4.15%). Cost on the real rolling 2019-26 windows: the VIX cut removes 7.6% (n = 125)
and 8.9% (n = 250), all starting Aug 2019 - May 2020; the share cut removes 12.6-15.7%. V6b's judgeable share falls
from 50% to 43% / 37% (n = 125) and from 78% to 69% / 63% (n = 250). Full-period rates barely move. **Inside the crash
year the cut makes things worse:** V6b's false "no" (n = 125, busy 2020-21) rises from 3.43% to **10.41%** (VIX cut) and
**16.00%** (share cut); its false claims from 0.43% to 1.31% and 2.10%; V6a's false "no" from 2.69% to 7.57% (VIX
cut). The cut keeps the calmer part of a crash year, whose own median measured improvement is mostly below the minimum
effect (-0.19 to +0.06): the regime dependence moves to the next regime instead of going away. Neither cut touches
V1's calm-window error. **Option 2, as measured, does not fix the problem and costs 8-16% of windows** (some evidence).

**Revision 6's V6b busy stress** (`v4_brier_busy_stress.json`) is kept and agrees: claims up to 44% / 91% and a "no" up
to 86% / 99.9% inside the 2020 crash, all regime truth by the measure above.
