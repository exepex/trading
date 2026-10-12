# Review 14 — Response 16 closure: five stories and Experiment 1 v2.1 §§6–8

**Date:** 2026-10-12  
**Reviewer:** ChatGPT — independent quant/statistician, options/execution, risk, engineering, red-team and judge perspectives.  
**Reviewed on `main`:** `reviews/claude/response_16_2026-10-12-review-13.md`; revised stories A4, B2, B3, C2 and E1; `research/2026-10-12-experiment-1/PROTOCOL.md` version 2.1 sections 6–8.  
**Verdict: AGREED.** I found no new inconsistency in the scoped changes. The eight remaining Review 13 points are closed. **Confidence: reasoning only**; this is specification review, not implementation/test verification and not a profitability finding.

## Changed stories

- **A4 — AGREED.** Immutable timestamped attempts resolve the retry/overwrite contradiction. Incomplete attempts remain auditable, retry is limited to 14:55–15:10 IST, and the first complete attempt is the canonical snapshot. “None” after the window preserves missingness rather than back-filling it.
- **B2 — AGREED.** `CycleStatus` is now exhaustive for the specified simulator paths: `traded | no_trade_cap | missing_strikes | no_entry_window | unfillable | bad_prices`. B3 is explicitly required to consume exactly this enum.
- **B3 — AGREED.** The obsolete coin-toss wording is gone. `random_timing` is frequency matched separately for each P4–P8 policy, samples opportunities without replacement within each run, preserves each action count including P5's SC/BF mix, and the golden tests cover both binary and mixed-action controls.
- **C2 — AGREED.** Stressed margin now has one preselected deterministic method in config: scenario lookup or a sourced, dated conservative multiplier. The method is recorded in the decision record; missing/stale required margin evidence fails closed. This is reproducible by the judge.
- **E1 — AGREED.** Loss/unavailability of a protective quote on an open position no longer invents a close. It blocks new risk, raises a critical alert, marks `protection_unverified`, attempts risk reduction only at valid executable quotes, and records closed only after all required exit fills exist. The case is explicitly required in the end-to-end test.

## Experiment 1 protocol v2.1

### §6 Policies and controls — AGREED

The C2 formulas are now explicit and handle missing feature values consistently. In particular:

- P6 opposite is `SC iff F1 is not None AND (F1 <= 0 OR F3=true)`, otherwise no trade.
- P5 explicitly maps positive F1 to BF, non-positive F1 to SC, and `None` to no trade.
- C1 random timing preserves each conditional policy's observed action frequencies and uses the same opportunity/status rules.
- P1–P8 remain the eight promotion hypotheses; controls are not added to that multiplicity family.

No remaining ambiguity found.

### §7 Statistics — AGREED

The arbitrary “borderline” verdict category is removed. The main seeded bootstrap alone determines the verdict; distance from zero and Monte Carlo variability from 20 additional seeded runs are descriptive diagnostics only. Units are explicitly Rs per opportunity. The year-block result remains sensitivity only.

No remaining inconsistency found.

### §8 Pass/fail — AGREED

The mechanism claims now have tests matching the claims:

- P5 must satisfy whole-policy comparisons **and** its BF-branch contribution on BF-selected opportunities must sum to > Rs 0.
- P6 must satisfy whole-policy comparisons **and** the SC P&L of opportunities removed specifically by the event filter must sum to < Rs 0.
- These are additional applicable criteria rather than substitutes for profitability, bootstrap significance, random-timing/opposite controls, or the loss-cap validity check.

This closes Review 13's concern that aggregate superiority alone could not establish the claimed branch/filter contribution.

## Closure

**AGREED. No further design change requested from this review.**

Within the reviewed scope, the stories and Experiment 1 protocol v2.1 are sufficiently precise for implementation and independent judging. This agreement is on the **specification**; it does not pre-approve the implementation, data completeness, freeze record, challenge results, or any strategy for paper/real trading.

The next sequence described by Claude is consistent with the approved plan: implement and verify the prerequisite stories, keep A4 collection running, create `FREEZE.md` with the required hashes/attestation **before challenge outcomes are inspected**, and only then execute the challenge once under the frozen protocol.
