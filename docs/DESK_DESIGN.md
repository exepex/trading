# Desk design: a team of expert roles finding net profitable F&O trades

Status: **design for review** (12 Oct 2026). Nothing here is built yet; the AI layer stays on hold until the owner
approves. Owner decisions it must respect: `docs/DESK_DECISIONS.md`. Roles and working rules: `AGENTS.md`.

## 1. The goal and the one principle

**Goal:** net profitable NSE F&O trades: profitable after all charges, slippage and tax (31.2%), proven on real data,
then on paper, before any real money.

**Principle: strategies are fixed and tested in advance; daily decisions inside them are dynamic.** A strategy is
never invented and traded on the same day: an untested rule is a guess. Strategies are created slowly in a research
loop and stored in a versioned playbook; every day the desk decides, from that day's data, whether a playbook rule
fires, on which contracts and at what size.

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
5. **Red team.** Tries to break it: luck, a period that flatters it, a scenario that blows the Rs 10,000 limit.
6. **Judge.** Verifies every claim (section 6). Fails send the work back.
7. **Owner approval.** Approved strategies enter the playbook as a new version; nothing enters without it.
8. **Paper trading.** At least 3 months and 20 positions before any real-money discussion; live results are compared
   with the backtest's expected range. A strategy outside that range is paused and sent back to step 2.

### 2.2 Daily loop: how decisions are made (3:00 pm)
1. **Data check** (data engineer, code): today's NSE/Groww data present, fresh and consistent; otherwise no new trades.
2. **Role reports** (independent, in parallel), each a short structured report, for example:
   - volatility trader: implied vs realised volatility, skew, term structure, and how that compares with history;
   - macro / event analyst: scheduled events inside each candidate holding window (RBI, Budget, elections, results);
   - positioning analyst: open interest, put-call ratio, FII/DII positions;
   - quant modeller: volatility forecast and market regime;
   - risk manager (code): open trades, rupees at risk, room left under the limits.
3. **Playbook check** (code): each approved rule is evaluated on the reports; a rule fires only if all its conditions
   hold. The rule, not a model, chooses strikes and size.
4. **Cost and tax check** (code): the expected net value after charges, pads and tax must stay positive.
5. **Judge check:** inputs are today's, every rule was applied as written, limits respected, reports consistent.
6. **Paper trade** opens; Slack message to #fno-desk with the reasons from each role.
7. **Open-trade review** (same team, same time): hold, take profit, or close at the rule's limit; the risk manager's
   hard limits apply without discussion.

Intraday watching is a later layer, added only if data shows it improves net results (owner decision).

## 3. The team

One shared goal; each role has its own job, inputs and output, and no role decides alone.

| Role | Runs as | Daily job | Research job |
|---|---|---|---|
| Head of desk | AI | Runs the meeting; makes sure every role reported | Sets questions; records decisions |
| Portfolio manager | AI | Picks among firing playbook rules when several do | Turns findings into strategy proposals |
| Volatility trader | Code + AI | Implied vs realised volatility, skew, term structure | Volatility-premium studies |
| Options strategist | AI | Checks the structure fits the view | Designs structures (spreads, condors) |
| F&O trader | AI | Liquidity, spreads, expiry and gap practicalities | What fails in live markets |
| Quant / statistician | Code | Regime and forecast numbers | Backtests, controls, significance |
| Quantitative modeller | Code | Volatility forecast | Builds and validates forecasts |
| Risk manager | **Code** | Limits: Rs 10,000 per trade, 3 open, drawdown brakes | Worst cases, stress tests |
| Macro economist / event analyst | AI | Events inside holding windows | Event effects on volatility |
| Positioning analyst | Code + AI | OI, PCR, FII/DII | Does positioning add anything |
| Market research analyst | AI | Market mood, sectors, news against expectations | News impact studies |
| Equity research analyst | AI | (stock options) results, company news | Stock-specific edges |
| Investment banker | AI | Corporate actions, block deals | Event-driven moves |
| Microstructure / execution | Code + AI | Bid-ask, fill assumptions | Calibrate the pad from real quotes |
| Regulation (SEBI/NSE) | AI | Rule changes, lot sizes, expiry days | Effect of rule changes |
| Behavioural finance | AI | Flags overtrading, chasing | Owner's and retail biases |
| Tax and cost accountant | **Code** | Net value after charges and 31.2% tax | Net results of every test |
| Data and backtesting engineer | **Code** | Data present, fresh, consistent | Data quality, no look-ahead |
| Mathematician | AI | Sanity of payoffs and sizes | Pricing and expected value |
| Red team | AI | Challenges the day's proposal | Tries to break each strategy |
| **Judge** | AI, **different model** from the work checked | Verifies the day's decision | Verifies every research claim |

"Code" roles are deterministic, tested Python: exact numbers, same answer every time. "AI" roles are language-model
agents for judgement.

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

Parameters are fixed per version. Changing a threshold makes a new version, which goes through the research loop
again (prevents tuning to past results).

## 5. Independent agents

- **One agent per AI role:** its own prompt (from `AGENTS.md`), its own inputs, a fixed report format (JSON plus a
  short text). Agents run in parallel and do **not** see each other's reports before submitting (avoids copying and
  groupthink).
- **Combination is explicit:** the head of desk and portfolio manager read all reports; disagreements are recorded,
  not hidden.
- **Different models where it matters:** the judge always runs on a different model from the work it checks (e.g.
  Claude proposes, ChatGPT judges, or the reverse); the red team should also differ from the proposer.
- **No agent can change limits, data or the playbook.** Agents read data and write reports; code applies the rules.
- **Everything is recorded:** every report, decision and verdict is stored with the data it used (reproducible).

## 6. The judge

- **Independent:** checks work, never does it; different model from the author; no stake in the outcome.
- **Checks evidence, not words:** re-runs the scripts, compares numbers with the data, confirms each role produced its
  report, confirms rules were applied as written, confirms limits were respected.
- **Verdicts:** pass, or fail with the exact reasons and what must be redone. A failed daily decision means no trade
  that day; a failed research claim goes back to its author.
- **Authority:** can block any trade or strategy. Only the owner can overrule the judge, in writing (logged).
- **Is itself audited:** a sample of verdicts is re-checked by the other model each month.

## 7. Failure handling

| Situation | What happens |
|---|---|
| Data missing or stale | No new trades; open trades reviewed with the last good data; alert |
| An AI role fails to report | Its rule conditions count as not met (no trade on missing information) |
| Agents disagree | Recorded; the playbook rule decides; the red team's objection is shown to the judge |
| Judge unavailable | No new trades that day |
| Risk limits hit | Code closes or blocks; no discussion |
| Paper results outside the expected range | Strategy paused, back to research |

## 8. Cost and effort (to be estimated before building)

About 10-15 AI role calls a day plus research sessions. Needs AI API keys (owner's environment, never in files) and a
monthly budget to be estimated once the design is agreed. Code roles cost nothing to run.

## 9. Build order (after owner approval)

1. Research loop first, by hand (as in desk meeting 1): the playbook needs at least one strategy that passes before
   anything is automated.
2. Playbook format and the code roles (data, risk, cost/tax, rule evaluation).
3. Daily paper desk with code roles only, on the first approved strategy.
4. AI roles and the judge added one at a time; each must show it improves decisions (measured), or it is removed.
5. Intraday watching, only if data shows it helps.

## 10. Questions for review

1. Is the split "fixed strategies, dynamic decisions" right, or should some strategy parameters adapt automatically
   (and how would that be tested without overfitting)?
2. Which roles must be code, and which genuinely need a language model?
3. How should the judge be audited, and what stops it being too lenient or too strict?
4. What is missing for the goal: a role, a check, a failure case?
