# Desk design: a team of experts finding the most profitable F&O trades, against the odds

Version 2 (12 Oct 2026), a full rewrite. Version 1 described controls well but not the core: **how a team of experts
in different fields works together to find winning trades**. This version puts that first; the controls agreed in
review 9 are kept in sections 6-9. Nothing is built yet; the AI layer stays on hold until the owner approves.
Owner decisions: `docs/DESK_DECISIONS.md`. Roles and working rules: `AGENTS.md`.

**How this design is closed:** section 11 lists every section with each AI's position. The design is final when both
AIs mark every section "agreed" (or the owner settles a disagreement) and the owner approves. No next step (desk
meeting 2, building) starts before that.

## 1. The goal and the odds we are up against

**Goal:** the most profitable NSE F&O trades **net** of charges, slippage, the desk's own running costs and 31.2% tax,
proven on real data, then on paper, before any real money.

**The odds (SEBI studies; details and sources in `reports/Retail FnO losses and safeguards.md`):**
- 88-93% of individual F&O traders lost money in every year measured (FY22-FY26); FY26 losses Rs 91,685 crore.
- About 93% of individuals only buy options, and about 90% of them lose; of the few who mainly sell, about 44% lose.
- Only 0.5% were profitable in all five years FY22-FY26; loss rates rise, not fall, with experience.
- Costs alone were 35% of loss-makers' gross losses; 4.4 lakh traders profitable before costs lost after costs.
- 59% of index-option turnover is same-day expiry; 97% within a week.
- The money goes mostly to proprietary firms and foreign investors, 96-99% of it to algorithmic desks.

**What "winning against the odds" means for us (reasoning, built on that evidence):** we will not out-run algorithms
at speed or out-guess the market's direction day to day. We win only by standing on the side that is **paid**, at a
horizon and in contracts the crowd and the fast desks leave alone, with costs kept small and losses capped. Every
trade must answer one question first: **who pays us, and why will they keep paying?**

## 2. Where a small, patient desk can win: the edge map

Each edge family has an economic reason (who pays), owning roles, the data that tests it, and its evidence today.
The team's research works through this map; any role may add a family when it has a reason and data.

| # | Edge family | Who pays us, and why | Owning roles | Data to test it | Evidence now |
|---|---|---|---|---|---|
| E1 | Volatility risk premium (sell protected insurance) | Buyers of protection and lottery options overpay for moves that mostly do not come | Volatility trader, options strategist, risk manager | NSE daily option chains, 2019-2026 | **Some evidence:** IV 13.8% vs realised 12.0-12.2%; protected condors +Rs 24,757 to +69,026 (10-30 months, data gap) |
| E2 | Conditional volatility pricing (when to sell, when to stay out) | Same payers; the edge is skipping months when options are cheap relative to live risk | Volatility trader, quant modeller, statistician | Same, plus past realised volatility | **Some evidence at most:** "IV above past 20-day realised" kept 27 months (+Rs 3,10,568, worst -7,867), skipped 5 incl. the 3 worst (naked straddle, diagnostic) |
| E3 | Event premium | Option buyers before RBI, Budget, elections, results; IV often falls after (VIX -12% to -34% on past event days), but surprises spike it | Macro economist, equity research, volatility trader | Event calendar + chains around each event | Untested |
| E4 | Term structure and short-dated richness | Retail crowds into weekly and same-day options; sellers of near-dated options or calendar structures may be paid | Positioning analyst, volatility trader, regulation | Weekly vs monthly chains | Untested; expiry-day trading itself is excluded (algorithm territory) |
| E5 | Skew (puts vs calls) | Hedgers pay for downside puts; lottery buyers pay for far calls | Options strategist, behavioural finance | Full chains (far strikes) | Untested; needs the full raw files |
| E6 | Conditional direction | Forced or slow flows (FII positioning extremes, after-shock drift) | Positioning analyst, macro, quant | FII/DII data, futures OI, prices | Simple trend: **none** (50-52%); conditional: untested |
| E7 | Stock vs index | Single-stock moves on results vs index volatility (dispersion) | Equity research, investment banker, volatility trader | Stock option chains, results calendar | Untested; stock options settle physically, need own rules |
| E8 | Cost advantage | Not an edge alone: a patient monthly trader with limit orders avoids the cost drag that sinks the crowd | Execution, tax and cost accountant | Real quotes (to calibrate the Rs 1 pad) | Assumed, not measured |

**Not ours (no edge for us, by evidence):** intraday speed, expiry-day games, closing-auction moves, order-flow
reading, buying cheap far-out options. Algorithms and prop desks own these.

## 3. The team: how experts work together (the core)

### 3.1 One goal, distinct jobs
Every role works for the same goal (net profitable trades) from its own field. Each role:
- **owns** edge families and questions (section 2), its own data, and the risks of its field;
- produces **finding cards**: observation (data, source, when it was known), interpretation, measurable implication
  for a trade, confidence (strong / some / reasoning only), counter-evidence, what would prove it wrong; or "not
  applicable" (never invented numbers);
- has a **scorecard**: did its contributions change decisions, and did those changes add net money? A role that adds
  nothing over time is re-scoped or removed.

### 3.2 How a trade idea is built: no single role can make one
A trade thesis needs every part below, each from the role that owns it:

| Part | Question | Owner |
|---|---|---|
| Payer | Who pays us and why will they keep paying? | Portfolio manager, behavioural finance, market research |
| Signal | What measurable, entry-known condition says the edge is present today? | Volatility trader, quant / statistician, quant modeller |
| Context | Which events, flows or rules inside the holding window change this? | Macro economist, positioning analyst, equity research, investment banker, regulation |
| Structure | Which exact legs express the view with capped loss? | Options strategist, mathematician |
| Price | Can we actually trade it, at what cost? | F&O trader, execution, tax and cost accountant |
| Survival | Worst case, margin, limits, correlation with open trades | Risk manager |
| Attack | How could this be luck, a flattering period, or a disaster? | Red team |

A thesis missing any part is not a trade. The **portfolio manager** assembles theses and ranks them by expected net
money per rupee of risk, against the no-trade option.

### 3.3 The meeting (research and daily use the same rhythm)
1. **Question** (head of desk): one question, e.g. "Which entry-known conditions improve a protected seller's net
   payoff?"
2. **Independent findings:** each role studies the data alone and submits its cards before seeing anyone else's
   (prevents copying and groupthink).
3. **Cross-examination:** every role must challenge at least one finding from another field, e.g. the risk manager
   tests the volatility trader's idea against the worst gap; the macro economist names the event that breaks it.
4. **Thesis assembly** (portfolio manager): combine findings into theses (3.2); record disagreements.
5. **Settle disagreements with data, not votes:** the disputing roles agree a test and its pass/fail **before** it
   runs; the result decides.
6. **Red team, then judge** (section 7).
7. **Decisions:** which theses go to testing, to paper, or are dropped and why; the next question.

### 3.4 The roles
| Role | Field and edge families | Runs as |
|---|---|---|
| Head of desk | Sets questions, makes every role contribute, records decisions | AI |
| Portfolio manager | Payers, ranking theses, allocation, when to switch a strategy off | AI for research; fixed rule (code) for daily allocation |
| Volatility trader | E1-E5: implied vs realised, regimes, skew, term structure, event premium | Code measures + AI interprets |
| Options strategist | Structures for each view; Greeks; capped loss | AI, checked by code |
| Mathematician | Payoffs, expected value, whether the numbers can work | AI, checked by code |
| Statistician / quant researcher | Sample size, controls, out-of-sample, multiple testing | Code + AI |
| Quantitative modeller | Forecasts (volatility, regime), tested out of sample | Code |
| F&O trader | What works and fails live: fills, gaps, expiry, liquidity | AI |
| Execution / microstructure | Spreads, fill assumptions, pad calibration (E8) | Code + AI |
| Risk manager | Limits, worst case, margin, correlation; hard rules | **Code** |
| Tax and cost accountant | Net after charges, running costs and tax (E8) | **Code** |
| Data and backtesting engineer | Data quality, availability times, no look-ahead | **Code** |
| Macro economist | E3, E6: RBI, Budget, global cues, gaps | AI |
| Positioning analyst | E4, E6: OI, put-call ratio, FII/DII positions | Code + AI |
| Market research analyst | Mood, sectors, news against expectations | AI |
| Equity research analyst | E7: company results, sector news | AI |
| Investment banker | E7: corporate actions, block deals | AI |
| Regulation (SEBI/NSE) | Lot sizes, expiry days, margins, rule changes | AI |
| Behavioural finance | E5, the payers' biases; our own biases (overtrading, chasing) | AI |
| Red team | Breaks every thesis | AI, different model from the author |
| Judge | Verifies every claim and decision (section 7) | Code checks + AI, different model from the author |

Every role contributes; not every role needs its own paid model call every day. Roles with nothing to say report
"not applicable".

## 4. Two loops

**Research loop (weekly / monthly), where strategies are found:** meeting (3.3) on an edge family -> thesis -> test
on real data -> red team -> judge -> owner approval -> playbook version -> paper trading -> results fed back.

**Daily loop (3:00 pm), where decisions are made:** data check -> role reports on today's data -> each approved
playbook rule checked -> decision record (section 5) -> judge -> paper trade -> review of open trades.

**Fixed policy, dynamic decisions:** a strategy is never invented and traded the same day. A rule may adapt
automatically only if the adaptation method itself (inputs, update schedule, fitting, bounds) was fixed and tested in
time order; any other change is a new version.

## 5. Playbook and decision record

**A playbook strategy** (`playbook/<name>-v<n>.yaml`): payer and economic reason; edge family; structure; entry-known
conditions; size rule (maximum loss including costs within Rs 10,000); funding (margin per lot, measured); exits
(profit, loss, time, event); evaluation plan fixed before paper (expected range, unit, review dates, pause rules);
evidence links (test, red team, judge, owner); status (research / paper / paused / retired).

**Decision record** (one per opportunity, code): observations with availability times; forecast (normally the tested
rule's own P&L distribution in similar conditions; a separate model only if it beats that); exact legs, prices, size,
exits; expected net value and adverse scenarios; account room and the no-trade option; reasons and disagreements.

## 6. Evidence rules (so the team does not fool itself)

- **Ledger:** every idea tried, including failures, goes in `research/LEDGER.md` before its result is read.
- **Discovery data:** NIFTY 2024-2026 has been looked at and can never be called out-of-sample. Untouched checks:
  2019-2023 and forward paper trading.
- **Pass/fail fixed before a test runs.** No tuning on the check data.
- **Availability times:** a test uses only what was known at decision time; daily-close research is labelled
  close-proxy, not the 3:00 pm desk.
- **Fills:** real charges, Rs 1 adverse fill per leg per order until calibrated; daily loss checks fill at the next
  observed price, never at the threshold; stale prices never fill.
- **Historical AI replays are exploratory** (a model may know what happened later); AI value is measured forward.
- **Paper gate:** at least 3 months and 20 positions (a minimum, not proof), judged by the plan fixed in advance.

## 7. Red team and judge

- **Red team:** a different model from the author; attacks every thesis (luck, flattering period, the disaster case).
- **Judge**, three checks: (1) hard validity in code (dates, contracts, arithmetic, funding, limits); (2) research
  sufficiency (sample, trials in the ledger, execution assumptions, counter-evidence); (3) interpretation (does the
  economic reason follow from the evidence). Fail = no trade, or the work goes back to its author.
- **Authority:** the judge can block anything. Only the owner can overrule a judgement (2 or 3), in writing, and
  overridden trades are scored separately. No one overrules a hard-validity failure.
- **Judge audited monthly:** a stratified sample of approvals, rejections, abstentions and all overrides re-checked
  against recalculated evidence and seeded known-answer cases; false approvals and rejections counted.

## 8. Owner limits, risk and money

- Rs 5 lakh paper account; Rs 10,000 maximum loss per trade including charges; at most 3 open trades (Rs 30,000 at
  risk at one time); drawdown brake Rs 30,000 below the highest point (no new trades until the owner restarts; the
  realistic worst including open trades is about Rs 60,000, 12%); holdings up to 2-3 weeks; decisions at 3:00 pm.
- Protection bought first and sold last; a missing protective leg means close. Margin is tracked apart from loss.
- **Three ledgers:** trade P&L after charges and pads; account result after the desk's running costs (AI, data);
  tax at 31.2% on the year's net F&O profit (research model, not tax advice). Each AI role must earn more than it
  costs.

## 9. Failure handling

| Situation | What happens |
|---|---|
| Data missing or stale | No new trades; stale prices marked and never used as fills; alert |
| A role fails to report | Its conditions count as not met |
| Roles disagree | Recorded; settled by an agreed test; until then the playbook rule decides |
| Judge or AI unavailable | No new trades; risk-reducing exits still run (code) |
| Limit or drawdown brake hit | Code blocks or closes; no discussion |
| Paper results outside the plan | As the strategy's evaluation plan says; open trades still managed |

## 10. Build order (after owner approval of this design)

1. Research meetings by hand on the edge map (E1-E2 first, with full chains and 2019-2023), until one strategy passes.
2. Playbook format and the code roles (data, risk, cost/tax, rule evaluation, hard-validity checks).
3. Daily paper desk with code roles on the first approved strategy; the other AI reviews results in the repository.
4. AI roles, red team and AI judge added one at a time (after the owner starts the AI plan); each kept only if it
   adds net value against the code-only desk.
5. Intraday watching only if data shows it helps.

## 11. Closing the design

| Section | Claude | ChatGPT | Owner |
|---|---|---|---|
| 1 Goal and odds | Agreed | Changes required: economics and evidence (review 10, section 2) | |
| 2 Edge map | Agreed (any role may add families) | Changes required: hypotheses, scope and buying thesis (review 10, sections 2 and 4) | |
| 3 The team and how it works | Agreed | Changes required: role scorecards (review 10, section 3) | |
| 4 Two loops | Agreed | Agreed | |
| 5 Playbook and decision record | Agreed | Agreed | |
| 6 Evidence rules | Agreed (from review 9) | Agreed | |
| 7 Red team and judge | Agreed (from review 9) | Agreed | |
| 8 Owner limits, risk and money | Agreed | Changes required: brake action and bound basis (review 10, section 5) | |
| 9 Failure handling | Agreed | Changes required: align brake action (review 10, section 5) | |
| 10 Build order | Agreed | Agreed | |

ChatGPT: mark each section "agreed" or give the specific objection and the change you want. Open questions:
1. Is the edge map complete? Which edge family is missing, or should be dropped, and why?
2. Is "who pays us" the right first test of every trade?
3. Does the thesis table (3.2) give every role a real job, or is any role decoration?
4. How should a role's scorecard measure its added net value fairly?
