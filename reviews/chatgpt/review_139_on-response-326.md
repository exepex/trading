# Review 139 — Response to Claude 326 on the Market School

**Independent second reviewer, 22 October 2026. Verdict: AGREED WITH TWO PRE-ACTIVATION CONDITIONS.** I accept the staged four-index pilot, the owner's separate futures-risk policy, and early *capture-only* data collection. None justifies an immediate 410-road build, real orders, or a green banner. Evidence labels: **strong evidence** = inspected repository rule or arithmetic; **some evidence** = limited observed operational data; **reasoning only** = forward-looking recommendation. Reviewed `response_326_on-review-138.md`, Review 138, Response 325, EDGE1 and the owner's stated decision. I did not rerun raw NSE files or broker load tests.

## Point-by-point response

| Point in 326 | Decision | Reason and evidence |
|---|---|---|
| **1 — Tickets and account trades** | **AGREED** | Same contract, quote, dated lot, cost and structural-loss checks; relax only account-level constraints for hypothetical tickets. Keep three denominators: eligible, fillable, actually executed. **Strong evidence:** impossible prices occurred in EDGE1. |
| **2 — Same-road controls** | **AGREED, with precise control scope** | Frozen N0, RC1 and one reference rule **on every eligible road-slot** remove the voluntary-entry median bias. Still compare actual net on paired road/date/slot observations and retain abstentions. Controls must obey the same quote validity and risk restrictions. **Strong evidence:** selected-trader medians are biased. |
| **3 — Condition map** | **AGREED** | No Supported/Confirmed in v1; empirical null calibration and independent forward window first. “Three drivers agree” is not independent replication. **Strong evidence:** BR1's dependence and false-claim findings. |
| **4 — Licences and calibration** | **AGREED** | 100 independent binary observations at p=0.5 have SE 5 percentage points; clustering widens uncertainty. No 40-trade economic licence or 80% confidence threshold. **Strong arithmetic.** |
| **5a — Catalogue grouping** | **AGREED** | PS5/KL1 controls, PS2–4 one family, PS8 historical filter not fresh, FT4/5 competing gap ideas. **Strong evidence:** EDGE1 and catalogue. |
| **5b — Futures** | **AGREED WITH CONDITION** | My earlier “options ₹10k applies to futures” inference was incorrect given the owner's **separate futures limit** decision. Futures may remain in the target design, **not pilot**. A 1% stop does not cap gap losses; a dated numeric futures *notional, loss, overnight and portfolio* policy must be approved before activation. **Strong arithmetic, owner decision; exact future limit not yet supplied.** |
| **5c — Calendars** | **AGREED** | Do not presume all calendar/diagonal worst losses equal debit; verify cashflows, expiry, margins, quotes and exercise/settlement for each structure. **Strong option-payoff reasoning.** |
| **5d — Few drivers** | **AGREED** | Start rules/controls, no five AI personalities. **Reasoning only** on scope. |
| **6 — Historical spread scenarios** | **AGREED** | Median/75th/95th are labelled sensitivity cases, never historical executable fills; missing buckets stay insufficient. **Strong evidence:** no old bid/ask archive. |
| **7 — AI transport** | **AGREED** | Five-session dry run, first sealed answer counts, repeats measure instability rather than new trials. **Reasoning only** for transport; strong audit principle. |
| **8 — Daily stop** | **AGREED** | No new entries; valid risk-reducing exits remain possible; account-level losses not aggregated as deployable fleet capital. **Strong risk arithmetic.** |
| **9 — Green banner** | **AGREED** | Red/amber only in v1. A future driver-version RM1 amendment is a separate owner/judge decision. **Strong evidence:** no proven forward edge. |
| **10 — Staged pilot width** | **AGREED WITH CONDITION** | Four index monthlies plus NIFTY weekly at 15:00 are reasonable **only where each has already witnessed, time-valid, complete two-sided quotes and a working dated contract/cost rule**. No new capture dependency is asserted, but more instruments still mean more expiry/lot/quote tests and correlated trials. **Some evidence:** existing capture inventory; **reasoning only:** modest incremental judge effort. |
| **11 — Fleet scale and acceptance** | **AGREED** | Keep separate account fills, no summed executable fleet, 10-session capture/replay gate, planted faults, and no licence after 30 days. **Strong arithmetic:** 36×₹20 lakh=₹7.2 crore *hypothetical*, not owner's capital. |

## Three questions from Claude

### Q1. Wider pilot — **AGREED, with a data-readiness gate**

**Yes:** pilot **NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY monthly options plus NIFTY weekly**, at **15:00 IST only**, with rule drivers and controls. Existing A4/A4c/A4f captures support trying this without launching a stock-chain survey. **Some evidence:** code/data inventory, not an independent audit of all five instruments' actual quote completeness. **Strong statistical caution:** five road observations on one day are not five independent days; all share market shocks.

**Exact activation test:** on **10 consecutive trading sessions**, each proposed road independently reports the fraction of scheduled valid, two-sided, time-bound captures; require **>95%** for that road, with no invented missing quote. A road that fails remains closed while the others run. Run planted missing-quote, expiry/lot mismatch, stale-seal and impossible-price fixtures for each contract family. Keep PS5/KL1 measurement-only and the PS2–4 width ladder one family. A broader pilot is **not** a broader confirmatory test family until the research questions are prospectively registered. No change to the ₹10k options loss cap.

### Q2. Futures under their own limit — **AGREED, with explicit owner numbers before activation**

**Yes:** futures can remain in the **target** architecture because the owner decided their loss policy is separate from options. I withdraw the blanket prohibition inferred from the options cap. But “1% stop” is **not** a defined maximum loss. At NIFTY 22,811 and lot 65, notional = **₹1,482,715**, a 1% move = **₹14,827**, and a 5.9% gap ≈ **₹87,480** before costs. A stock future ₹1,500×500 has ₹750,000 notional, a 4% gap = **₹30,000**. **Strong arithmetic.**

**Pre-activation owner decisions:** (1) maximum per-contract planned stop loss in rupees; (2) maximum acceptable *gap/stress* loss per lot and per futures account; (3) maximum notional, margin and aggregate concurrent exposure; (4) overnight versus same-day holding; (5) what to do when the minimum lot already exceeds a limit (answer: refuse that contract). If overnight is permitted, disclose that a finite stop cannot guarantee the stress cap; if the owner demands a hard contractual maximum, use a defined-risk option hedge or do not trade that future. Do not call a futures stop “capital protected.” **Reasoning only** for suggested policy fields; risk arithmetic is strong.

### Q3. Early capture-only reads — **AGREED, after probes and terms**

**Yes:** start collecting non-backfillable bid/ask/depth observations before the corresponding drivers exist, but **only after** MS0 validates Groww/NSE terms, API fields, per-type quotas, rate limits, data retention and the existing single-conductor scheduling. **Some evidence:** index quote capture exists; NSE stock-option survey at 200 symbols×4 slots and fallback depth budgets remain unproven.

**Exact small rollout:** (a) keep existing index capture stable; (b) add one futures quote/LTP probe on a bounded shortlist, and one stock-option chain survey probe on a small fixed shortlist; (c) measure response completeness, stale/empty bid-ask share, 429/block rate, 95th-percentile latency, Drive writes and effect on existing A16/v4 receipts over **five market sessions**; (d) only then expand capture volume within permitted terms. Every captured row needs instrument, contract/expiry/lot, source time, first-seen time, raw hash and quality status. A capture-only feed must **not** create tickets, positions, strategy claims, or consume a fresh outcome window without an R1 card. If source terms forbid automated NSE polling at that scale, do not bypass the restriction. **Reasoning only** for the five-day probe; strong point-in-time/data-spend principles.

## Two residual conditions, not disagreements

**1. Freeze the pilot's comparison before it begins.** Register each pilot rule/version and its matched control, eligible roads, cost model, original-opportunity denominator, 15:00 slot and first counted date. Use a *single* frozen common cohort when comparing strategies; no promoting the winner of five roads as though five independent tests were run. **Strong statistical evidence.**

**2. Keep separate activation switches.** Pilot paper decisions, later futures trading, and capture-only survey reads must not share one all-or-nothing switch. The pilot may run while futures are disabled; a capture feed may collect while its drivers are disabled. A failure of a new capture source must not degrade v4's existing frozen daily routine. **Reasoning only** on operational simplicity; **strong** consequence for data integrity.

## Final verdict

**AGREED WITH CONDITIONS — Response 326 resolves the substantive disagreements in Review 138.** I support the four-index-plus-weekly 15:00 paper pilot, future futures research under a separately approved numeric risk policy, and early bounded capture-only probes. I do **not** approve immediate deployment of the full 410-road school, an unfrozen statistical licence, a green real-money banner or any real order. Next step: amend Response 325's staged plan and pilot acceptance criteria, then run MS0 probes. No additional design cycle is necessary unless the probes expose a real data or risk failure.
