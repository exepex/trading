# Review 9: desk design — connect expert reasoning to tested trade decisions

**Verdict:** Accept the two-loop direction and the shared-role process. The design is a useful desk operating model, but does not yet specify the measurable inference and allocation process that turns expert findings into profitable decisions. Complete those business rules before automating AI calls. Continue data-driven research immediately; this review is not a request for another code-audit cycle.

- Reviewer: ChatGPT; date: 12 October 2026.
- Reviewed snapshot: 22970012418b0251477a0270bd54e16123f664d1.
- Primary sources: [DESK_DESIGN.md](../../docs/DESK_DESIGN.md), [Claude response 7](../claude/response_7_2026-10-12-desk-design.md).
- Context read: updated [AGENTS.md](../../AGENTS.md), [owner decisions](../../docs/DESK_DECISIONS.md), [desk meeting 1](../../research/2026-10-12-desk-meeting-1/README.md), its results JSON and [response 6](../claude/response_6_2026-10-12-desk-meeting-1.md).
- Boundary: design review with explicit arithmetic and a small calculation from the committed results. The desk-meeting backtest has not been independently replayed in this review; its profitability claims remain exploratory. No code changed, AI layer approved, or real order placed.

## 1. What is right

**Reasoning only — design agreement, not proof of trading edge.**

- Research starts with data and mechanisms, then produces rules. Daily execution applies what has been tested.
- The same team can discover new opportunities without inventing an unvalidated rule and trading it immediately.
- Numeric calculations, funding and risk constraints belong in code; expert interpretation can inform measured inputs.
- Independent first reports, recorded disagreements and a challenging judge improve the reasoning process.
- The owner retains approval. No real trades are tool-placed.
- Manual research and deterministic paper trading precede an expensive automated AI desk.

These fit the owner's clarification. “Fixed strategies” should mean a fixed, testable **decision policy**, not permanently fixed forecasts or market views.

## 2. The main missing business link: evidence -> forecast -> payoff -> allocation

**Reasoning only — portfolio, modelling, mathematics and options perspectives.**

Sections 2–4 jump from role reports to firing rules and then an “expected net value” check. They do not define where that expectation comes from. An LLM saying “options look expensive” and a threshold firing are not a quantified profitable opportunity.

Add one shared decision record per opportunity:

| Step | Required output |
|---|---|
| Observations | Point-in-time data, source, timestamp, missing inputs and the specific evidence each role contributes |
| Forecast | Target and horizon: distribution/scenarios for the move, volatility and relevant option repricing; uncertainty and model/version |
| Trade expression | Exact available legs, prices, size, exits and expiry; comparison with feasible alternatives |
| Economic value | Expected P&L after the complete trading lifecycle and costs; adverse scenarios; sensitivity to forecast error |
| Account decision | Available funds/margin, current exposures, risk consumption, expected account benefit and the no-trade alternative |
| Explanation | Why this information should improve the decision; what would invalidate it; disagreement and final reason |

For a short-volatility trade, compare implied pricing with an **entry-time forecast** of future realised variation/jumps over a compatible horizon. A positive IV-minus-trailing-RV difference alone is not an expected-P&L calculation. If the trade exits before expiry, its residual option value and volatility changes also matter.

Each AI report should state observations, interpretation, measurable implication, uncertainty, counterevidence and abstention/missing-data status. Other roles may challenge its implication. The code/calibrated model supplies probabilities and money amounts; confidence prose does not become a probability without validation.

## 3. A concrete finding from the supplied data

**Some evidence — descriptive arithmetic from the existing results JSON, not an independently validated strategy.**

The narrative calls the cycles where implied volatility did not exceed subsequent realised volatility the danger months. I grouped the 32 recorded short-straddle P&Ls in results.json:

| Retrospective group | Cases | Positive P&Ls | Sum of recorded P&L | Worst |
|---|---:|---:|---:|---:|
| Entry IV > subsequently realised volatility | 23 | 19 | ₹249,306 | -₹15,858 |
| Entry IV <= subsequently realised volatility | 9 | 7 | ₹44,557 | -₹41,030 |

The nine cases include the worst recorded loss, but seven were winners and the group aggregate was positive. The binary IV/RV comparison therefore does not, by itself, classify profitable versus unprofitable trades. Trend, path, exits and option repricing can matter.

**Decision — reasoning only:** retain conditional volatility pricing as a research hypothesis; do not install the retrospective comparison as a daily filter or conclude that excluding those nine cycles would improve a deployable system. Future realised volatility is unavailable at entry. The naked straddle remains outside the owner's protected-loss mandate; these numbers are a diagnostic, not a trade recommendation.

The average entry IV and realised volatility in meeting 1 also refer to different remaining-expiry/holding horizons. Study a compatible horizon or explicitly model the residual value at the planned exit. No new claim of a proven volatility premium is made here.

## 4. Fixed versus adaptive: answer to question 1

**Reasoning only — modeller and statistician.**

Yes to a fixed tested policy with dynamic outputs. Automatic adaptation is acceptable when the **adaptation algorithm itself is frozen and evaluated**.

For example, a forecast may update using only previously available observations, and size may vary with forecast uncertainty, live prices and remaining approved risk. That need not create a new strategy version every day. Fix the input definitions, update schedule, fitting method, parameter bounds and decision rule. Test the entire update sequence chronologically.

An improvised threshold, changed prompt, new event override or altered fitting procedure is a policy change and requires a new version. Every strategy/feature tried must enter the research ledger, including rejected trials. Repeated selection on the same history can create apparent winners: see [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). A version number alone does not cure that selection bias.

The 2024–2026 observations already examined are discovery data. Do not later label the same observations untouched out-of-sample merely because a strategy file was frozen after looking at them.

## 5. Daily information and execution timing must agree

**Strong evidence from the design's timing and supplied data types — data, execution and trader perspectives.**

A 3:00 pm decision cannot use that day's final close, end-of-day option chain or statistics published later. Give each input an availability time, not just a trading date. FII/DII positioning and some news/flow data may be lagged; yesterday's published figure can be usable without being today's observation.

Choose and document one of these research representations:

- For the intended 3:00 pm desk, capture point-in-time inputs at or before the cut-off and model fills after the decision with contemporaneous executable quotes.
- Until that history exists, run an explicitly labelled daily-close research proxy that uses available completed information and a later fill observation. Do not claim it reproduces the 3:00 pm desk.

Sequential role reports, judge time and quote ageing also matter. Recheck quote freshness and limits immediately before a paper fill; an approved proposal is not an indefinitely valid price.

AI roles on historical news require an extra evidence boundary: a modern model may already know later historical outcomes. Hiding later rows from its prompt does not remove that learned knowledge. Historical AI replays are exploratory; forward paper decisions are the cleanest evidence of incremental real-time contribution.

## 6. Owner limits: respect the choices, correct the accounting implications

The governing assumptions are now **₹5 lakh paper capital, ₹10,000 maximum trade loss including charges, at most three open trades, 31.2% model tax on annual net F&O profit, holdings up to 2–3 weeks, daily decisions around 3:00 pm**. I accept these owner decisions and do not substitute the earlier ₹2 lakh/1% diagnostic profile.

### 6.1 Six percent is not a worst-month bound

**Strong evidence — arithmetic, risk and portfolio roles.**

Three simultaneous ₹10,000 risks are ₹30,000, or 6% of initial ₹5 lakh capital. That limits open exposure, not cumulative monthly losses. Six sequential full losses are ₹60,000, or 12%, even with no more than three positions open at once.

The sentence in DESK_DECISIONS that the worst realistic month is about -6% is unsupported. “Drawdown brakes” in the design need an explicit definition: account equity basis, drawdown measurement, threshold, whether it blocks entries or orders exits, and restart authority. No new monthly percentage is approved by this review.

### 6.2 Payoff risk is not funding capacity

**Strong evidence — options mathematics and exchange margin rules; broker implementation remains to be verified.**

A protected structure can satisfy a ₹10,000 terminal-loss calculation yet require substantially different cash/margin. Track available cash, reserved premium, broker-required margin and open commitments separately from payoff risk. [NSE Clearing's margin framework](https://www.nseclearing.in/risk-management/equity-derivatives/margins) includes distinct margin components.

The bound assumes the required protection is actually present. Define partial-fill handling and leg entry/exit sequencing so a temporary naked position is not accepted as a protected trade. Initial scope can remain NIFTY; stock options need their own settlement/funding rules. [NSE's individual-securities specification](https://www.nseindia.com/static/products-services/equity-derivatives-individual-securities) states physical settlement, so their handling cannot be copied indiscriminately from index research.

### 6.3 Once-daily loss exits are observations, not guaranteed fill caps

**Strong evidence — design logic and execution perspective.**

A daily stop can be crossed between reviews or across a gap. The hedge's payoff bound and a daily exit threshold are different protections. Do not simulate an exact stop fill from daily closes, or assume that code can guarantee an immediate close when a threshold is touched.

When data is stale, keep last-good marks explicitly stale; do not fill an exit at them. Maintain risk-reducing exit handling when an AI or judge is unavailable. A strategy paused for research can still have open positions requiring management.

## 7. Net profit must include the desk's operating cost

**Reasoning only — cost accountant and portfolio roles.**

The design includes charges, pads and a tax assumption, but omits the proposed AI/API/data bills from the trading/account decision. “Code roles cost nothing” also ignores any actual compute/storage/data expense. Use actual incremental costs; do not invent overhead for resources with zero extra cash cost.

Illustration, not a budget estimate: three trades earning ₹500 each after transaction costs generate ₹1,500 a month. A ₹3,000 monthly AI bill makes the account unprofitable even before tax.

Keep three separate ledgers: trade P&L after transaction costs; account result after operating costs; annual tax under the approved modelling assumptions. Apply the owner's 31.2% annual-net-profit model rather than taxing each winning trade independently. Treat it as a research scenario, not certification of the owner's complete legal tax position.

A daily trade may have positive incremental expected value while the whole desk fails to cover fixed costs. Both questions must be answered. Likewise, an AI role must add enough net decision value to justify its cost.

## 8. Roles and the AI portfolio manager: answer to question 2

**Reasoning only — all roles should contribute, but expertise does not require one paid LLM call per role.**

- **Code:** accounting, risk/funding, contract/payoff validation, timestamps, feature calculations, quantitative forecasts, rule evaluation and quantitative test/judge checks.
- **AI/human analytical perspectives:** economic explanations, event interpretation, counterarguments, research design and trade-structure hypotheses, grounded in cited inputs.
- **Hybrid:** volatility, flows and execution — code measures, judgement interprets, tests decide whether that interpretation adds value.

Market, macro, corporate, equity and positioning roles should report “input unavailable/not applicable” when the data or instrument does not support the claim. OI or a put-call ratio alone does not identify a profitable directional forecast. No role should invent numbers to complete a meeting.

**Material gap:** the portfolio manager “picks among firing rules” as an AI, despite claiming the playbook determines the decision. That selection is itself part of the trading algorithm. So are an options strategist's daily structure changes and a trader's discretionary veto.

Start with a defined deterministic allocation policy. Later compare an AI selector with the same opportunities, account constraints and costs, including its abstentions. Version and evaluate prompts/models that affect orders. The data snapshot can reproduce the numeric checks; it does not guarantee identical LLM reasoning on rerun.

## 9. Judge, overrides and failure handling: answer to question 3

**Reasoning only — red team, behavioural and head-of-desk perspectives.**

Different models and independent initial reports are useful process controls, not guarantees of correctness. Both can repeat the same wrong input or economic assumption.

Separate judge outputs:

1. **Hard validity:** timestamp, contract, arithmetic, funding and owner-approved limits. Code should establish these, not a language model's opinion.
2. **Research sufficiency:** sample, uncertainty, selection history, execution assumptions and counterevidence.
3. **Interpretation:** whether the economic explanation follows from the evidence.

Define failure categories before looking at results. Audit a stratified sample of approvals, rejections and abstentions, including all material overrides. Measure false approvals and false rejections on known test cases and independently recalculated evidence; agreement between models is not the ground-truth label.

An owner can approve an amended risk policy prospectively or override a discretionary judgement, with the effect recorded. An override cannot turn stale inputs into current data or a failed arithmetic identity into a valid result. Overridden paper decisions must remain separately identified when evaluating the tested policy.

## 10. Evidence gate and staged build: answer to question 4

**Reasoning only — statistical and research management.**

Three months and 20 positions are reasonable minimum observation requirements chosen in the design. They are not proof of edge, especially when positions overlap or depend on the same market shock.

Specify before evaluation:
- profitability after all operating costs and the modelled tax;
- uncertainty in net expectancy with appropriate time/regime grouping;
- account drawdown and tail scenarios under the approved limits;
- opportunity coverage and missing-data exclusions;
- forecast calibration and execution differences;
- the comparator for each added role/feature;
- scheduled review points and the distinction between a hard-loss pause and an uncertain statistical result.

Repeated daily checks against an undefined “expected range” can cause arbitrary pauses or model switching. Define that range, observation unit and response beforehand. Do not invent a universally sufficient trade count.

Phase 3's code-only desk needs a stated validation path because earlier sections require an AI judge for every daily decision. Use deterministic validity checks and a manual independent research review during the first stage; add the automated AI judge in the later owner-approved phase. That reconciles the owner's AI hold with a usable deterministic core.

## 11. Decisions for the next desk round

**Reasoning only — proposed research priorities, not approved trades.**

| Item | Decision | Next measurement |
|---|---|---|
| Two-loop desk | Keep | Define the shared forecast/payoff/allocation record |
| Conditional protected premium selling | Keep as a lead hypothesis, not a proven strategy | Compatible-horizon entry-time volatility/jump forecasts and complete protected-payoff paths |
| Naked selling | Exclude from deployable candidates under the owner's bound | Retain only as a diagnostic comparator if useful |
| “No directional edge exists” | Do not generalize | Simple trend findings do not exhaust conditional directional information |
| “All IV <= future RV cycles are danger months” | Reject as a deployable classifier | Test a past-only predictor, then its actual incremental after-cost value |
| One AI agent for every role immediately | Defer automation | Manual role analyses and deterministic baseline first; add paid roles by measured contribution |
| Exact daily stop fills / 6% monthly-loss guarantee | Reject those assumptions | Model the daily exit convention and account drawdown policy explicitly |

The next research question should be: **Which entry-known conditions improve the expected net payoff of a fully protected trade, within the owner's funding and loss limits, compared with taking the same feasible exposure without that information?**

That question connects all the roles to the owner's goal. Volatility supplies a forecast, macro/events challenge it, execution prices it, mathematics values the payoff, risk/funding constrains it, portfolio management compares alternatives, and the red team checks whether the apparent gain survives independent evaluation.

No code-level defects are raised in this design review. The substantive changes above concern economic inference, information timing, accounting, risk and decision authority.
