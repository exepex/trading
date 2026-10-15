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
   intersection-union claim (Berger 1982).

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

## 4. Disclosure: V6b under a busy-regime stress (revision 6; `v4_brier_busy_stress.json`)

The same regime test was applied to V6b with its revision 5 banded thresholds, inside the busiest 125 and 250 sessions
by 2% days (16 Dec 2019 - 18 Jun 2020 and 31 Jan 2020 - 2 Feb 2021).

- **Claims:** up to 44% at n = 125 and 91% at n = 250, against 0.13%. This is in the orientation where the
  forecaster is better in crashes.
- **False "no":** up to 86% at n = 125 and 99.9% at n = 250, in the other orientation.

The calm stress passed only because calm windows are not judgeable. Read plainly: a V6b verdict from a window that is
mostly one crash measures that crash, not general skill. The rule is not changed in this revision. The choice is the
owner's (protocol section 11, E): accept with this disclosure, exclude crash-dominated windows, or make V6b
descriptive too, which would leave no claimable member in v4.
