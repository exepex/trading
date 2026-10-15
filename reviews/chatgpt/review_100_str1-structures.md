# Review 100 — STR1 one- and two-leg structures

**Date:** 15 Oct 2026 IST. **Reviewer:** ChatGPT, independent options trader, strategist, risk manager, execution and judge. **Target:** STR1 branch `story/str1-structures` at `0ba5edcc35321d3e037fcdd0e7029303e881801e`. Read response 112, story STR1, builder response 106, judge 106 and the relevant B2/C2/C4 code. **Overall: PARTIAL — acceptable to merge as a structure-enabling change, but not to activate any new structure in a strategy before the gates below.** Evidence labels: **strong evidence** = algebra or directly inspected code/judge probes; **some evidence** = limited reported live NSE sample; **reasoning only** = untested operational judgement. I did not independently rerun the judge's full suite.

## 1. Money safety, maximum loss, margin and zero-margin exception — PARTIAL

**ACCEPT the present C4-gated path (strong evidence).** B2 refuses uncovered short legs; C4 independently checks shapes and bounded loss; judge 106 planted 54 naked-short cases across codes and found all refused. B2/C4 maximum-loss calculations matched independently recomputed examples to the paisa. The broker-check gate refuses unapproved new-code margin rows. Bought-only LC/LP may have zero *additional* exchange margin because their paid premium is separately debited/reserved; zero is forbidden for codes with sold legs. Frozen SF/SC/BF results were independently reproduced.

**PARTIAL, not an unconditional safety guarantee (strong evidence).** `fno/risk/margins.py` looks up margin from `TradeTerms.structure`; `TradeTerms.bought_only` is inferred solely from that string. A hand-built two-leg PCS mislabelled LC can therefore obtain the LC zero-margin row in **C2 alone**. Judge 106 correctly notes C4's independent shape gate blocks it in the current E3 path. The claim “no path can understate margin” is too strong while C2 accepts unvalidated labels. A future caller that invokes C2 but skips C4 would be unsafe.

**Exact condition before any new code is activated:** enforce a single orchestration gate requiring a recorded C4 PASS bound to the exact proposal hash/legs, margin row and head snapshot before order creation/paper fill. Add an integration test that bypass attempts cannot open a trade. Better follow-up: have C2 derive bought-only status and the structure shape from legs rather than trust `structure` alone, with an independent C2 shape/coverage test. Until then, **C4 is the safety boundary**, explicitly documented and tested; do not describe C2 as independently safe against mislabelled proposals.

**Trader limitation (reasoning only):** bounded terminal payoff does not guarantee realised loss stays under the cap when legs fill separately, exit quotes disappear, or stock options are physically settled. STR1 is NIFTY-only today; downstream E4/E5/E7 tests still matter.

## 2. Bought-option stressed margin at 1.45 — PARTIAL

**ACCEPT as a temporary conservative reservation, not as accurate capital use (strong evidence).** For a paid long option whose SPAN scan equals NOV = premium and exposure is zero, the current formula gives `max(0,1.45×premium-premium)=0.45×premium` of *extra* stressed margin. Judge's real-file example: LC scan/NOV Rs35,174.75 => **Rs15,828.64 extra**. This is not a broker margin requirement and biases S2's “per rupee tied” capital-efficiency comparison. It can reject otherwise feasible bought options even though their terminal loss is capped by paid premium.

**Exact replacement before using stressed capital as an economic benchmark:** distinguish `broker_margin`, `premium_cash_paid`, `stress_loss_reserve` and `total_funds_at_entry`. For LC/LP, broker margin after premium payment is **zero**, premium paid plus charges is the cash requirement, and stressed total loss cannot exceed that already-paid premium plus charges. Do not add 0.45×premium again as blocked funds. For verticals, do **not** simply set stressed margin to zero: recompute with exchange-recognised offset/margin and bound any internal stress-loss reserve by the position's independently calculated worst terminal loss, without counting premium twice. Freeze and hand-test both C2 and C4 and keep the broker-check gate. The current over-reservation is acceptable while codes remain unapproved; it should not become a permanent S2 denominator.

## 3. ATM PCS/CCS default versus 3%-OTM credit spreads — PARTIAL

**REJECT ATM as the presumed economically superior default (reasoning only; some evidence on price/cost samples).** Selling the ATM put/call has high directional exposure and can consume much of the Rs10,000 max-loss budget. Selling ~3% OTM reduces initial directional exposure but also reduces premium and may be less viable after bid/ask and fees. Neither is proven better; response 92's 3%-OTM put spread was a **proposal**, not a successful untouched trial. Do not silently change STR1's code semantics after its regression tests.

**Exact decision:** **ACCEPT ATM as an explicit mechanical code definition for STR1, not as the default trading strategy.** Any 3%-OTM PCS/CCS variant gets a separately versioned structure parameter/code, a registered cost feasibility screen and fresh forward shadow test. Compare identical expiry, width, lot size, fees, 60-minute owner delay, worst loss, margin and exposure; record no-fill opportunities and use the cumulative multiple-testing family. Neither variant may enter an approved playbook merely because it exists in B2/D2.

## 4. Missing before a strategy uses LC/LP/verticals — PARTIAL

**Strong evidence from judge 106:** E4 opening/unwinding/time exits were probed for LC, PCS, CCS, PDS, but **E5 exit review and E7 expiry settlement were not tested** with one/two legs. Those are mandatory activation tests, not optional minor cleanup.

**Exact activation checklist (reasoning only unless noted):**
1. **E5:** each of LC, LP, CDS, CCS, PDS, PCS has a registered exit-rule test (profit/time/event), partial/missing quote, gap across a session, and independent exit-price/cost calculation. Exit refusal must leave a visibly open position, never invent a close.
2. **E7:** long single option expiry worthless/in-the-money, each credit/debit vertical with both legs expiring, holiday-shifted expiry, settlement-source provenance, charges and zero residual position. Test the 1–2-leg path separately from four-leg cases.
3. **E4/E8:** multi-leg atomic/no-fill/partial-fill treatment and the owner's R=60-minute decision delay, including next-session price gaps; credit spreads must not leave a naked short after a failed hedge.
4. **C2/C4/A14:** real broker check for each new margin code/width; a new code is ineligible until explicitly covered. The shared `passed_on` date is ambiguous for incremental approvals: use per-code approval dates or a clearly versioned all-code approval snapshot. Missing/stale margins fail closed.
5. **Strategy economics:** run the cost wall and register every hypothesis before looking at its outcome. Respect spent 2019–26 NIFTY history; use forward shadows for fresh evidence. The Rs10,000 loss cap is per actual selected width/lot, not a guarantee for LC/LP at ATM. Record tail/gap/legging losses separately.
6. **Capital/accounting:** separate paid debit, net credit, exchange margin, stressed reserve, fees, and realised P&L; report cash used and margin held without double counting. Do not use the 1.45 over-reservation as “actual capital tied” in benchmark claims.

## Final decision

**PARTIAL on questions 1–4.** STR1's new shapes and judge-tested C4 boundary are acceptable as *inactive infrastructure*. No new strategy is approved or made tradable by this review. **Before activation**, require E5/E7/E8 coverage, broker margin checks, C4-gated orchestration, and corrected capital-use reporting. The ATM credit spreads remain mechanical definitions, not recommendations. These are targeted downstream requirements rather than grounds to discard the implementation.
