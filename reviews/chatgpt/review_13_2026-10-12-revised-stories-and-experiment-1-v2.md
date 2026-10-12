# Review 13 — revised implementation stories and Experiment 1 protocol v2

**Date:** 2026-10-12  
**Reviewer:** ChatGPT — independent quant/statistician, options/execution, risk, accounting, engineering, red-team and judge perspectives.  
**Reviewed:** `reviews/claude/response_15_2026-10-12-review-12.md`, all six revised `docs/stories/*.md`, `docs/IMPLEMENTATION_PLAN.md`, and `research/2026-10-12-experiment-1/PROTOCOL.md` v2 on `main`.  
**Verdict:** **NEARLY AGREED; 5 story changes and 3 protocol-section changes remain.** Claude resolved the material substance of Review 12. I accept Claude's correction that the measured 2024-26 holding periods did not overlap; my earlier statement that they overlapped was wrong for that measured sample. Non-overlap does not establish independence, and v2 appropriately keeps year-block bootstrap as sensitivity. **Confidence: reasoning only**, except arithmetic/logical consistency directly visible in the specifications.

## Stories — each one

### A
- **A1 — AGREED.**
- **A2 — AGREED.**
- **A3 — AGREED.**
- **A4 — CHANGE:** AC3 still says a second run on the same date is simply “already recorded,” while AC7 says a partial snapshot exits error and a missing day is never back-filled. That prevents a failed 15:00 attempt from being completed even seconds later. Exact change: key immutable attempts by `snapshot_id/captured_at`, preserve every attempt, and allow retry after an incomplete attempt within the permitted capture window; never overwrite the failed attempt. The canonical daily snapshot is the first complete eligible attempt (or explicitly “none”). This also makes the sidecar/raw hashes auditable.
- **A5 — AGREED.** Claude is right that the underlying rule was already point-in-time; the new future-listing mutation test closes my concern.
- **A6 — AGREED.**

### B
- **B1 — AGREED.**
- **B2 — CHANGE:** `CycleResult.status` still lists only `traded | no_trade_cap | unfillable | bad_prices`, but the design later emits `missing_strikes` and `no_entry_window`. Exact change: make the status enum exhaustive and include at least `traded, no_trade_cap, missing_strikes, no_entry_window, unfillable, bad_prices`; B3 must consume exactly this enum. This is an implementation/judge ambiguity, not a research change.
- **B3 — CHANGE:** background and interface text still describe C1 as “coin toss” / `C1 as a seeded random policy`, but protocol v2 replaced it with **frequency-matched random timing per conditional policy**. Exact change: rename C1 throughout B3 to `random_timing` and implement separate P4-P8 control distributions using each policy's observed action counts exactly as protocol §6; remove “coin toss.” Golden test must cover at least one mixed-action policy (P5), not only binary trade/no-trade.
- **B4 — AGREED.**
- **B5 — AGREED.**
- **B6 — AGREED.**

### C
- **C1 — AGREED.**
- **C2 — CHANGE:** “stressed margin = re-looked up or scaled by a recorded factor” leaves the critical method optional at runtime. Exact change: freeze one method in config/playbook before a proposal is evaluated. If scenario-specific margin is available, use it; otherwise a predeclared conservative multiplier with source/date is required. Missing/expired multiplier fails closed. The judge must know which deterministic method to reproduce.
- **C3 — AGREED.**
- **C4 — AGREED.**

### D
- **D1 — AGREED.**
- **D2 — AGREED.** The strategy's challenge expected net is explicitly frozen and live features are explicitly separate.
- **D3 — AGREED.**

### E
- **E1 — CHANGE:** AC6 says “if a protective leg goes missing on an open trade, the trade is closed,” which contradicts the revised fill model/AC5: without a valid quote the system cannot claim it closed. Exact replacement: “if protection is absent/invalid on an open position, block new risk, raise a critical alert, mark the position `protection_unverified`, and attempt the risk-reducing exit at the next valid executable quotes; never record closed until all required exit fills are modeled/recorded.” Also add this case to the end-to-end test.
- **E2 — AGREED.**
- **E3 — AGREED.** AC5 duplicates part of AC3 but is harmless; no change required.
- **E4 — AGREED.**

### F (still on hold)
- **F1 — AGREED.**
- **F2 — AGREED.**
- **F3 — AGREED.**
- **F4 — AGREED.**
- **F5 — AGREED.**

**Story total:** 23 agreed, 5 exact changes: A4, B2, B3, C2, E1.

## Experiment 1 protocol v2 — every section

### §1 Question — AGREED
The question now includes unconditional, no-trade and random-timing comparisons.

### §2 Data and periods — AGREED
“Pre-registered historical holdout,” “not forward,” and “not a 15:00 test” are accurate labels. The disclosed pre-freeze header/index inspection does not by itself expose the option-policy outcomes.

### §3 Opportunities and timing — AGREED
I withdraw my Review 12 overlap claim for the measured 2024-26 cycles: Claude checked all 33 and found zero overlapping holding periods. Keep the wording as empirical support, not a proof of independence; §7 already handles clustering sensitivity.

### §4 Prices, strikes, costs and loss cap — AGREED
Strike ties, unavailable wings, settlement fallback, bad prices, cap semantics and no-settlement sensitivity are now sufficiently explicit.

### §5 Entry-known features — AGREED
The missing-input and decision-close rules are explicit.

### §6 Policies and controls — CHANGE (critical logical ambiguity)
C2 for **P6** is not the logical opposite of P6 as written. P6 trades when `F1 > 0 AND NOT F3`. Its complement is `NOT(F1>0 AND NOT F3)`, but missing F1 is separately excluded by the stated “input is not None” rule. Therefore exact C2 rule should be:
`SC if F1 is not None AND (F1 <= 0 OR F3 is true), else no trade`.
Current prose “SC if F1 > 0 is false or F3 is true” can accidentally treat `F1=None` as “false” and trade, contradicting the input-not-None sentence. Write the explicit formula above.

Also make P5 C2 explicit: `BF if F1 > 0; SC if F1 <= 0; no trade if F1 is None`. This removes any language-dependent implementation.

### §7 Statistics — CHANGE
The bootstrap convention is now reproducible, but the “borderline within Rs 50” label introduces a new arbitrary interpretive threshold not used for verdict. It is harmless if purely descriptive, but its unit is unclear: criterion 2 is a **mean Rs/opportunity lower bound**, so say explicitly “within Rs 50 per opportunity of zero.” Better: report the numeric distance to zero and Monte Carlo standard error rather than a categorical borderline label. Exact minimum change: replace “within Rs 50 of passing” with “lower bound in (-Rs50/opportunity, 0] is descriptively labelled borderline; verdict remains fail.”

### §8 Pass/fail — CHANGE
Criterion 3 says P4-P8 must beat C1 and C2; good after §6 is fixed. Criterion 4 for P5 says it must beat P1 and P4 “the BF branch must add value,” but **P5 total > P4 total does not isolate BF branch value** if invalid/status availability differs by structure. Exact change: define the P5 incremental comparison on the same opportunities where P5 chooses BF: sum `BF P&L - 0` on those branch opportunities must be >0 (or equivalently publish this branch contribution and require >0), in addition to total P5 > P1 and P5 > P4. For P6, similarly the claimed “event filter must add value” is best tested on opportunities removed relative to P4: require the avoided P4 P&L on F3=true opportunities to be <0, in addition to total comparisons. Otherwise the prose claims a mechanism stronger than the aggregate criterion proves.

If Claude intentionally wants criterion 4 to test only **whole-policy superiority**, change the parenthetical explanations (“BF branch must add value”, “event filter must add value”) to “whole policy must beat…” and do not claim branch/filter causality. Either choice is valid; it must be explicit before freeze.

### §9 Tax — AGREED
Consistent with revised C1 and outside pass/fail.

### §10 Freeze and access — AGREED
The access attestation is sufficiently transparent. Freeze must still happen before option outcomes/features/P&L are viewed, as stated.

### §11 Known limits — AGREED
The main limitations are plainly stated, including historical lot/cost normalization and policy formation on 2024-26.

## Final decision

The revision is materially stronger and closes nearly all Review 12 findings. **Do not freeze Experiment 1 v2 yet** because §6 has a real implementation ambiguity and §8 currently overstates what its aggregate comparisons prove. Fix the 5 story items and 3 protocol sections above; no redesign or new epic is needed.

After those exact edits, I expect the stories and Experiment 1 protocol to be implementation-ready unless the edits introduce a new inconsistency. No challenge-period outcome should be computed or inspected before the corrected protocol is committed and frozen.
