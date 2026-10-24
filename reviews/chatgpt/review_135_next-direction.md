# Review: next direction after EDGE1 (on response 322)

**Independent review, 22 October 2026. Verdict: MODIFY Package A, postpone B, and do not raise the ₹10,000 cap.** Keep useful live reports. Build a minimal owner journal before another paper account. Research and paper only; no orders.

**Evidence:** “Verified” means checked against the repository documents, not independently rerun against raw NSE/Drive data. “Some evidence” means limited historical observations. “Reasoning only” means a prospective judgement.

## A. Fact checks

**EDGE1 — verified, strong evidence for the tested rules.** 23 of 24 protected variants failed the 2019–22 cost screen. BANKNIFTY iron fly TP50 passed with +₹1,839 on 21 complete trades, then lost ₹337/trade across 40 complete trades in 2023–26 (p=0.91). The target did not fire in the later 43 entries. EDGE1 explicitly calls its own results *exploratory*, because the history was already spent. This rejects those tested rules, not every possible defined-risk strategy. The ledger's 98 trials are not 98 independent statistical experiments.

**Naked selling — verified, strong evidence for realised sample tails.** NIFTY naked strangle: +₹3,823 average across 43 complete run-2 trades, worst −₹50,332. BANKNIFTY naked straddle: +₹1,584 average across 42, worst −₹84,883. These are observed worst losses, not maximum possible losses: an uncovered short call has theoretically unbounded loss. Positive sample means are not proof of positive future expectation.

**Volatility premium — CHANGE, strong arithmetic; reasoning-only extrapolation.** Response 322's reported IV30 minus trailing RV20 (mean +1.3 vol points, median +2.1, positive on 72%) compares a forward-looking 30-day implied measure with *trailing* 20-session realised volatility. It is not a directly tradable premium. The model sensitivities ₹3,400 per straddle and ₹480 per capped condor per vol point are vega approximations, not expected realised profits. ₹480×1.3=**₹624**, against ₹810–940 costs: illustrative **−₹186 to −₹316** before tail losses. Break-even is **1.69–1.96 vol points** under these assumptions. The cap made *these tested structures* uneconomic, not all possible short-volatility strategies mathematically impossible.

**Lots — verified from LOT_CHECK.** Current Jan-2026 NIFTY lot **65**, BANKNIFTY **30**. Historical lots changed: NIFTY 75/50/25/75/65, BANKNIFTY 20/25/15/30/35/30. Historical tests must use each contract's actual dated lot; historical margin calculations remain unchecked.

**Data spend — CHANGE, verified.** The project's governance forbids a confirmatory test of a *previously examined outcome* on the same history; it does not ban exploratory research. NIFTY 2019–23 option/future 15-minute candles, participant OI features, and some previously unread stock-option outcomes remain available for carefully registered questions. **Fresh OI as a predictor does not make already-exposed NIFTY price outcomes a fresh holdout.** A trading-edge verdict still needs independent future outcomes.

**SEBI — external numbers not independently verified.** The widely reported ~93% loss share for individual equity-F&O traders over FY22–24 is plausible, but I did not read the primary PDF. Do not use the “₹2 lakh average loss”, “87.7% FY26” or “59% same-day-expiry turnover” as verified without primary sources, dates and denominators.

**System status — verified from cut-list.** Book 1 had **zero trades and no registered version** on 21 Oct. The cut-list reports 77,008 production lines, 74,785 test lines, 9,809 tests and 5,705 commits in 11 days. Engineering overhead is substantial; none proves a trading edge.

**C5 arithmetic:** (500−230)×65=**₹17,550 before charges**, about ₹18,400 if ₹850 costs apply. The model price is not a live executable quote.

## B. All 14 directions

**Chance** below is a subjective *low/unknown* ranking of demonstrating a repeatable after-cost edge within 1–3 years, not an estimated probability. Loss figures are payoff bounds or examples before unspecified fees.

| Candidate | Verdict / chance | One-lot loss and honest evidence |
|---|---|---|
| C1 owner journal | **KEEP minimal**; no edge created [reasoning]. | Logging ₹0 risk; real recorded positions have their own risks. Timestamp every prospective decision, quote, skip, fill, cost and outcome. |
| C2 manual paper account | **CONDITIONAL** after owner uses journal; unknown [reasoning]. | Enforce **≤₹10k** defined-risk loss including fees; forward-only 10–20 decisions before extending. |
| C3 sizing | **KEEP existing calculator**; no edge [strong arithmetic]. | 0.5% of ₹20 lakh = **₹10k**; deterministic cap tests, no Kelly sizing without measured edge. |
| C4 IV-regime sale | **DROP build**, low [some evidence against]. | Protected ≤₹10k; F1/VIX/RED filters failed. Only pre-registered forward tests can change this. |
| C5 wider hedged sale | **DO NOT RAISE CAP**, low/unknown [reasoning]. | Example **₹17,550+fees**; broader wings ₹17–30k+. Old price outcomes exploratory only. |
| C6 calendar/diagonal | **DROP**, low [reasoning]. | Example debit ₹6–13.3k, but do not assume every short-near/long-far calendar has maximum loss equal to debit without specifying expiry and settlement. Needs synchronized executable two-expiry quotes. |
| C7 event vol | **DROP trading build**, low [some evidence against]. | Example long straddle **₹13.8k+fees**; ~61 indexed events and earlier event filters failed. Forward event protocol required. |
| C8 expiry day | **DROP for owner**, very low [reasoning + weekly results]. | Naked straddle **unbounded**; bounded spread ≤₹10k if validated. 60-minute owner reaction is ill suited. Fresh 2019–23 candles can test execution feasibility. |
| C9 NIFTY/BANKNIFTY relative value | **DROP**, very low [reasoning]. | Two capped structures may lose **₹20k+** combined; needs synchronized prices and basis/correlation checks. |
| C10 directional forecast trades | **DROP trading use**, very low for current rules [strong evidence]. | Debit spread ₹5–7k+fees; q1 Brier 0.2449 vs baseline 0.2455, p=0.89. Keep forward forecast scoring. |
| C11 participant OI | **ONE optional study**, unknown/low [reasoning]. | **₹0 study trading loss**; freeze one question, release-time lag, baseline and future validation. Historical price outcomes already exposed. |
| C12 portfolio hedge | **CONDITIONAL** on actual stock exposure; insurance, not profit [strong economics]. | Long put loses premium (illustrative ₹15.8k > cap); put spread bounded debit but overall portfolio remains exposed. Measure beta, hedge basis and after-premium drawdown. |
| C13 naked selling | **REJECT** as promotable [strong observed tails]. | Unbounded short-call risk; observed ₹26k–85k worst losses. Already measured historically. |
| C14 stop building | **KEEP as default** without owner participation [reasoning]. | No new trading exposure; retain cheap reports/captures if useful. |

**Missing options:** (1) A **cost/quote feasibility study** before strategy testing: measure bid/ask, displayed size and next-session repricing on forward 15:00 snapshots, not model mids. Research risk ₹0, ~2–3 builder days if capture is reused. (2) A **portfolio-level protective overlay** on the owner's actual Indian stock holdings, with beta and basis mismatch, not a claim of option profit. (3) A **learning/abstention curriculum**: Greeks, payoff bounds, crash replay, expiry rules, slippage, and documented “no trade”; judge by fewer rule errors. More intraday and regime models should wait until their cost hurdle and unused outcome set are established.

## C. Packages A, B, C and my D

**A — MODIFY (preferred base).** Claude's full 6–9 builder + 2–3 judge days are premature with zero desk trades. Start with a **1–2 builder-day CLI/CSV journal** reusing existing reports and C2. Log prospective decision time, price witness, original thesis, trade/no-trade, defined loss, fees, exit and result. Build a separate manual ledger only after **10 genuine decisions** demonstrate usage. Six-week process success: ≥5 complete prospective entries, no backdated fills, no cap violations. Economic results after 30–50 resolved trades are **descriptive**, not proof.

**B — POSTPONE.** One frozen OI study is reasonable if the owner values further research. Example: do extreme FII index-futures positions predict **next-month absolute NIFTY return** better than a predeclared baseline? Use only reports available before each forecast. Historical OI against already-exposed returns is exploratory; only forward results support confirmation. ~3–5 builder + 1–2 judge days [reasoning]. Stop on the registered failure; do not retune.

**C — CONDITIONAL.** Only if the owner supplies portfolio weights, index beta and an insurance budget. Weekly quote-based put/put-spread coverage report; ~2–4 builder + 1 judge days [reasoning]. Success = measured portfolio drawdown reduction per rupee of premium versus no hedge. Stop if one lot overhedges or basis mismatch defeats protection.

**D — RECOMMENDED: “Measure, learn, then build.”** Keep existing morning/evening forecasts, 15:00 captures, scores and frozen desk. Add a minimal decision journal **plus weekly spread/cost feasibility report**, not a new trading engine. ~2–4 builder + 1–2 judge days if code is reused [reasoning]. After six weeks: ≥5 genuinely prospective logged decisions including abstentions, timestamped quotes, no risk breaches. At 10 decisions decide whether to add the manual ledger. At 30–50 *resolved* trades show net per original opportunity, uncertainty, missed fills and charges; no statistical skill claim. **Stop** on non-use after six weeks, fabricated/backdated fills or any attempt to bypass cap. Continue B0 only if it does not restart the frozen desk or require substantial upkeep.

## D. Should wider hedged short selling use a ₹17k–25k cap?

**For:** wider wings cost less, retain more credit and keep *contractual* loss bounded, unlike naked calls. A forward-only research diagnostic could measure quote feasibility. [Some evidence for mechanics, reasoning for edge.]

**Against:** model vega ~₹900 per vol point ×1.3 points ≈ **₹1,170**, against ~₹850 costs: illustrative **₹320 before tail losses**. One ₹20k loss wipes out about **62** such ₹320 gains; two wipe out 125. This is not an observed edge. More collateral and risk, spent historical outcomes, and ~12 monthly observations per year make meaningful confirmation very slow. [Strong arithmetic, reasoning-only expectation.]

**Decision: NO increase now**, including for a promotable paper shadow. A labelled **research-only payoff diagnostic** can examine hypothetical wider risk without altering production C2/C4 gates, if nearly free to run. Any genuine wider-cap paper experiment later needs a separate explicit owner decision, versioned limits, isolated accounts and a frozen stop rule. No real-money inference.

## E. Recommendation and biggest way it could be wrong

**Choose D (a smaller A).** **Strong evidence:** tested protected EDGE1 rules have no robust net edge; naked variants breached the cap; engineering overhead is high and Book 1 has no trades. **Some evidence:** short-option premium exists but is sensitive to friction and tail losses. **Reasoning only:** a small journal plus cost report can improve decision discipline and reveal whether the owner uses the system.

**Biggest risk of this recommendation:** an untested, genuinely executable **defined-risk** strategy with wider wings or better timing might retain enough premium after costs to justify its risk. Avoiding a forward test could miss it. That possibility is not evidence to relax limits now.

## F. Disagreements with Claude

1. **Cap “makes premium uncapturable”: CHANGE.** Vega×IV–trailing-RV is not expected P&L; EDGE1 rejects tested policies, not all protected strategies. [Strong reasoning.]
2. **“Only forward tests remain”: CHANGE.** Untouched intraday quantities and stock-option outcomes remain; fresh predictor ≠ fresh outcome. [Strong: DATA_SPEND.]
3. **Build full Package A immediately: CHANGE.** Zero book trades and large dormant code argue for proving journal usage first. [Strong status; reasoning on scope.]
4. **OI as only clean historical index test: CHANGE.** OI is a fresh feature but prior index outcomes are exposed. [Strong factory rules.]
5. **C5 as next shadow: PARTIAL disagreement.** Bounded wings are safer than naked sales, but tiny modeled edge and long sample horizon do not justify a cap increase. [Strong arithmetic, reasoning policy.]
6. **Exact SEBI loss/turnover figures: UNVERIFIED.** Obtain primary reports and denominators before quoting them. [Not independently verified.]
7. **Positive naked sample mean implies positive future premium: QUALIFY.** 35–44 trades with one ₹50k–85k loss cannot settle tail expectancy. [Some evidence.]
8. **50 journal trades positive → real-money gate: CHANGE.** Positive small samples are not proof; RM1's independently frozen gates remain binding. [Strong statistical reasoning.]

**Agreement:** preserve no-naked rule, risk sizing, useful live reports, anti-overfitting data-spend governance and owner control. No further large research architecture without a concrete measurable need.

**Sources:** `reviews/claude/response_322_next-direction.md`; `research/edge1/{RESULTS,PROTOCOL,LOT_CHECK}.md`; `research/{LEDGER,DATA_SPEND,FACTORY_RULES}.md`; `docs/DATA_USE_MAP.md`; `reviews/claude/response_318_cut-list.md`; `AGENTS.md`. Raw Drive files, the full IV/RV CSV and primary SEBI PDFs were not independently rerun/checked.
