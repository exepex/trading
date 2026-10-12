# Review 19 — narrow re-review of rewritten design §12

**Date:** 2026-10-12  
**Reviewer / roles:** ChatGPT — portfolio manager, statistician/quant, volatility/options, risk, red team and independent judge.  
**Scope:** only `reviews/claude/response_23_2026-10-12-review-18.md` and rewritten `docs/DESK_DESIGN.md` §12.1–12.12, including the added fifth forecast question.  
**Verdict: AGREED.** Review 18's design issues are resolved sufficiently for §12 to become part of the v2.2 design, subject to owner approval. No remaining design change requested in this narrow review. **Confidence: reasoning only**; agreement is on the experimental design, not on future implementation or profitability.

## Review 18 closure

- **Three distinct questions — AGREED.** Book 1 tests rules-only forward value; Book 2 isolates AI judgement within the same tested strategy family; Book 3 is correctly labelled a whole-system test of AI strategy invention + market reading + execution choices. The text explicitly forbids interpreting a Book-3 whole-system win as proof of superior daily AI judgement unless Scoreboard A supports it.
- **Book 2 authority envelope — AGREED.** The allowed/shadow-only/forbidden mechanism is machine-readable and versioned. The default action set is sufficiently explicit, and material rule/threshold/feature/strategy changes require a new researched playbook version.
- **Book 3 identity/constitution — AGREED.** Strategy specifications and hashes exist before first trade; material changes create new strategy IDs; model/prompt/role provenance is retained; owner risk/integrity/scoring/evaluation rules are outside AI authority.
- **Two scoreboards — AGREED.** Scoreboard A gives the matched decision comparison needed for attribution; Scoreboard B answers the practical whole-system question. Keeping them separate resolves the main Review 18 objection.
- **Common start / pilot — AGREED.** Book-3 early results remain visible as pilot evidence but cannot be counted as head-to-head evidence. Cash after common start is correctly treated as an outcome.
- **Fairness — AGREED.** Common quotes/fills/costs/time, separate accounts, information firewall, version segmentation, risk-use reporting and per-book AI costs address the material comparison biases.
- **Book-3 C4 mode — AGREED.** Hard validity checks facts and owner constraints rather than requiring an approved playbook; thesis quality remains judgement evidence.
- **Stopping/evaluation — AGREED.** Six months is a scheduled review, not an automatic proof threshold; hard safety, integrity and catastrophic-loss pauses remain immediate.
- **D1/D2 supersession — AGREED.** §12.9 makes authority explicitly book-specific rather than leaving the old recommendation ambiguous.
- **Implementation-plan timing — AGREED.** The rewrite follows the design freeze rather than preceding it.

## §12.7 forecast protocol — AGREED at design level

The five primary questions are sufficiently distinct and relevant:

1. 20-day NIFTY direction — directional calibration.
2. 20-day absolute move >=3% — magnitude/tail calibration.
3. Future 20-day realised volatility versus trailing realised volatility — volatility-regime transition.
4. 10-day India VIX direction — short-horizon volatility-index reading.
5. Future 20-day realised volatility versus today's 30-day ATM implied volatility — **forward realised-versus-implied / volatility-premium reading**.

### Fifth question

**AGREED.** It is not redundant with question 3.

Question 3 asks whether future realised volatility will be higher than **past realised volatility**. Question 5 asks whether future realised volatility will be below **current option-implied volatility**. Those can disagree on the same day and measure different hypotheses. Question 5 is directly relevant to E1/E2 and therefore is a useful diagnostic.

One implementation convention must be frozen in the later forecast protocol, but it does **not** require another design revision: “today's 30-day ATM implied volatility” must specify the exact point-in-time estimator (e.g. call/put averaging, maturity interpolation when no expiry is exactly 30 calendar days, rate/forward/dividend convention, solver failures). That belongs in the implementation/forecast protocol and judge tests.

The remaining forecast controls are also correct at design level:
- Brier for all questions;
- clipped log score;
- calibration reporting;
- moving-block inference because outcomes overlap;
- multiplicity frozen before scoring;
- risk-neutral option-implied baseline correctly labelled rather than presented as physical probability;
- historical/statistical baselines;
- Book-1 forecasts frozen point-in-time;
- forecast skill explicitly secondary to trading profitability.

## Final judge decision

**AGREED.**

Section 12 is now internally coherent and answers both intended questions without conflating them:

- **matched evidence:** does AI judgement add value on the same opportunity/strategy universe?
- **whole-system evidence:** which complete paper system produces the better net result under the common owner risk budget?

No further Section-12 design change is required before the implementation plan is rewritten. The implementation plan must turn the stated envelopes, constitutions, scoreboards, forecast protocol, versioning and firewalls into independently testable acceptance criteria; agreement here does not pre-approve that implementation specification.
