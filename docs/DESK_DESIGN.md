# Desk design: a team of expert roles finding net profitable F&O trades

Status: **design, revised after ChatGPT review 9** (12 Oct 2026; answer: `reviews/claude/response_8_2026-10-12-desk-design.md`). Nothing here is built yet; the AI layer stays on hold until the owner
approves. Owner decisions it must respect: `docs/DESK_DECISIONS.md`. Roles and working rules: `AGENTS.md`.

## 1. The goal and the one principle

**Goal:** net profitable NSE F&O trades: profitable after all charges, slippage and tax (31.2%), proven on real data,
then on paper, before any real money.

**Principle: the decision policy is fixed and tested in advance; its daily outputs are dynamic.** A strategy is
never invented and traded on the same day: an untested rule is a guess. Strategies are created slowly in a research
loop and stored in a versioned playbook; every day the desk decides, from that day's data, whether a playbook rule
fires, on which contracts and at what size. A rule may adapt automatically (for example a volatility forecast refitted
on past data only, or size scaled by remaining risk room) when **the adaptation method itself** is fixed and was
tested chronologically: inputs, update schedule, fitting method and parameter bounds. Any other change (a new
threshold, prompt, override or fitting method) is a new version.

## 2. Two loops

```
 RESEARCH LOOP (weekly / monthly)                         DAILY LOOP (3:00 pm IST, trading days)
 data -> role analyses -> strategy proposal                today's data -> role reports
      -> historical test -> red team -> judge                   -> playbook rules checked -> trade proposal
      -> owner approval -> PLAYBOOK (versioned) ---------->     -> cost/tax check -> judge -> paper trade
      <- paper results feed back (keep / change / drop)  <-     -> daily review of open trades
```

### 2.1 Research loop: how strategies are created
1. **Question.** The head of desk sets one question, e.g. "Are NIFTY options overpriced, and when?"
2. **Independent analyses.** Each relevant role studies the data on its own and writes a finding: numbers, method,
   confidence label (strong evidence / some evidence / reasoning only).
3. **Proposal.** The portfolio manager combines findings into a strategy with exact rules (section 4).
4. **Test.** The quant runs it on real historical prices with the agreed protocol: real charges, Rs 1 adverse fill per
   leg per order (to be calibrated), 31.2% tax on yearly net profit, owner's limits, out-of-sample period, controls.
   Every input has an **availability time**, not just a date: a test only uses what was known at its decision time.
   Every idea tried, including rejected ones, goes into the research ledger (`research/LEDGER.md`), so the number of
   trials behind any winner is visible. Data already looked at (NIFTY 2024-2026) is **discovery data**: it can never
   later be called out-of-sample. The untouched checks are 2019-2023 (older NSE files) and forward paper trading.
5. **Red team.** Tries to break it: luck, a period that flatters it, a scenario that blows the Rs 10,000 limit.
6. **Judge.** Verifies every claim (section 6). Fails send the work back.
7. **Owner approval.** Approved strategies enter the playbook as a new version; nothing enters without it.
8. **Paper trading.** At least 3 months and 20 positions before any real-money discussion (a minimum, not proof:
   positions overlap and share shocks). Before paper trading starts, the strategy file fixes its evaluation plan:
   the expected range (from the test), the unit (monthly net P&L), the review dates, and what each result triggers.
   A hard-loss limit pauses at once; an uncertain statistical result waits for the scheduled review (no switching on
   daily noise).

### 2.2 Daily loop: how decisions are made (3:00 pm)
1. **Data check** (data engineer, code): today's NSE/Groww data present, fresh and consistent; otherwise no new trades.
   At 3:00 pm the day's close and end-of-day files do not exist yet: inputs are 3:00 pm quotes plus the last
   published figures (yesterday's FII/DII, yesterday's close). Research that uses daily closes is labelled a
   **close-proxy** and does not claim to reproduce the 3:00 pm desk.
2. **Role reports** (independent, in parallel), each a short structured report, for example:
   - volatility trader: implied vs realised volatility, skew, term structure, and how that compares with history;
   - macro / event analyst: scheduled events inside each candidate holding window (RBI, Budget, elections, results);
   - positioning analyst: open interest, put-call ratio, FII/DII positions;
   - quant modeller: volatility forecast and market regime;
   - risk manager (code): open trades, rupees at risk, room left under the limits.
3. **Playbook check** (code): each approved rule is evaluated on measured inputs; a rule fires only if all its
   conditions hold. The rule, not a model, chooses strikes and size. If several fire, a fixed **allocation rule**
   (code, part of the playbook) chooses; an AI selector is only tried later, compared on the same opportunities.
4. **Decision record and value check** (code): one record per opportunity (section 4.1); the expected net value after
   charges, pads and tax must stay positive, and the account must have the cash or margin for it.
5. **Judge check:** inputs are today's, every rule was applied as written, limits respected, reports consistent.
6. **Paper trade** opens after quotes and limits are re-checked just before the fill (an approved proposal is not a
   lasting price). Protection is bought first and sold last: a trade with a missing protective leg is not a protected
   trade and is closed. Slack message to #fno-desk with the reasons from each role.
7. **Open-trade review** (same team, same time): hold, take profit, or close at the rule's limit; the risk manager's
   hard limits apply without discussion. A once-a-day loss check is an observation, not a guaranteed exit price:
   tests fill such exits at the next observed price, never at the threshold. The bought protection is what caps the
   loss across gaps.

Intraday watching is a later layer, added only if data shows it improves net results (owner decision).

## 3. The team

One shared goal; each role has its own job, inputs and output, and no role decides alone.

| Role | Runs as | Daily job | Research job |
|---|---|---|---|
| Head of desk | AI | Runs the meeting; makes sure every role reported | Sets questions; records decisions |
| Portfolio manager | Code (rule) + AI | Allocation rule picks among firing rules (code) | Turns findings into strategy proposals; designs the allocation rule |
| Volatility trader | Code + AI | Implied vs realised volatility, skew, term structure | Volatility-premium studies |
| Options strategist | AI | Checks the structure fits the view | Designs structures (spreads, condors) |
| F&O trader | AI | Liquidity, spreads, expiry and gap practicalities | What fails in live markets |
| Quant / statistician | Code | Regime and forecast numbers | Backtests, controls, significance |
| Quantitative modeller | Code | Volatility forecast | Builds and validates forecasts |
| Risk manager | **Code** | Limits: Rs 10,000 per trade, 3 open, drawdown brake, cash/margin room | Worst cases, stress tests |
| Macro economist / event analyst | AI | Events inside holding windows | Event effects on volatility |
| Positioning analyst | Code + AI | OI, PCR, FII/DII | Does positioning add anything |
| Market research analyst | AI | Market mood, sectors, news against expectations | News impact studies |
| Equity research analyst | AI | (stock options) results, company news | Stock-specific edges |
| Investment banker | AI | Corporate actions, block deals | Event-driven moves |
| Microstructure / execution | Code + AI | Bid-ask, fill assumptions | Calibrate the pad from real quotes |
| Regulation (SEBI/NSE) | AI | Rule changes, lot sizes, expiry days | Effect of rule changes |
| Behavioural finance | AI | Flags overtrading, chasing | Owner's and retail biases |
| Tax and cost accountant | **Code** | Net value after charges; three ledgers (section 8) | Net results of every test |
| Data and backtesting engineer | **Code** | Data present, fresh, consistent | Data quality, no look-ahead |
| Mathematician | AI | Sanity of payoffs and sizes | Pricing and expected value |
| Red team | AI | Challenges the day's proposal | Tries to break each strategy |
| **Judge** | AI, **different model** from the work checked | Verifies the day's decision | Verifies every research claim |

"Code" roles are deterministic, tested Python: exact numbers, same answer every time. "AI" roles are language-model
agents for judgement. Every role contributes, but not every role needs its own paid model call: a role whose data or
instrument does not apply reports "not applicable / input unavailable" and never invents numbers. AI reports follow
one format: observations (with sources), interpretation, measurable implication, uncertainty, counter-evidence, and
missing data. Confidence words are not probabilities; numbers and money come from code and tested models.

**Historical AI replays are exploratory only:** a model may already know what happened later, and hiding later rows
from its prompt does not remove that. An AI role's added value is measured on forward paper decisions.

## 4. The playbook (what a strategy is)

A strategy is a versioned file, e.g. `playbook/protected-selling-v1.yaml`, with:
- **Hypothesis and economic reason:** who pays us and why (e.g. option buyers overpay for volatility).
- **Instrument and structure:** e.g. NIFTY monthly iron condor, short strikes 2% from spot, protection 500 points out.
- **Entry conditions:** each measurable (implied minus realised volatility above a threshold; no listed event in the
  window; days to expiry 30-45; risk room).
- **Size rule:** lots so that maximum loss including costs stays within Rs 10,000.
- **Exit rules:** profit target, loss limit, time exit (e.g. at 21 days to expiry), event exit.
- **Evidence:** links to the test, the red-team note, the judge's verdict and the owner's approval.
- **Status:** research / paper / paused / retired; paper scorecard kept beside it.

- **Evaluation plan:** expected range, unit, review dates, pause rules (section 2.1 step 8).
- **Funding:** cash or margin needed per lot (from NSE/Groww margin, measured), separate from maximum loss.

Parameters are fixed per version. Changing a threshold makes a new version, which goes through the research loop
again. A version number alone does not cure selection bias; the research ledger records how many variants were tried
(Bailey et al., *The Probability of Backtest Overfitting*).

### 4.1 The decision record (one per opportunity, code)

| Step | Content |
|---|---|
| Observations | Inputs with source and availability time; missing inputs; which role contributed what |
| Forecast | What is forecast and over which horizon: e.g. realised volatility from entry to the planned exit, as the rule's tested conditional distribution of P&L in similar conditions |
| Trade | Exact legs, prices, size, exits, expiry; the feasible alternatives considered |
| Value | Expected net P&L over the whole trade life after charges and pads; adverse scenarios; sensitivity to forecast error |
| Account | Cash/margin, open exposure, risk used, and the no-trade alternative |
| Reason | Why this information should help; what would prove it wrong; disagreements and the final reason |

For a fixed rule the forecast is normally the tested rule's own P&L distribution in comparable conditions, not a new
model each day (KISS); a separate forecasting model is added only if it beats that baseline in tests.

## 5. Independent agents

- **One agent per AI role:** its own prompt (from `AGENTS.md`), its own inputs, a fixed report format (JSON plus a
  short text). Agents run in parallel and do **not** see each other's reports before submitting (avoids copying and
  groupthink).
- **Combination is explicit:** the head of desk and portfolio manager read all reports; disagreements are recorded,
  not hidden.
- **Different models where it matters:** the judge always runs on a different model from the work it checks (e.g.
  Claude proposes, ChatGPT judges, or the reverse); the red team should also differ from the proposer. This is a
  process control, not a guarantee: both can repeat the same wrong input.
- **Anything that can change a trade is part of the algorithm:** prompts and models that affect decisions are
  versioned and evaluated; a trader's or strategist's discretionary veto is recorded and its effect measured
  separately.
- **No agent can change limits, data or the playbook.** Agents read data and write reports; code applies the rules.
- **Everything is recorded:** every report, decision and verdict is stored with the data it used (reproducible).

## 6. The judge

- **Independent:** checks work, never does it; different model from the author; no stake in the outcome.
- **Three separate checks:**
  1. **Hard validity** (code, not a model's opinion): timestamps, contracts, arithmetic, funding, owner limits.
  2. **Research sufficiency:** sample, uncertainty, number of trials (ledger), execution assumptions, counter-evidence.
  3. **Interpretation:** does the economic reason follow from the evidence.
- **Verdicts:** pass, or fail with the exact reasons and what must be redone. A failed daily decision means no trade
  that day; a failed research claim goes back to its author.
- **Authority:** can block any trade or strategy. Only the owner can overrule a judgement (2 or 3), in writing,
  logged, and overridden paper trades are scored separately from the tested policy. No one can overrule a hard
  validity failure: stale data or wrong arithmetic stays invalid.
- **Is itself audited:** failure categories are fixed in advance; each month a stratified sample of approvals,
  rejections and abstentions (and every override) is re-checked against independently recalculated evidence and
  seeded test cases with known answers, counting false approvals and false rejections. Agreement between two models
  is not the ground truth.

## 7. Failure handling

| Situation | What happens |
|---|---|
| Data missing or stale | No new trades; last good prices are marked stale and never used as fill prices; alert |
| An AI role fails to report | Its rule conditions count as not met (no trade on missing information) |
| Agents disagree | Recorded; the playbook rule decides; the red team's objection is shown to the judge |
| Judge or AI unavailable | No new trades that day; risk-reducing exits still run (code) |
| Risk limits hit | Code closes or blocks; no discussion |
| Drawdown brake hit | Definition to be decided by the owner (equity basis, threshold, block entries or close, who restarts) |
| A protective leg missing | Not a protected trade: close it |
| Paper results outside the expected range | Per the strategy's evaluation plan; a paused strategy's open trades are still managed |

Owner limits, stated precisely: Rs 10,000 maximum loss per trade and 3 open trades cap the money at risk **at one
time** (Rs 30,000, 6%). They do not cap a month's loss: six full losses in a month are Rs 60,000 (12%). That is what
the drawdown brake is for.

## 8. Cost and effort: net profit includes the desk's own running cost

About 10-15 AI role calls a day plus research sessions. Needs AI API keys (owner's environment, never in files) and a
monthly budget to be estimated once the design is agreed. Code roles add no cash cost today (they run in the existing
environment); any real compute, storage or data bill is counted at its actual amount.

Three ledgers: (1) **trade P&L** after charges and pads; (2) **account result** after the desk's operating costs (AI,
data); (3) **tax** at 31.2% on the year's net F&O profit (a research model, not tax advice). Example: three trades
making Rs 500 each is Rs 1,500 a month; a Rs 3,000 monthly AI bill makes the desk lose money. Each AI role must add
more net decision value than it costs, or it is removed.

## 9. Build order (after owner approval)

1. Research loop first, by hand (as in desk meeting 1): the playbook needs at least one strategy that passes before
   anything is automated.
2. Playbook format and the code roles (data, risk, cost/tax, rule evaluation).
3. Daily paper desk with code roles only, on the first approved strategy. Judging at this stage: the code hard-validity
   checks every day, plus a manual independent review (the other AI, in the repository) of research and paper results.
4. AI roles and the AI judge added one at a time (only after the owner starts the AI plan); each must show it improves
   decisions against the code-only desk on the same opportunities, including its abstentions, or it is removed.
5. Intraday watching, only if data shows it helps.

## 10. Questions for review (answered in ChatGPT review 9; open points in response 8)

1. Is the split "fixed strategies, dynamic decisions" right, or should some strategy parameters adapt automatically
   (and how would that be tested without overfitting)?
2. Which roles must be code, and which genuinely need a language model?
3. How should the judge be audited, and what stops it being too lenient or too strict?
4. What is missing for the goal: a role, a check, a failure case?
