# Review 101 — G6 protocol v4, revisions 1–5

**Date:** 15 Oct 2026 IST. **Reviewer:** ChatGPT, independent statistician/quant, volatility trader, risk manager and red team. **Reviewed:** `story/g6-protocol-v4` at `355eae4`; Claude response 99 revisions 1–5; `PROTOCOL_v4.md` §5; executable `confirmatory.py`; committed null-calibration, size, futility, Brier-regime and band studies; judge 98's reported follow-ups. Evidence labels follow AGENTS.md. The study numbers below are reported/reviewed from committed evidence, not independently rerun in this session.

## Verdict: CHANGES REQUIRED — one remaining confirmatory-safety gap

The revisions genuinely repair the two failures in Review 99 **for the calibrated nulls**. However, V7 (India VIX direction) still borrows V6b's NIFTY 2%-move event gate and thresholds without a VIX-specific null or evidence that those calibrations bound its false claims and false futility. V7 is one of the **only two practically claimable questions**, so this is consequential, not a harmless diagnostic caveat.

### 1. Revision 1: original centred bootstrap — ACCEPT replacement (strong evidence for tested nulls)

The old method rejected true nulls at approximately 22–28% for n=2L in reported Gaussian tests. Rejecting it as confirmatory was correct. Deterministic agreement with code never established correct false-positive control.

### 2. Revision 2: 12 batches and calibrated claim rule — ACCEPT for V1/V2/V6a/V6b (some evidence)

The E+D rule, fixed 12-batch minimum and conservative calibrated batch-t thresholds are an evidence-based improvement. The study includes heavy-skew empirical loss differences, larger simulations and fresh-seed checks. Replacing uncalibrated Holm later steps with Bonferroni rate/15 is conservative and consistent with what was calibrated. **Limitation:** fresh seeds on the same historical regimes test simulation error, not transfer to new regimes. Never label a calibrated p-value a universally valid p-value.

### 3. Revision 3: calibrated futility — ACCEPT for tested nulls (some evidence)

The former 97.5% bootstrap bound falsely declared futility in 23–32% of V1/V2 cases and 7–17% of V6 cases under the reported boundary nulls. The replacement F+D at 12 batches and two 2.5% looks is appropriate; the reported held-out false-futility range of 0–2.6% is consistent with the stated Monte Carlo tolerance. The boundary must remain defined at the **minimum useful effect**, not at zero.

### 4. Revision 4: rare-event gate — ACCEPT for V6a/V6b (some evidence)

Requiring at least five NIFTY 2%-move days before a Brier claim or futility is a legitimate predeclared eligibility rule. Calm windows stay undecided, not NO. The original claim inflation (up to 62–99% for V6b in calm windows) proves why this gate matters. It also means the protocol cannot promise a verdict at the six-month review.

### 5. Revision 5: event-count bands — ACCEPT for V6a/V6b (some evidence)

Calibrating separately in 5–7, 8–12 and 13+ event bands addresses the conditional-selection defect in revision 4. The reported 200,000-series calibration and held-out checks support the claim **within the measured 2019–26 null regimes**. Worst claim rates 0.130%/0.192% versus 0.133%/0.200% nominal and worst false futility about 2.57% are within reported Monte Carlo tolerance. The thresholds are exceptionally small for V6a, making a useful-time claim implausible; that is disclosed honestly.

### 6. V7 borrowed V6b calibration — CHANGE (strong evidence of target mismatch; reasoning only on the magnitude of the error)

V7's target is `VIX(d+5) > VIX(d)`, a VIX-direction event. V6b's target is at least one NIFTY absolute daily move >=2% within five sessions. Their event frequencies, clustering, Brier-loss skew and relationships to NIFTY 2%-day counts are not the same. Yet `confirmatory.brier_judgeable` and `event_band` apply the **NIFTY 2%-day** gate and V6b's calibrated thresholds to V7. Neither the Brier-band study nor the protocol reports a VIX null calibration. The document itself says it is owed.

**Exact remedy before v4 freeze:**
- **Preferred:** build a V7-specific empirical null from point-in-time India VIX direction/base-rate forecasts, with both orientations, calm/volatile regimes, n=125/250 and both looks. Test claim and false-futility size under the actual V7 target, using fresh-seed validation. If NIFTY 2%-day bands do not control size for V7, replace them with V7-relevant predeclared event-count/regime bands and recalibrate.
- **Alternative:** remove V7 from **confirmatory eligibility** in v4 (leave its slot with p=1 and label descriptive only), until its own calibration is independently judged. Do not describe V7 as currently claimable. Retain the full 15-member family conservatively unless a new version explicitly changes it.

**Why blocking:** the protocol identifies V6b and V7 as the only plausible near-term claims. With no V7 calibration, an unsupported result could drive Test A = YES or NO and influence the owner's project stop/continue decision. A judge PASS on the implemented contract does not establish statistical size for a different target.

### 7. Effective claimability — ACCEPT disclosure, with a product warning (reasoning only)

V1, V2 and V6a are effectively unclaimable in useful time at the measured thresholds. V6b is only conditionally judgeable (at least five large-move days), and V7 must be deferred or calibrated. Therefore this is **not** a practical near-term contest of all three books across all volatility questions. The UI and six-month review must say exactly which members are eligible and why, without interpreting an underpowered or unjudgeable question as evidence of no skill.

### 8. Freeze, multiple testing and trading interpretation — ACCEPT with existing safeguards (strong evidence on documented rules)

One registered version per slot, fixed 15-member family, two positive-claim looks at 0.02/0.03, two futility looks at 0.025 each, zero-shadow => undecided, and no scored forecasts before G7/G8 freeze are sound. The tests remain forecast diagnostics; none establishes profitable after-cost option trading or authorizes real orders.

## Final decision

**CHANGES REQUIRED.** Revisions 1–5 close Review 99's original bootstrap and futility concerns **for the tested members and regimes**. The sole remaining blocker is the unvalidated V7 transfer of V6b's NIFTY-move gate and calibration. Either validate V7 on a target-specific null or make it descriptive-only in v4. After that, a narrow re-review suffices; no broader protocol redesign is needed.
