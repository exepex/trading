# Review 140 — Final check of Response 327 (agreed Market School)

**Independent second reviewer, 22 October 2026. Verdict: CHANGES REQUIRED — three small wording/acceptance fixes, not another redesign.** I compared Response 327 against Response 325, Review 138, Response 326 and Review 139. **Strong evidence** means an exact source-contract or arithmetic comparison; **some evidence** means a reported operational observation not independently rerun; **reasoning only** means a proposed operational convention. No real orders.

## 1. Does 327 carry the agreement?

**AGREED on the substantive decisions (strong evidence, document comparison).** Section 2 preserves the separation of account trades and hypothetical tickets, three denominators, matched road-day-slot controls and abstentions, descriptive-only condition map, prospective multiplicity/second-window requirement, no 40-trade licence, calibration as descriptive, PS5/KL1 as controls, width-ladder grouping, calendar payoff checks, spread sensitivity scenarios, first-sealed AI answer, risk-reducing exits, hypothetical-account labelling, and red/amber-only v1. Section 3 correctly includes **both Review 139 conditions**: freeze the pilot's rule/control/road/cost/denominator/cohort/start before day 1, and independently switch paper decisions, futures and capture-only feeds without disrupting v4. No new economic edge or real-money permission is asserted.

**One small omission — CHANGE (strong evidence):** Review 139 expressly required that every capture-only record carry **instrument, contract, expiry, dated lot, source timestamp, first-seen timestamp, raw hash and quality status**. Response 327 P0b names measured operational metrics but drops this record-level witness contract. Add that sentence to P0b. Without it, an early capture archive could be unusable for point-in-time studies or fail to distinguish contract changes. This is a real data-integrity concern, not a new service.

**One imprecise phrase — CHANGE (strong evidence):** P0b says capture probes “use no fresh data window.” New bid/ask records are themselves fresh data; Review 139 said **do not consume a fresh outcome window without an R1 card**. Replace with: “Capture-only observations may be archived with provenance; they do not create tickets, positions, strategy claims or spend a registered fresh *outcome* window. Any analysis that exposes an unused outcome requires an R1 card and DATA_SPEND update first.” This prevents both accidental spending and the false impression that collecting new quotes is forbidden.

## 2. Build order, gates, effort and dates

**AGREED on P0 → P0b → P1 → P2 → P3+ as a dependency plan (reasoning only).** P0 terms/probes before expanding capture is correct; P0b can run **in parallel with P1 development** once P0 passes, provided it cannot interfere with v4 or the pilot. The staged 4-index-monthly plus NIFTY-weekly 15:00 pilot, controls and five rule-driver *families* match Response 326/Review 139. A road failing quote-readiness stays closed rather than contaminating other roads.

**P1 acceptance — CHANGE one missing test (strong evidence):** Review 138/139 explicitly required **all refused and unavailable opportunities to remain in the original decision denominator**, not just separate three counts. Response 327 P1 says “tickets with three counts” and lists zero unsealed/over-cap/invented/duplicate fills, but its gate does not say **zero dropped refusal records or silent missing road-day decisions**. Add to the P1 gate: “Every scheduled road/driver decision has a sealed trade, no-trade, refused, closed-road or unavailable outcome with reason; missing and refused opportunities remain in the correct denominator. Plant a refused entry and verify it survives replay and both reports.” Otherwise an apparently high fill rate can be created by disappearing failed attempts. Keep the already agreed planted stale/missing quote, seal, lot/expiry, impossible-price and replay checks.

**Arithmetic (strong evidence):** 4 index monthlies + NIFTY weekly = **five road classes**, not five independent market days. Over 95% across ten sessions means, for a road with exactly one required complete snapshot each day, **10/10** valid days; **9/10 = 90%** fails. If a road requires multiple contract-leg observations per day, define the scheduled snapshot/leg denominator before counting; do not turn missing legs into a passed aggregate. The 10-session readiness window is operational evidence, not statistical power. Thirty forward sessions are descriptive only.

**Effort (reasoning only):** P0 **3 builder + 1 judge**, P1 **10–18 builder + 5–8 judge** is a plausible estimate but omits a separate P0b effort estimate and the cost of P2's reporting/review. Add **“P0b and P2 effort: to be measured after P0; not included in the P0/P1 estimates.”** Do not claim a fixed total. Late-November first counted session and mid-January descriptive review are plausible *scenarios*, not commitments; 30 NSE trading sessions can be later due to holidays, missing valid sessions or a delayed P1 gate. Define the P2 review as **30 valid counted forward sessions after the registered start**, not simply 30 calendar trading sessions since launch.

## 3. Owner decisions in §5

**AGREED on the decision categories (strong evidence).** Final sign-off; futures policy; report sections; drawdown restart; and possible second Groww key cover Response 325's owner questions and Review 139's future activation condition. A second key is optional and subject to Groww's permitted usage; P0 must not assume it.

**Futures “five numbers” — CHANGE the heading (strong evidence):** Section 5 calls these “five futures numbers,” but **(d) overnight/same-day is a policy choice, and (e) refuse an over-limit lot is a mandatory rule, not a number**. Make the requested fields explicit:
1. **₹ maximum planned stop loss per lot** (number);
2. **₹ maximum stress/gap loss per lot and ₹ per futures account** (two numbers);
3. **₹ maximum notional, ₹ margin use, and ₹/risk maximum total concurrent exposure** (three numbers, units specified);
4. **Overnight allowed: yes/no**, and if yes, permitted holding horizon (policy);
5. **Over-limit minimum lot: automatically refuse** (fixed rule, not discretionary).

No futures driver starts until these values are approved, dated and checked against actual contract lots and gap scenarios. The owner cannot set a stop price that *guarantees* a worst-case futures loss; overnight gaps can exceed stress examples. The NIFTY arithmetic is correct: 22,811×65=₹1,482,715; 1%=₹14,827.15; 5.9%=₹87,480.19 before fees.

**One additional clarification (reasoning only):** §5's report-section approval is required **before P1 changes the signed-off 08:50/20:05 pages**, although it does not block P0. The drawdown restart policy must be settled before any driver can enter a suspended state. A second key does not block the pilot if existing API quotas suffice.

## 4. Remaining desk-role risks

**Risk manager / portfolio manager (strong evidence):** A 1% futures stop is not a hard loss cap; keep futures disabled until owner policy and exam gaps are tested. Independent driver paper accounts are not additive deployable capital.

**Statistician / quantitative modeller (strong evidence):** A control that trades every eligible road can make matched comparisons interpretable, but the 5 roads remain correlated; no licence, Supported/Confirmed cell or green banner from 30 sessions. A fixed reference rule must be selected before the first counted day and obey the same data and risk constraints.

**F&O / options strategist / volatility / execution (some evidence):** Four index captures are reported to exist, but their full quote freshness, lot/expiry and fillability on all five roads are **not independently established** by inventory. Per-road readiness is the correct gate. Weekly and monthly expiry must not be confused.

**Data engineer / red team (strong evidence):** Missing decisions/refusals and missing first-seen timestamps can create false performance or look-ahead. Add the two concrete tests/fields above; no new platform.

**Regulation / market research / macro / derivatives flow / equity research / tax-cost accountant / behavioural / head of desk (reasoning only unless noted):** P0 must verify source terms, dated charges and NSE settlement rules; major event-day closures must be disclosed; no backfilled outcome can become a forward trial; do not present simulated wins as trading permission. These do not justify expanding P1.

## Exact changes required

1. **P0b:** restore capture provenance fields and replace “use no fresh data window” with the precise no-*outcome-spend* rule. **Strong evidence: Review 139.**
2. **P1/P2:** add a sealed decision/refusal/no-trade completeness test and explicit denominator; define P2 as 30 valid counted sessions. **Strong evidence: Reviews 138–139.**
3. **§5 / estimates:** distinguish futures numeric limits from policy choices and mandatory refusal; mark P0b/P2 effort unestimated, and state the report-section approval precedes P1 report changes. **Strong document comparison; reasoning-only schedule convention.**

**Final: CHANGES REQUIRED (three small edits).** Otherwise Response 327 accurately consolidates the agreement and is ready for the owner's final review. No broader architecture, extra statistical service or additional strategy family is needed.
