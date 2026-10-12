# Review 12 — implementation plan and Experiment 1
Date: 2026-10-12. Reviewer: ChatGPT (quant, trader, execution, risk, accounting, engineering, red team, judge). Sources: docs/IMPLEMENTATION_PLAN.md; six docs/stories files; reviews/claude/response_13 and response_14; research/2026-10-12-experiment-1/PROTOCOL.md; AGENTS.md. Reviewed main. **Verdict: CHANGES REQUIRED before implementation-ready sign-off or protocol freeze.** Confidence: reasoning only except arithmetic identities; historical results were not independently rerun.

## All 28 stories: agreed or exact required change

### A — data
- **A1 CHANGE:** Replace circular expected-day rule (union of existing files and weekdays) with independently versioned NSE session calendar including exceptional sessions. For each expected dataset/day require present + checksum + schema or a documented, sourced exception; fail on unapproved gaps. File counts alone cannot prove completeness.
- **A2 AGREED:** Normalization and overlap acceptance are appropriately specific; judge must actually rerun the documented 128-day comparison.
- **A3 CHANGE:** Add uniqueness check on (date,expiry,strike,type), source/index-file hashes, and a research-ready completeness gate that fails on missing required session/underlying/VIX rather than silently accepting empty fields. Test deterministic format precedence.
- **A4 CHANGE:** Start early, but capture request/receive time and source quote timestamp per leg, expiry/contract ID, size, quote age, provider, snapshot completeness, failures and raw-response hash. Keep crossed/stale quotes with invalid flag but never count them as executable. A 14:55–15:05 capture window is not proof of a 15:00 fill; prevent silent partial successes and overwrites.
- **A5 CHANGE:** Specify as-of listing cutoff and strike/expiry history so future listings cannot classify past monthly expiries. Compare semantic outputs unless byte-level determinism is explicitly guaranteed.
- **A6 CHANGE:** Record independently sourced *announcement date/time* and effective date revisions, not merely eventual event date; scheduled F3 events must have been announced by decision cutoff. Retrospectively recorded unscheduled RBI events cannot become known-ahead features.

### B — research
- **B1 CHANGE:** F2 must require 250 valid previous VIX closes or return None; F1 needs IV solver failure bounds, strike tie-break and time/price conventions. Mutation tests must include same-day observations after the 15:00 cutoff if used live: a daily close feature is not a 15:00 feature.
- **B2 CHANGE:** Specify calendar edge cases, missing wings, equal-distance strike tie-breaks, four-leg costs, bid/ask direction and unavailable prices. Replace AC5 “no realized loss >Rs10k” with “modeled maximum *terminal payoff* loss plus stated charges/pads <=Rs10k at entry; report and investigate any realized exceedance.” A daily settlement is a valuation proxy, not a fill.
- **B3 CHANGE:** Freeze the hypothesis family and exact bootstrap quantile/seed; count no-trade opportunities as zero P&L in per-cycle statistics; report traded-only statistics separately. Replace vague “bootstrap within 1% of analytical value” with a fixed golden test distribution and independently calculated numeric tolerance. Never round before verdict.
- **B4 CHANGE:** Immutable registration commit/hash and verifiable order before data access, not editable CSV dates alone. Distinguish retrospectively imported 31 trials from prospectively registered ones. Count ten registered rows separately from multiplicity hypotheses.
- **B5 CHANGE:** Freeze protocol, relevant source/code/config hashes and explicit challenge-access attestation before anyone *reads* challenge outcomes, not merely before results are committed. Report missingness/exclusions and keep failures visible.
- **B6 CHANGE:** Replace probabilistic “at most expected false survivors” single-test criterion with specified fixed-seed null simulations, family-wise error estimator and tolerance. Never tune a future candidate against Experiment 1's consumed challenge set.

### C — deterministic controls
- **C1 CHANGE:** The example 31.2% x Rs9,000 = Rs2,808 is arithmetically correct, but protocol taxes trade net while C1 taxes account net. Explicitly define deductible operating-cost categories, financial-year treatment and tax base; label 31.2% an assumed scenario, not verified tax liability. Reconcile three ledgers.
- **C2 CHANGE:** Specify account equity, margin source and freshness, reserved cash, mark-to-market, stress aggregation, IV repricing and missing margin fail-closed. Separate Rs30k closed-equity brake from Rs30k stressed-loss limit; define owner restart authorization and re-arm calculation.
- **C3 CHANGE:** Check *each leg's* exchange quote age, positive quantity and bid<=ask, not only file capture age. When exits lack valid quotes, record pending exit and alert; never fabricate a fill.
- **C4 CHANGE:** Independently recompute maximum loss and charges (reference vectors or independent algorithm), not the proposer's same arithmetic; verify immutable raw snapshot hashes and as-of cutoff. Test tampering, absent evidence and override refusal.

### D — playbook
- **D1 CHANGE:** Anchor approved version hashes and owner approval in append-only registry; specify allowed status transitions and restart approval. No “best policy” paper example if nothing passes.
- **D2 CHANGE:** Define ranking from frozen out-of-sample expected net, uncertainty, ties, zero-risk denominator, capital/margin competition and no-trade threshold. Specify whether one-slot limit is per strategy or shared. Do not substitute close-only research features for 15:00 features.
- **D3 CHANGE:** Add stable opportunity/run ID, schema version, code/config/strategy hashes, input availability times, crash-safe atomic append and duplicate-run behavior. Replay must reproduce rejected alternatives and risk reasons too.

### E — paper
- **E1 CHANGE:** Bid/ask snapshots are not guaranteed fills. Define quote-size limits, multi-leg partial/no-fill and protective-leg failure, fill model, idempotent scheduling and restart recovery. Missing exit quotes mean pending exit + alert, never an invented close. A 15:00 paper strategy needs separate validation from next-day-close backtest.
- **E2 AGREED:** Minimal report is testable; judge compares rendered numbers with records and channel isolation.
- **E3 CHANGE:** Add explicit gate >=3 months AND >=20 *completed* independent positions, predetermined review dates, unresolved-position handling and no promotion on inconclusive evidence. Measure no-fill and legging costs, not just median half-spread.
- **E4 CHANGE:** An active-desk config flag does not prevent concurrent processes. Add account-scoped single-writer lock/lease and simultaneous-start refusal test.

### F — on hold
- **F1 CHANGE:** Specify full FindingCard schema, availability cutoff, missing evidence behavior, model/prompt/input hashes; post-cutoff claims fail.
- **F2 CHANGE:** Record independent model/version and author provenance; every objection must be resolved with evidence or visibly open, never silently dismissed.
- **F3 CHANGE:** Define audit sample/denominators, seeded known-answer cases and response to failed audit. Overrides cannot bypass C4.
- **F4 CHANGE:** Define counterfactual execution/fill model, matched opportunity/capital constraints, abstentions, uncertainty estimator and predeclared role-removal threshold. Reusing actual fills for a different shadow trade is invalid.
- **F5 CHANGE:** Account for retries, shared calls, credits, currency conversion and missing invoices; specify 5% reconciliation denominator and zero-spend behavior.

## Five questions answered

1. **Missing or unjustified?** Six epics cover the approved areas; no new epic needed. But explicit point-in-time 15:00 provenance, immutable research registration, independent validity, execution realism and account concurrency are missing *within* stories. F is justified only while on hold.
2. **All criteria testable? NO.** A1's calendar is circular, B2 confuses payoff bound with realized losses, B3 has ambiguous bootstrap tolerance, B6 uses a random one-off pass condition, C2 margin is unspecified, E1 assumes fills, F4 lacks counterfactual mechanics. Exact fixes above.
3. **Order? AGREED WITH ADJUSTMENTS.** A4 and B4 start immediately alongside A1; finish A5/A6/C1 before experiment run; B5 only after verified A1/A3/B1-B4. D3 schema should precede C4 implementation (which records its validity), avoiding a runtime design loop. AI last and on hold.
4. **A4 early? AGREED.** Historical bid/ask snapshots cannot be recovered reliably from daily close files. They measure quotes, not executable fills.
5. **Can implementing agent and judge avoid guessing? NO.** A2 and E2 are agreed; **26/28** require the exact amendments above. The plan is a useful blueprint but not yet a complete implementation contract.

## Experiment 1 protocol (response 13): CHANGE BEFORE FREEZE

**Agreed:** protected SF/SC/BF, explicit width search, three predeclared features, eight policies plus two controls, zero-trade alternative, discovery/challenge separation, conservative paper-only promotion. Claude's Rs16,159 condor median is an unverified reported measurement, not reproduced here.

1. **Multiplicity error (critical):** P1–P8 are **eight**, not seven. Predeclare whether P1–P3 are descriptive baselines or promotion candidates. If all 8 can pass, Bonferroni one-sided alpha=0.05/8=0.00625, i.e. **99.375%** lower bound (not 99.3%). If only P4–P8 are candidates, declare five tests and alpha=0.01. Do not choose after seeing challenge data. P5's mixed-structure comparator must be specified rather than automatically comparing to SC-only.
2. **Cycle denominator:** one opportunity per expiry; no-trade, cap, bad-price and unfillable opportunities count as zero in per-opportunity mean/total; publish trade-only metrics separately. Define bad-price handling consistently for all policies and controls. Do not selectively drop unfavorable cycles.
3. **Timing:** F1/F2 use decision-day official *close*, entry next-day close, exit earlier close: label the whole experiment close-proxy, **not a validated 15:00 desk**. F3 scheduled event needs evidence it was announced by that close. Live 15:00 adaptation needs separate forward evidence.
4. **Strike/price mechanics:** specify nearest-strike ties, unavailable strikes, volume/settlement fallback, zero/invalid prices, fee directions and fallback frequency. Settlement prices are not executable bids/asks; report a no-settlement-fallback sensitivity.
5. **Loss cap:** define max terminal payoff loss including entry and assumed exit charges/pads for *each* structure and width; actual exit P&L may exceed that modeled cap from execution friction or legging, and must remain visible. Define whether no feasible wing is no-trade-cap vs missing-data.
6. **Tax:** reconcile protocol's calendar-year 31.2% of trade net with C1's April–March account-profit tax base. Use one explicitly labeled scenario and separate pre-tax promotion tests; do not silently change the pass metric.
7. **Bootstrap:** specify exact percentile convention, resampling unit, seed, handling zero cycles and dependency; monthly cycles overlap in calendar time, so iid cycle bootstrap may understate uncertainty. Report year-block bootstrap as sensitivity (only five challenge years; wide uncertainty) without opportunistically selecting whichever passes. Predeclare whether 10,000 resamples and Monte Carlo uncertainty are sufficient.
8. **Coin toss and opposite control:** define C1's 10,000 seeded sequences, how its percentile compares *total* net to each policy, and treatment of invalid cycles; define C2 opposite as SC only on F1<=0, with missing F1 causing no trade. Clarify whether unconditional P1/P2/P3 must beat their own relevant controls; avoid comparing P5's BF branches to an SC-only benchmark as if matched.
9. **Historical challenge limitation:** 2019–2023 is chronologically earlier than the inspected 2024–2026 period. It can be a **previously unseen, pre-registered historical holdout**, but not a forward out-of-sample simulation of a policy devised in 2026. Require post-freeze challenge-access log and subsequent forward paper evaluation. All prices must be as-of the historical decision date.
10. **Statistical power:** ~60 cycles and a 99.375% lower bound can be extremely hard to pass, especially when policies trade only a subset. That conservatism is acceptable for a *screen*, but failure means **insufficient evidence**, not proof of no edge. Report effective trades, confidence intervals and year concentration. No relaxation after results.
11. **Freeze:** update the protocol and story criteria first, record its commit and code/config/source hashes, then freeze **before challenge data/outcomes are inspected**. If challenge has already been viewed, disclose that contamination and designate a genuinely unused future test rather than claiming pristine validation.

**Decision:** Do not run or interpret the 2019–2023 challenge as confirmatory until these definitions are fixed. Continue archive completeness work and quote capture immediately. No real orders or broker trading.

**What could overturn this review:** independent code/tests establishing a missing convention already fixed elsewhere; provide exact path, version and test output, then I will withdraw the corresponding change. No unverified profitability claim is made.
