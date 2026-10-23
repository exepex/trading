# Review 138 — Market school design (Response 325)

**Verdict: CHANGES REQUIRED.** The goal is sound: the system should make and record paper decisions and learn from forward evidence, rather than requiring the owner to invent trades. The proposed 410-road, four-slot, 36-driver first build is over-built and contains material risk/statistical errors. **Evidence labels:** strong evidence = checked repository contract, arithmetic or statistical principle; some evidence = limited observed study; reasoning only = prospective design choice. I read Response 325, EDGE1, Response 324 and the owner's context; I did not rerun NSE/Drive data or rate-limit probes. No real orders.

## 1. Account trades versus tickets — PARTIAL

**Strong evidence:** Separate hypothetical idea quality from funded paper-account returns. A ticket with no valid two-sided quote, sufficient size, valid contract or bounded payoff is **not an executable opportunity**. Apply the same ₹10,000 contractual max-loss, dated lot, costs and quote-validity rules to tickets; relax only account-level cash/bucket limits. Report eligible decisions, fillable opportunities and executed fills as different denominators. Do not add ticket rupees to account P&L. Otherwise the instructor learns from impossible trades.

## 2. Same-road comparison — CHANGE

**Strong evidence:** A median across only drivers who chose to trade a road is selection-biased. “75% lost” can mean the selected strategies were poor, not that the road was hard. Return on risk across different structures is not automatically comparable. Start with **same road, same slot, same day paired after-cost differences against a frozen control**, reporting abstentions and missed fills. Cluster by session and overlapping holding periods. A mixed model with road/day effects is a possible *later descriptive sensitivity*, not a fix for selective participation. **Reasoning only:** do not build it now.

## 3. Condition-map FDR and Confirmed — CHANGE

**Strong evidence:** Benjamini–Hochberg FDR 10% controls an expected fraction of false discoveries among selected claims under assumptions, **not** a 90% chance each Supported cell is true. Thousands of overlapping cells, repeated 13-week rechecks, dependent drivers and selected second windows invalidate a naive one-look guarantee. Three drivers sharing market data are not independent confirmations. BR1 already found false-positive inflation under market dependence; its “6–42 effective bets” is not transferable to this grid.

**Rule:** v1 map statuses **Exploratory / Watching / Not established** only. For Supported/Confirmed later, freeze a finite economic family, one primary metric, prospective start, untouched second window and empirically check false-claim rates on realistic date/holding-block nulls. A map cell alone must never authorize real money.

## 4. Licences and calibration — CHANGE

**Strong arithmetic:** At a 50% outcome rate, 100 independent Bernoulli observations have standard error sqrt(0.25/100)=**5 percentage points** and approximate 95% uncertainty **±9.8 points**, before clustering. Ten confidence buckets have roughly ten observations each. Thus “calibration error ≤10 points after 100” is not a reliable pass. Forty trades on 30 sessions are not 40 independent bets; an **80% confidence interval** is too permissive for selecting among dozens of drivers.

**Recommendation (reasoning only):** Learner→paper-active after plumbing/risk tests, without an economic licence. At ≥100 resolved opportunities across ≥60 sessions publish only exploratory five-bin reliability, Brier versus a frozen base rate, counts and uncertainty. A recommendation licence needs a prospective sample/power plan, a multiplicity-adjusted **one-sided 95% lower bound of paired after-cost advantage >0**, and a second untouched forward window. If the power plan takes years, say “not established”; no automatic licence from 40 trades.

## 5. Driver catalogue — CHANGE

**Strong evidence:** EDGE1 did not find a profitable protected monthly rule. PS5 (failed BANKNIFTY fly) and KL1 (known loser) are **controls only**, not promotable candidates. PS2–PS4 are a width ladder, not independent discoveries. PS8 repeats unsuccessful volatility filters. FT4 and FT5 are competing gap hypotheses, not independent evidence.

**Critical arithmetic:** A NIFTY future at ₹22,811 with lot 65 has notional **₹14,82715** (₹1,482,715); a 1% stop is **₹14,827** before costs, already over the ₹10k rule. A 5.9% overnight gap is **₹87,480**. For a stock future at ₹1,500×500, a 1% stop is ₹7,500 but a 4% gap is **₹30,000**. A stop is not a maximum loss. **Do not activate FT1–FT7** under the current hard cap without an explicit owner decision to accept gap risk; prefer defined-risk options. CD1–CD3 also need a verified payoff/margin model across expiries: “max loss = debit” is not a universal calendar rule. Stock F&O physical settlement is a real risk.

**Pilot:** NIFTY monthly options at 15:00 only; one capped seller, one capped debit buyer, one directional debit spread, RC1 random control and N0 no-trade. All unproven, including any rule from EDGE1. No five AI personalities or 200-stock fleet yet. [Reasoning only.]

## 6. Simulator 75th-percentile spread penalty — CHANGE

**Strong evidence:** No historical bid/ask for the 2019–26 close series. A 75th percentile learned from later quotes is a *scenario*, not validated historical execution. It can understate crisis spreads or overstate normal spreads. **Show median, 75th and stressed 95th-percentile forward spread scenarios**, each with source dates and counts, plus no-fill cases for unavailable size. If fewer than 30 distinct quoted sessions in a bucket, say “insufficient spread data.” Simulator remains **practice-only**; never license from its results. [Threshold reasoning only.]

## 7. Claude API and non-determinism — PARTIAL

**Reasoning only:** Decide transport after a five-session workload dry run, not by model brand. Start rule-only; introduce one AI after captures and accounts work. Record exact model/prompt/pack hashes, timestamps, temperature, transcript, tokens and cost. The **first sealed answer** is the scored production decision. Repeated identical-input dry runs measure agreement, not independent trades. Report structure/strike agreement, risk-rule disagreement, latency, misses, calibration and cost per usable decision. Never replace an unfavourable first answer with a later one.

## 8. Daily stop — CHANGE

**Strong evidence:** Stop new entries at the ₹25k per-driver daily drawdown. But “closing a capped option spread only adds cost” is **false**: a valid close can reduce remaining exposure. Equally, forced closing into a thin quote can worsen losses. Continue planned exits and permit validated risk-reducing closes, never invent a fill. Keep the aggregate fleet loss and exposure visible: 36 independent ₹25k driver stop levels sum to **₹900k** of hypothetical loss triggers, not one deployable owner budget. Independent paper accounts must not be represented as one affordable fleet.

## 9. Green banner — CHANGE

**Strong evidence:** RM1 has no demonstrated passing driver and its current evidence rules name Book 1. Replacing that with “driver version” is a substantive owner/judge decision, not a simple rename. Calibration of profit *frequency* is not positive expectancy: 90% wins of ₹100 and 10% losses of ₹2,000 yield **−₹110 per trade**. **No green in v1.** RED = missing data/risk/no eligible trade; AMBER = paper research only. A future green requires an independently approved, versioned real-money gate with forward executable net evidence and no unresolved risk issue, then should mean “eligible for independent manual review,” not “buy.”

## 10. Cuts for one judge — CHANGE

**Strong arithmetic:** MS0–MS10 estimates **71–95 builder + 36–42 judge = 107–137 person-days**. One judge at five days/week needs **7.2–8.4 weeks** solely for judgement, before rework. The proposed November launch dates are not evidence-based.

**Cut first:** 200-stock chain surveys (~800 NSE calls/day); stock/index futures; five AI drivers; four slots; generalised historical simulator; Greeks attribution and 13 root causes; thousands of condition cells, licences and regime CUSUM; dashboard expansion and green banner. **Reasoning-only scope choice:** first deliver a **one-index/one-slot** NIFTY monthly paper pilot reusing existing C2/C4, fills, O9 and forecast reports. Estimate **8–15 builder + 4–7 judge days** depending on reuse. Require 10 clean capture/replay sessions before activation and 30 forward sessions before a *descriptive* review, not an economic licence.

## 11. Hidden fleet risks — CHANGE

**Strong arithmetic:** 410 roads×4 slots = **1,640 road-slots/day**. 36 drivers×5 entries×4 slots = **720 potential account entries/day** before exits; 36×₹20 lakh = **₹7.2 crore hypothetical capital**. At 200 NSE chain requests per slot and 1/1.5 seconds, survey takes **300 seconds (5 minutes)** per slot before retries. A 3.5-minute Groww estimate is not an end-to-end capacity guarantee.

**Risks:** selected-driver bias; reuse of the same quoted depth by many independent paper accounts; look-ahead in event/condition tags; exchange and broker access terms; repeated recommender selection overfitting; aggregate tail risk; stock physical delivery; correlated AI answers; outages concentrated on volatile days; and maintenance overwhelming research.

**Pilot acceptance:** 10 consecutive market sessions with >95% complete time-valid captures; zero unsealed booked decisions, over-cap trades, invented or duplicate fills; all refusals retained. Plant one stale quote, missing seal, thin leg and replay conflict. After 30 forward sessions publish net per original opportunity and the matched control, with uncertainty. No licence from 30 sessions.

## Cross-role challenge

**Mathematician/options strategist:** bounded payoff, dated lots, real charges; futures stops do not bound gap loss. **Statistician/quant modeller:** matched road-days, prospective test families and sample power; FDR and 80% intervals are not proof. **F&O/volatility trader and execution:** spreads, displayed size and overnight gaps dominate small theoretical edges. **Risk/portfolio/head of desk:** ₹10k cap, no naked legs, no aggregate fleet presented as deployable capital. **Market research/macro/flows/equity/investment banking:** common shocks correlate roads; publication times must precede decisions. **Regulation:** check NSE/Groww automated-access terms and physical settlement before expanding. **Behavioural:** avoid a green banner for unproven trades. **Tax/cost accountant:** dated charges, taxes as disclosed assumptions. **Data engineer/red team:** fail closed on missing quotes, seals, stale contracts and replay.

## Final decision

**CHANGES REQUIRED before MS0–MS10.** The school should generate and learn from automatic **paper** decisions, but the initial fleet is far too broad and its statistical licensing is not defensible. Build a **NIFTY monthly, 15:00, rule-only, write-once pilot** first; expand only after measured data quality, cost and operational success. Do not unfreeze the entire desk or amend RM1 for a green banner before forward economic evidence. Biggest way this recommendation could be wrong: broad parallel exploration may discover niche effects that a narrow pilot misses, but breadth cannot substitute for independent evidence.
