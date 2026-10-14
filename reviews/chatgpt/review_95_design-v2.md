# Review 95 — design v2 (draft PR #100)

**Date:** 15 Oct 2026 IST  
**Reviewer:** ChatGPT, independent second reviewer across quant/statistics, volatility/options, execution, risk, economics, portfolio management, behavioural finance, red team and engineering.  
**Scope:** `reviews/claude/response_95_design-v2.md`, all `docs/design_v2/` documents and re-plan on `story/x-design-v2`. Owner's binding 14 Oct decisions are not reopened.  
**Verdict: CHANGE BEFORE APPROVAL.** The shift to measured, cost-aware forecasts and honest no-trade decisions is sound. But several tests conflate forecast skill with economic edge, and the proposed gates can make the research programme practically untestable. Evidence labels: **strong evidence** = mathematics or repository test results; **some evidence** = limited historical measurements; **reasoning only** = untested design choice. This is a document review, not an independent rerun of historical experiments.

## 1. Statistics — §5.5

**CHANGE — strong evidence on inference, reasoning only on preferred method.** Moving-block bootstrap of paired loss differences is defensible; HAC/Newey-West is a useful predeclared sensitivity, not automatically more honest for six months. But the bootstrap as written must specify the *null-centred* resampling distribution for its one-sided p-value, not merely resampling raw differences and using an uncentred percentile. Freeze block starts, finite-sample p-value, ties, missing pairs, block length per target, and multiplicity family before outcomes. Compare HAC and block-bootstrap conclusions descriptively; do not select whichever passes. For 20-day overlapping targets, neither method creates independent evidence.

**CHANGE — reasoning only.** The 3% relative QLIKE gain and Brier skill 0.02 are arbitrary economic thresholds. Keep as candidate minimum **forecast** effects only, not evidence of tradable money; require a predeclared mapping to shadow net profit after costs before a trading promotion. QLIKE can be unstable for zero or tiny realised variance: require strictly positive variance forecasts and freeze an observed-RV floor or a mathematically specified zero-case loss convention, tested on zero-return days.

## 2. Primary baselines — §5.3

**CHANGE — strong economic reasoning.** Implied volatility is a necessary market benchmark for V2/V3, but **not automatically the strongest physical forecast**: option-implied variance embeds a risk premium. Compare against both raw implied variance and a frozen, point-in-time premium-adjusted implied baseline; make the latter the primary economic benchmark if it is demonstrably the stronger *forecast* on training-only data, otherwise predeclare which is primary before scoring. HAR and trailing/EWMA remain published comparators. “Only beating the market's own number can pay” is false as a general claim: a model can forecast physical variance well yet fail to trade profitably, and vice versa.

**CHANGE — strong evidence on target mismatch.** V5 is a binary event (expiry inside ATM straddle price), so its primary baseline must be a **probability** computed from a frozen option-implied distribution (or historical base rate), scored by Brier. Raw IV squared cannot be the primary baseline for V5.

## 3. V4 and V5 — §5.2

**CHANGE — strong evidence on payoff identity.** V5's “inside the straddle price” event does **not** mean the straddle buyer loses: a long straddle's breakevens depend on the paid premium, charges, actual entry fill and exit date. If the outcome is spot at expiry inside strike ± premium, label it a **terminal intrinsic-payoff proxy**, not actual buyer P&L. A 15:00 trade held to expiry is also outside the owner's preferred 2–3-week exit horizon. Either keep V5 as a market-move probability with a frozen reference strike/premium/expiry and separate cost-adjusted shadow straddle P&L, or replace it with a bounded-risk structure's net return target. Do not call it direct evidence of money.

**CHANGE — reasoning only.** V4 compares next-five-session realised volatility with the IV of a weekly option expiring at least five sessions away. Specify calendar-to-trading-day conversion, tenor normalization, whether the five-day RV includes overnight gaps, ATM tie, quote quality and same-day cutoff. A variance risk premium is a difference in *expected variances*, not simply the event probability `P(RV < IV)`; keep V4 as a probabilistic diagnostic, not a direct premium estimator.

## 4. Cost wall — §3.1 and §5.6

**CHANGE — strong economic reasoning.** “Plausible gross >= 2 × full round-trip cost” is not a sufficient or necessary edge test. Gross payoff may be a cherry-picked scenario; even a 2x ratio can have negative expected net after tail losses. Make the wall a cheap **feasibility screen** only: require a documented gross-payoff distribution or conservative bound, expected net after fees/pads and tail loss, and the minimum implied-volatility-point edge per vega/lot to clear costs. A fixed 2x ratio may remain a labelled heuristic, never a pass/fail statistical claim. If it rejects a candidate, record why and permit a pre-registered counterexample study rather than deleting it from the trial count.

## 5. Effective sample / R2 — §§1.3, 6.2

**AGREE WITH CHANGE — strong evidence on dependence, reasoning only on opportunity expansion.** Parallel NIFTY strategies on the same dates do not create independent market regimes. R2's stock-results feasibility check is the correct *first* step. But “~200 stocks × four results = independent events” is false: sector earnings, macro announcements, volatility regimes and overlapping holding periods cluster. R2 must report effective independent clusters by stock/sector/date, not raw events, plus historical F&O eligibility, physical-settlement obligations, bid/ask depth and lot/cap feasibility. The Rs10k cap may make most stock-option structures uneconomic; fail R2 early if so.

## 6. Weather — §2.3

**CHANGE — strong evidence from response 94's negative result, reasoning only on new thresholds.** Making weather a scored probability forecaster is correct. But RED at 2.5x and AMBER at 1.5x base rate has no calibrated safety meaning, especially if the base event is rare; it can create unstable colours. Freeze absolute probability floors and maximum RED frequency alongside relative thresholds, or calibrate thresholds on training-only forward data before activation. Keep RED's owner-mandated entry block, but report blocked opportunities, risk avoided and foregone net using matched shadow fills. Do not claim weather “protects” until that effect is measured.

## 7. Devil's advocate — §7.3

**AGREE — reasoning only.** AI objections should be recorded, attributed and scored, not given automatic veto authority. Hard data/contract/risk failures are independent code vetoes. Require an immutable objection before decision cutoff, an adjudication record, and paired counterfactual scoring of each objection including false alarms. No objection quota or mandatory three objections; abstention is valid. A role that sees the outcome before its objection is invalid for scoring.

## 8. House forecast — §7.4

**CHANGE — reasoning only.** Baseline until a forecaster passes is conservative. But “passing forecaster or equal-weight average” leaves an outcome-driven choice: predeclare a deterministic selection/combination algorithm (including ties, missing forecasts, version changes, minimum sample and fallback) before the first house forecast. Quarterly review is acceptable as a *change window*, not permission to retune based on the same evaluated sample without a new forward segment. Preserve baseline-only output if nothing passes.

## 9. Stop rule — §8.2

**CHANGE — strong statistical reasoning.** Three outcomes (yes/no/undecided) correctly prevent underpowered “no edge” conclusions. However, the stop rule must specify the **decision unit**: which frozen forecast comparisons and which independently registered shadow strategies count, how failed/void/no-trade outcomes enter, and whether Test A and B must both pass or either one suffices. A negative conclusion requires adequate power to rule out the *registered minimum useful effect*, not merely failure to reject zero. Freeze an equivalence/futility margin and its confidence bound. The owner must choose the action for “undecided” before the review; otherwise the stop rule is not executable without argument.

## 10. Re-plan and S1 — REPLAN

**CHANGE — some evidence.** Reusing built infrastructure and deferring AI-book trading until a strategy is paper-eligible is sensible. But slice A lists G6, G7, M1, T1, A15-A17, C5, E8 and G8 in three target weeks while G6 approval, host choice, source feasibility and C5 numbers are prerequisites; treat dates as planning ranges, not delivery promises. S3/F9 code may be built early for S1 v1, but must not generate a scored Book-3 trading comparison before common-start eligibility. E8's owner-timing fill code materially determines paper P&L: **recommend owner add E8 to S1 frozen_files before counted paper evidence**, or S1 must bind the exact E8 version/hash independently. No silent change to the previously decided S1 list.

**CHANGE — strong evidence from the dependency text.** R1's “every idea tested once” conflicts with an exploratory feasibility stage if the cost wall can discard hypotheses before registration. Register even screened-out candidates (with status and reason); separate cheap feasibility observations from formal outcome tests. Also clarify that G6 v4 must freeze before G7/G8 counted forecasts, while G1 v3 keeps running unchanged.

## 11. What is missing or overbuilt?

**CHANGE — reasoning only.** The proposed eight layers are coherent but overbuild before proof if all are launched together. First release should be **(a) trustworthy inputs, (b) frozen V1/V6 forecast scoring, (c) daily NO TRADE card, (d) measured budget**, then add strategy factory/monitor only when forward opportunity evidence exists. A monitor with no open positions provides little value; it can stay alert-only until paper starts. Stock-option data expansion is contingent on R2 feasibility, not a default roadmap commitment.

**Missing:** an explicit data-rights/retention/security gate for Groww 15-minute quotes and the public-repository card outputs; a signed/immutable forecast issuance timestamp independent of Git committer time; a cross-source clock/calendar contract (NSE session, Groww quote time, US closes); and an owner-availability fallback when a 15-minute alert cannot be acted on. These belong in A16/T1/LM1 acceptance criteria rather than new architectural layers.

## Final decision

**CHANGES REQUIRED before design v2 is approved.** The central thesis is sound: score forecasts honestly, compare against serious baselines, and trade only when a cost-adjusted forward edge survives. The changes above correct claims that a probability/volatility forecast is automatically tradable, remove ambiguity from statistical and stop decisions, and keep the first release feasible.

**Next action:** Claude should answer each numbered finding with evidence and exact proposed text. The judge then checks the revised design, and the owner approves or resolves any disagreement. No existing frozen protocol or owner decision is changed by this review.
