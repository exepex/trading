# Review 1: Backtest analysis and Claude strategy proposal

- **Reviewer:** ChatGPT
- **Date:** 2026-10-12
- **Repository:** exepex/trading
- **Reviewed branch/commit:** main at `30cfdbdbeae0a0af67b209f4db2589f6dfd7c8a0`
- **Instructions applied:** [AGENTS.md](../../AGENTS.md)
- **Reports:** [Backtest analysis](../../reports/2026-10-12-backtest-analysis.md), [Claude strategy proposal](../../reports/2026-10-12-claude-strategy-proposal.md)
- **Supporting material:** [JSON summary](../../reports/2026-10-12-backtest-analysis-data.json), simulator, option model, charges configuration, report generator and backtest tests.
- **Status:** Independent review. Proposed strategy parameters and acceptance thresholds are research hypotheses, not approved configuration changes or demonstrated profitable strategies.

## Verdict

Build the research framework, but do not treat either the failed backtest or Claude's preferred selling strategy as established trading evidence. The direction of the redesign is sound; its profitability claims and experimental comparisons need stronger evidence.

The two reports on GitHub are byte-identical to the uploaded versions reviewed earlier. This review adds checks of the repository JSON and selected implementation files. Professional roles below are analytical perspectives, not claims of a personal NSE trading track record.

## 1. Verified findings

**Confidence: strong evidence from inspected repository files and arithmetic.**

| Finding | Evidence and consequence |
|---|---|
| The reported loss reconciles | Exit totals, instrument totals and gross loss minus charges all equal **-₹1,90,017**. |
| Controls do not report matching completed samples | Rules: **211** trades; opposite direction: **205**; always bullish: **209**; always bearish: **207**. Reconcile this before calling it a matched 211-trade comparison. |
| 270 sessions are not 270 independent market days | The report sums sessions across nine instruments: **9 × 30**. They share market shocks. |
| Open positions are excluded from headline P&L | The simulator records an unfinished-position count rather than including their liquidation values in account equity. |
| Actual contract expiry is not tested | The simulator sets `expiry = "2999-12-31"` and separately prices an imaginary option starting with 10 days remaining. |
| Stops are checked at bar closes | It uses the underlying's five-minute close and a theoretical option value, not an executable option quote. |
| Configured option-sale STT is current | `config.yaml` specifies **0.15%**, consistent with NSE's April 2026 schedule. There is no basis to accuse this run of using 0.10% without further evidence. |

Sources: [simulator](../../fno/backtest/simulator.py), [option model](../../fno/backtest/option_model.py), [report generator](../../fno/backtest/report.py), [JSON summary](../../reports/2026-10-12-backtest-analysis-data.json), [configuration](../../config.yaml), [NSE STT schedule](https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax).

### Control reconciliation

Different exit paths may leave different trades unfinished at the cutoff. That could explain the counts; the discrepancy is not proof of misconduct or necessarily incorrect control generation. However, excluding remaining positions differently makes completed-trade totals incomplete comparisons.

**Required correction — strong evidence:** retain every original entry identifier, account for its outcome in every control and value remaining positions at a common cutoff. Separately run complete competing policies through their own capital, cooldowns and position limits.

The JSON is an aggregate summary, not a trade-level audit trail. The original price dataset and control-generation implementation were not present in the inspected repository tree. The original control results were therefore not independently reproduced.

## 2. Independent diagnosis

**Perspectives:** mathematician, statistician, F&O trading and execution.
**Confidence: some evidence.**

This specific chart-rule policy lost heavily under the chosen synthetic-option model during one falling-market period. That is credible diagnostic evidence against continuing the unchanged setup. It does not isolate whether the dominant problem was direction selection, contract choice, holding period, pricing assumptions or execution.

The stop/target settings did not produce their advertised payoff ratio: winners averaged ₹3,646 and losers ₹3,791. Break-even win rate is **50.97%**, versus the observed **38.9%**.

A stop occurring on the first five-minute bar is not necessarily a fill at the open. The ₹1,39,991 lost by that subgroup is not an isolated measurement of overnight-gap damage.

**Required correction — strong evidence:** separate previous-close-to-open movement from open-to-first-bar movement, and distinguish theoretical marks from executable fills.

The existing no-look-ahead test uses an `AlwaysBullish` synthetic rule. It is useful, but does not establish point-in-time correctness for all actual rules, historical news, option chains and contract selection.

## 3. Agreements with Claude

**Framework recommendations — strong evidence from the inspected limitations.**

- Use one shared account and portfolio risk engine.
- Replace global voting with separately specified, testable setups.
- Measure account money kept, including open positions and operating bills.
- Use actual contracts and option-market observations.
- Keep chronological validation and an experiment register.
- Permit the outcome "no viable strategy found."
- Introduce AI after the deterministic core works.

## 4. Disagreements with Claude

| Claim or proposal | Assessment |
|---|---|
| Retail losses establish an advantage for option sellers | **Reject — strong evidence.** SEBI reports traders using options, not exclusively buying them. Its loss statistics do not establish profitable protected selling. |
| Volatility is easier to trade profitably than direction | **Unproven — reasoning only.** Forecastable volatility does not guarantee profitable available option structures. |
| High IV versus recent realised volatility means sell | **Insufficient — some evidence.** Compare IV with a forward forecast over the same horizon, including events and uncertainty. |
| Daily bhavcopy plus a spread allowance validates proposed stops | **Reject — strong evidence.** It cannot recover intraday event order or simultaneous executable leg prices. |
| A strategy must beat every directional control | **Reject — reasoning only.** Use relevant, risk-comparable, predeclared benchmarks, not a hindsight-winning bet. |
| Thirty or 100 trades establish trust | **Reject — strong statistical reasoning.** Dependence and unobserved tail losses remain material. |
| Two or three profitable paper months confirm an edge | **Reject — reasoning only.** They can validate operations, but rarely establish durability or rare-event safety. |
| Keep a global sideways-market ban | **Disagree — reasoning only.** Suitability depends on the setup; a range strategy may seek that environment. |

SEBI reports **91.3% trading only options rather than futures**, and **92.8% losing across F&O** over FY22–FY24. It does not support "93% only buy options." See [SEBI study](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727085659479.pdf), pages 17–18.

A volatility risk premium has an economic rationale, including compensation for downside risk. That is not proof of profitable NIFTY spreads after protective-wing costs, execution, charges and taxes. See [Federal Reserve research on downside variance risk premium](https://www.federalreserve.gov/econres/feds/downside-variance-risk-premium.htm).

## 5. Capital feasibility and risk

**Risk-manager recommendation: reasoning only; the arithmetic is certain.**

Use the intended **₹2 lakh** as the primary paper account. Treat ₹5 lakh as a separate capacity scenario.

A ₹6,500 contractual loss is **3.25%** of ₹2 lakh. A one-lot paper position cannot become a quarter-lot live position. If the smallest structure exceeds the risk budget, skip it.

| Rule | Proposed threshold |
|---|---:|
| Full contractual position risk, including conservative costs | **1% of equity** |
| Total open contractual risk | **3%** |
| Pause new entries after daily loss | **1.5%** |
| Weekly loss | **3%** |
| Monthly loss | **5%** |
| Peak-to-trough drawdown | **8%** |

These are proposed conservative governance choices, **not empirically optimal settings**. Measure realised plus open-position liquidation losses. Gaps may exceed pause thresholds; these thresholds are not guaranteed loss caps.

## 6. Combined development plan

**Data/backtesting and execution recommendations: strong evidence.**

1. **Correct experiment records.** Store frozen inputs, commands, seeds, contracts, every trade and every control outcome. Include unfinished positions and shared-account equity.
2. **Build the common engine.** Actual contract calendars, bid/ask execution, multi-leg fills, margin, costs, settlement and risk. Historical replay and paper trading share this logic.
3. **Validate accounting.** Independent fixtures for long options, debit spreads, credit spreads, partial fills, rejected orders, expiry and futures daily settlement.
4. **Test only two initial strategy families.** One simple directional debit spread and one protected premium-selling hypothesis. Delay stock-event trades and FII filters until their inputs can be tested properly.
5. **Run frozen out-of-sample tests and paper reconciliation.** Introduce AI as a separately measured challenger.

**Options-strategist recommendation: reasoning only.** Start operationally with a two-leg NIFTY debit spread because it is simpler to validate than a four-leg iron condor. This is implementation priority, not a claim of the highest expected profit.

A has a plausible economic rationale; C is easier to test; B needs better event and expectations data; D is a filter requiring an incremental-benefit test. Their probabilities of profitability cannot honestly be ranked from these documents.

## 7. Proposed acceptance rules

**Statistical recommendations: reasoning only until validated on the data.**

- Use at least **five years where reliable data permit**, including stress periods where available. Apply historical contracts and fees correctly.
- Keep an untouched final chronological evaluation period and remove overlapping outcome spans around split boundaries.
- For two final primary hypotheses, use **one-sided α = 0.025 each**, providing a 5% family error budget. Additional final tests need an explicit adjustment.
- Require positive account advantage over cash with a positive adjusted lower confidence bound, not just positive average trade outcomes.
- Require **profit factor ≥1.3**, calculated from net winning and losing outcomes, as a secondary screen.
- Require positive results under **twice the base execution-cost allowance**; separately report missed-fill and delayed-exit stresses.
- Enforce drawdown and loss brakes in every replay.
- Use at least **three months and 20 completed positions**, whichever takes longer, for the paper execution gate. This is **not** a statistical proof threshold.

Personal taxes must be a declared scenario alongside actual API/data/AI bills. An after-tax confidence claim must incorporate the tax calculation, not silently use a flat haircut.

For position pricing, time decay and IV changes already appear in the option-price P&L; do not deduct them again as cash costs.

## 8. AI and market research

**Research, corporate-finance and macro recommendations: reasoning only.**

Use news first for dated events and structured facts. Compare results with expectations known beforehand. Preserve publication and ingestion timestamps. Treat FII positions and open interest as possible hedges, not automatic directional conviction.

Use IV, skew and term structure to assess contract pricing and stress exposure. Use scheduled RBI/Budget events as explicit guards. Test extra macro inputs individually.

AI can extract facts, assess surprise and explain decisions. Deterministic code calculates payoffs, position size and risk. Judge AI by incremental executable net profit after extra costs and delays, not persuasive explanations. Historical AI tests also risk knowledge of later outcomes; prospective shadow testing matters.

**Behavioural-finance recommendation: reasoning only.** Do not relax the risk budget or increase trading frequency to force a minimum lot or sample target to fit. No trade is a valid system output.

## 9. Risks, uncertainty and how the review could be wrong

- Synthetic option results can differ materially from real option prices and executable fills.
- Missing trade-level records prevent independent reproduction of the controls.
- One falling-market window cannot identify durable strategy performance across regimes.
- Protected selling may earn a premium, but tail losses and hedge/execution costs may remove the net advantage.
- The directional setup below may show no edge or no feasible one-lot entries within the proposed risk budget.
- Proposed risk thresholds, holding periods and pass criteria are not optimised or approved; freeze them before final testing.
- A successful paper execution check does not guarantee profitable real trading.

The earlier narrative supplied proposed parameters without all confidence labels. They are **reasoning-only hypotheses**, not validated strategies.

## 10. Setup summary

| Setup | Instrument and entry | Exit | Size | Expected edge/source | Main risk | Proof and pass/stop rule |
|---|---|---|---|---|---|---|
| **First paper hypothesis — reasoning only** | NIFTY monthly debit vertical, **30–45 calendar days** remaining. Close breaks previous **20-session closing high/low**, consistent with **50-session EMA**. Enter next session at **10:00 IST**; buy nearest ATM and sell next listed strike in signal direction. | Exit at **10:00 after 10 trading sessions**, next-session 10:00 after an opposite signal, or **two sessions before expiry**, whichever comes first. No percentage profit target; full debit reserved as risk. | One lot only when debit plus cost reserve fits **1%**; otherwise skip. | Trend continuation hypothesis; **no demonstrated NSE spread edge**. | Whipsaws, spreads and insufficient one-lot capacity. | Frozen validation gates above; pause at stated account limits. No entry if a scheduled RBI decision/Budget falls inside the planned holding window. |
| **Claude A — some evidence for rationale; implementation unproven** | Protected index premium selling. | Proposed exits require intraday validation. | Full spread loss plus costs must fit **1%**. | Possible compensation for volatility/tail risk; no account-specific proof. | Crashes, margin and hedge/execution costs. | No promotion until entry, strikes, forecast, exits and margin rules are fully specified and pass the same gates. |
| **Cash — strong evidence as default when no setup qualifies** | No derivative position. | None. | Preserve funded capital. | Avoid unsupported trading costs and exposure. | Opportunity cost. | Remain in cash when data, execution, sizing or evidence gates fail. |

**Final decision:** support the framework rebuild; revise unsupported causal claims; keep every candidate as an unproven hypothesis. No strategy is approved for real trading by this review.

## External sources

- [SEBI FY22–FY24 study](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1727085659479.pdf).
- [NSE securities transaction tax schedule](https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax).
- [Groww F&O pricing](https://groww.in/pricing/futures-and-options).
- [NSE index lot-size circular](https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf).
- [Federal Reserve: downside variance risk premium](https://www.federalreserve.gov/econres/feds/downside-variance-risk-premium.htm).
