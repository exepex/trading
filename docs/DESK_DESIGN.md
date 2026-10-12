# Desk design: a team of experts finding the most profitable F&O trades, against the odds

Version 2.1 (12 Oct 2026; agreed by both AIs; **approved by the owner as the framework on 12 Oct 2026**, implementation waits for the owner's separate decision): version 2 amended after ChatGPT review 10 (answer: `reviews/claude/response_10_2026-10-12-desk-design-v2.md`), plus the owner's additions (discovery engine 3.5, portfolio risk 8.1).
Version 2 was a full rewrite. Version 1 described controls well but not the core: **how a team of experts
in different fields works together to find winning trades**. This version puts that first; the controls agreed in
review 9 are kept in sections 6-9. Nothing is built yet; the AI layer stays on hold until the owner approves.
Owner decisions: `docs/DESK_DECISIONS.md`. Roles and working rules: `AGENTS.md`.

**How this design is closed:** section 11 lists every section with each AI's position. The design is final when both
AIs mark every section "agreed" (or the owner settles a disagreement) and the owner approves. No next step (desk
meeting 2, building) starts before that.

## 1. The goal and the odds we are up against

**Goal:** the most profitable NSE F&O trades **net** of charges, slippage, the desk's own running costs and 31.2% tax,
proven on real data, then on paper, before any real money.

**The odds (SEBI; details and sources in `reports/Retail FnO losses and safeguards.md`):**
- 88-93% of individual F&O traders lost money in every year measured (FY22-FY26); FY26: 87.7% lost, Rs 91,685 crore
  in total (SEBI press release, 20 Aug 2026).
- 59% of index-option turnover is same-day expiry, 75% within one day, 97% within a week (same release).
- In SEBI's FY26 behavioural sample, about 93% were predominantly option buyers and about 90% of them lost; of the few
  predominantly sellers, about 44% lost. (Sample, not the whole population; secondary summaries, detailed study not
  re-verified; groups differ in capital and activity, so this is not proof that switching sides pays.)
- About 0.5% were profitable in all five years FY22-FY26 (secondary summary); costs were about 35% of loss-makers'
  gross losses.
- Most profits went to proprietary firms and foreign investors, mostly to "algo entities", which SEBI defines as any
  entity that sent at least one algorithmic order in the year: this does not prove that speed is the source.

**What "winning against the odds" means for us:** retail outcomes motivate strict net accounting and risk discipline.
Our initial research prioritises slower, capped-risk opportunities compatible with the owner's decision schedule.
Sustainable mechanisms may include compensation for bearing unwanted risk, conditional mispricing and better
cost-adjusted selection. **No side or horizon is assumed profitable or neglected; each thesis must establish its own
evidence.**

**The first question for every thesis:** what service, risk transfer or information advantage could give positive
expected net value; what pays for it; and what evidence would show it is not enough? A good story can still fail the
data. A pattern the data supports but no one can explain may stay in research, and can only be traded with a
stricter statistical bar and at most one lot (section 3.5).

## 2. Where a small, patient desk can win: the edge map

Each edge family has an economic reason (who pays), owning roles, the data that tests it, and its evidence today.
The team's research works through this map; any role may add a family when it has a reason and data.

| # | Edge family | Who pays us, and why | Owning roles | Data to test it | Evidence now |
|---|---|---|---|---|---|
| E1 | Volatility risk premium (sell protected insurance) | Some buyers pay for protection: a premium for carrying crash risk, possibly fair; the test is whether the premium exceeds the expected protected loss plus all costs within our limits | Volatility trader, options strategist, risk manager | NSE daily option chains, 2019-2026 | **Some evidence:** IV 13.8% vs realised 12.2%; protected condors +Rs 24,757 to +69,026 (10-30 months, data gap), but most 2% and 3% condors exceed the Rs 10,000 cap per lot (meeting 1 correction); at-the-money flies fit |
| E2 | Conditional volatility pricing (when to sell, buy or stay out) | Same payers; the edge is choosing the action by entry-known conditions | Volatility trader, quant modeller, statistician | Same, plus past realised volatility | **Some evidence at most:** "IV above past 20-day realised" kept 27 months (+Rs 3,10,568, worst -7,867), skipped 5 incl. the 3 worst (naked straddle, diagnostic). Mechanism unclear: two of the three worst came from steady one-way moves (+4.0%, +4.5%) with low realised volatility, so an unhedged trade is also a bet on the net move |
| E9 | Conditional buying of protected movement | Option sellers may at times underprice coming movement or jumps (hypothesis, no claimed edge) | Volatility trader, quant modeller, options strategist | Full chains, past-only forecasts, events | Untested; bounded-debit structures only, never cheap far-out "lottery" options |
| E3 | Event premium | Option buyers before RBI, Budget, elections, results; IV often falls after (VIX -12% to -34% on past event days), but surprises spike it | Macro economist, equity research, volatility trader | Event calendar + chains around each event | Untested |
| E4 | Term structure and short-dated richness | Retail crowds into weekly and same-day options; sellers of near-dated options or calendar structures may be paid | Positioning analyst, volatility trader, regulation | Weekly vs monthly chains | Untested; expiry-day trading itself is excluded (algorithm territory) |
| E5 | Skew (puts vs calls) | Hedgers pay for downside puts; lottery buyers pay for far calls | Options strategist, behavioural finance | Full chains (far strikes) | Untested; needs the full raw files |
| E6 | Conditional direction | Forced or slow flows (FII positioning extremes, after-shock drift) | Positioning analyst, macro, quant | FII/DII data, futures OI, prices | Simple trend: **none** (50-52%); conditional: untested |
| E7 | Stock vs index | Single-stock moves on results vs index volatility (dispersion) | Equity research, investment banker, volatility trader | Stock option chains, results calendar | Untested; stock options settle physically, need own rules |
| E8 | Cost advantage | Not an edge alone: a patient monthly trader with limit orders avoids the cost drag that sinks the crowd | Execution, tax and cost accountant | Real quotes (to calibrate the Rs 1 pad) | Assumed, not measured |

**Excluded from the initial scope** (a practical choice for our schedule, data and limits, not proof that no edge
exists there): latency races, expiry-day trading, closing-auction moves, order-flow reading, cheap far-out options.

## 3. The team: how experts work together (the core)

### 3.1 One goal, distinct jobs
Every role works for the same goal (net profitable trades) from its own field. Each role:
- **owns** edge families and questions (section 2), its own data, and the risks of its field;
- produces **finding cards**: observation (data, source, when it was known), interpretation, measurable implication
  for a trade, confidence (strong / some / reasoning only), counter-evidence, what would prove it wrong; or "not
  applicable" (never invented numbers);
- has a **scorecard** of one of two kinds:
  - **Optional judgement roles** (e.g. macro, market research, positioning interpretation): compared on the same
    dated opportunities with and without the role's contribution (paired shadow decisions), as the difference in
    account net result after the role's own running cost; abstentions and rejected trades count, not only endorsed
    winners; judged only over the opportunities where the role applies; joint tests where roles interact; frozen
    before results. Simulated, so the same price rules and uncertainty apply. Lower risk can justify lower profit.
  - **Mandatory control roles** (data, risk, cost/tax, regulation, judge's hard checks): scored on correctness, caught
    violations, funding and protection integrity, stress results. Never removed because no disaster happened lately.

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

A thesis missing any part is not a trade; a part may be a valid "not applicable", and the parts need not be separate
paid model calls. The **portfolio manager** assembles theses and, after funding, joint exposure, uncertainty and
holding-period limits, ranks them by expected net money per rupee of risk (a starting heuristic) against no trade.

### 3.3 The meeting (research and daily use the same rhythm)
1. **Question** (head of desk): one question, e.g. "Which entry-known conditions improve a protected seller's net
   payoff?"
2. **Independent findings:** each role studies the data alone and submits its cards before seeing anyone else's
   (prevents copying and groupthink).
3. **Cross-examination:** each role tests the material assumptions of other fields' findings, e.g. the risk manager
   tests the volatility trader's idea against the worst gap; the macro economist names the event that breaks it.
   Agreement after checking is a valid outcome; no objection quotas.
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

### 3.5 The discovery engine: computing power without fooling ourselves (code)
The team's advantage over a human trader is memory and testing power: every pattern can be checked on every day.
The danger is the same power: among 1,000 random coin-toss patterns tested on 33 monthly cycles, about 18 win 23 or
more (69.7%) by luck alone (exact binomial; about 7 win 24 or more, 70%+). Expected counts, not a guarantee. The engine (owned by the quant / statistician and data engineer) works like this:
1. **Feature library**, each with an availability time: candles and gaps, past realised volatility, implied
   volatility, skew and term structure, India VIX, OI and put-call ratio, FII/DII positions, event calendar,
   calendar effects, and combinations of these.
2. **Candidate generator:** systematic combinations of features and actions (sell protected, buy protected, no trade)
   on feasible structures. Every candidate is counted in the ledger automatically.
3. **Scan on discovery data** after real charges and pads, measuring net P&L, worst case and stability across years.
4. **Mechanism filter:** survivors go to the roles for an economic explanation (section 1). Unexplained ones may stay
   in research only, with a stricter bar and at most one lot.
5. **Bar rises with the number of tries:** significance judged against the number of candidates scanned, plus
   controls (coin toss, opposite). Harvey, Liu and Zhu (t of about 3 rather than 2) motivate this but give no
   universal cutoff for our small, dependent option samples: each experiment protocol fixes its own test (sample,
   trial count, dependence) before candidates are evaluated.
6. **Challenge on data not used for discovery** (2019-2023), with any fitting using only earlier data; then forward
   paper trading. Nothing is tuned after seeing the challenge.
The roles then do what the engine cannot: explain, find the event that breaks it, price it and size it.

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
- **Discovery data:** NIFTY 2024-2026 has been looked at and can never be called out-of-sample. 2019-2023 is a
  historical challenge to an already chosen idea (not a deployment replay: any fitted forecast uses only data before
  each test decision); forward paper trading is the clean check. After tuning on 2019-2023 it is no longer untouched.
- **Pass/fail fixed before a test runs.** No tuning on the check data. Beating an unfiltered version is a screen, not
  a promotion: a strategy must also make money net on its own and pass the full evaluation plan.
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
  risk at one time); holdings up to 2-3 weeks; decisions at 3:00 pm.
- **Drawdown brake (owner decision):** when closed-trade equity is Rs 30,000 below its highest point, **no new
  trades**; open trades continue under their own rules (exits included) until they close; they are not force-closed.
  Restart only by the owner in writing; the full history and the old high point are kept, and the brake re-arms at
  Rs 30,000 below the equity on the restart day (recorded). Worst case basis: from the closed-equity high point, with
  every open trade fully protected and capped, about Rs 60,000 (Rs 30,000 + 3 x Rs 10,000), 12%; not a monthly bound
  and not a bound if protection or funding breaks. Marked account value and open exposure are always shown too.
  (Today's old live desk closes all trades when its kill switch fires; the new desk follows this rule.)
- Protection bought first and sold last; a missing protective leg means close. Margin is tracked apart from loss.

### 8.1 Portfolio risk: the whole account, not just each trade (risk manager, code)
Three NIFTY trades are close to one bet, so the account is checked as a whole before every new trade:
- **Stress tests:** all open trades plus the proposed one fully re-priced (not Greek estimates) under fixed
  scenarios: NIFTY +/-5% and +/-8% overnight; implied volatility doubled and halved (a fall hurts bought options);
  joint price-and-volatility shocks; the passage of time; replays of 23 Mar 2020, 4 Jun 2024 and Feb 2026 (labelled
  stress tests, not the worst possible case). Combined stress loss must stay within Rs 30,000, and stressed margin
  within available cash. Loss from current marked value and maximum loss from entry are shown separately. The
  scenario engine and its thresholds are specified and tested before they govern paper trading.
- **Exposure limits (the Greeks):** account loss from a 2% NIFTY move at most Rs 15,000 (direction, delta) and from a
  5-point rise in implied volatility at most Rs 15,000 (volatility, vega). Proposed values, reasoning only; set from
  research before paper trading.
- **Spread across strategies by evidence:** a strategy without a paper record may hold at most 1 of the 3 slots;
  slots move between strategies only at scheduled reviews, by their evidence; not all 3 slots on the same strategy
  and expiry until it is proven.
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
| Per-trade or portfolio limit hit | Code blocks the new trade; a broken protection is closed; no discussion |
| Drawdown brake hit | No new trades; open trades continue under their own exit rules; owner restarts (section 8) |
| Paper results outside the plan | As the strategy's evaluation plan says; open trades still managed |

## 10. Build order (after owner approval of this design)

1. Research meetings by hand on the edge map (E1-E2 first, with full chains and 2019-2023), until one strategy passes.
2. Playbook format and the code roles (data, risk, cost/tax, rule evaluation, hard-validity checks).
3. Daily paper desk with code roles on the first approved strategy; the other AI reviews results in the repository.
4. AI roles, red team and AI judge added one at a time (after the owner starts the AI plan); each kept only if it
   adds net value against the code-only desk.
5. Intraday watching only if data shows it helps.

## 12. Three paper strategies: pure rules, hybrid, fully AI (proposed v2.2, for review)

Status: **proposed by the owner on 12 Oct 2026, for ChatGPT review**; replaces the two-book draft of the same day; not
part of the approved v2.1 until agreed and approved. Owner's aim: "we do not know whether AI or rules are smarter ...
prove both, find where each is lacking, and get the best of both", working as a team of roles.

### 12.1 The three strategies (three paper books)
| | Book 1: pure rules | Book 2: hybrid | Book 3: fully AI |
|---|---|---|---|
| Who analyses the data | Code: statistics and tested formulas | AI roles (finding cards, section 3) | AI roles |
| Who decides the trade | Tested playbook rules only | AI decides, **inside boundaries set by tested rules** (which strategies are allowed, entry conditions that must hold, sizes) | AI decides everything, including designing its own strategies |
| AI while trading | None (AI only helps research beforehand) | Analysis; chooses, times, skips or exits early within the boundaries | Full control within the owner's money limits |
| Evidence before paper | Historical test (experiment protocols, sections 4-6) | Boundaries tested on history; the AI's choices only on paper | None possible: an AI's judgement on past dates is contaminated by hindsight; paper only |
| A change is | A new playbook version (research loop) | New boundary version (research loop) or new AI version (recorded) | A new AI version (model, prompts, roles), recorded |

The three answer three separate questions: do tested rules alone make money; does AI judgement improve tested rules;
does AI alone beat both.

### 12.2 The owner's money limits apply to all three (not strategy rules)
Enforced by code for every book (C2, C4), whatever the strategy decides: Rs 10,000 maximum loss per trade including
costs; at most 3 open trades; Rs 30,000 entry-blocking drawdown brake; portfolio stress; **defined-risk trades only**
(maximum loss known at entry); never real orders. Without these, a book could win by taking risks the others may not,
and the comparison would teach the wrong lesson.

### 12.3 Same rules of the game (fairness)
- Separate Rs 5 lakh paper accounts per book (E4's lock is per account; books never share an account).
- Same market at the start: NIFTY options, holding up to 3 weeks; book 3 chooses its own structures, strikes and
  expiries within that. Wider markets (BANKNIFTY, stocks) are opened to all books together, later.
- Same decision time (about 15:00 IST), data cutoff, real 3 pm quotes (A4), fill model (E1) and charges (C1).
- Independence: no book sees another book's decision of the day before committing its own.
- Pre-commitment: every decision with its reasons is written to the decision record (D3) and committed to git before any
  fill or outcome exists.
- Each book's AI costs are charged to its own account ledger (C1, F5); book 1 has none at run time.

### 12.4 Scoring predictions every day, not only trades
Each book makes 2-3 trades a month: after 3 months about 10 trades each, too few to separate skill from luck unless
the difference is very large. So all three books answer a **fixed set of daily forecast questions** (frozen before the
start), for example: probability that NIFTY closes within +/-2%, +/-3% and +/-5% of today's close at the next monthly
expiry; probability that India VIX is higher in 10 trading days. Scored daily with proper scores (Brier and log score):
about 20 scored days a month per book.
- Book 1's forecasts come from code (its tested conditional frequencies); books 2 and 3 from their AI roles.
- All are compared with the **option market's own forecast**: the probabilities implied by that day's NIFTY option
  prices. Beating the option market's forecast is the real test of skill.
- With three books, comparisons are pairwise (1 vs 2, 2 vs 3, 1 vs 3, each vs the market) and the uncertainty bands
  account for the number of comparisons.

### 12.5 Evaluation plan (fixed before the start)
- Monthly report: three ledgers per book, drawdown, open risk, forecast scores against each other and against the
  option-implied baseline, with uncertainty.
- First scheduled verdict after 6 months; nothing is switched off for statistical reasons before a scheduled review
  (hard-loss rules act at once, as for every strategy).
- "Better" is judged on paired days: forecast-score differences with their intervals, and net account result after
  costs. An inconclusive result is reported as inconclusive.
- Where each book fails is studied by the roles (lessons memory) and becomes research questions.

### 12.6 Combining the best
A combination of what works in each book is a **new design**, tested like any other: registered, evaluated on forward
paper data it was not built from, judged and approved by the owner. No book silently borrows another's decisions.

### 12.7 Timing and effect on the plan
- Book 1 trades only after a strategy passes the historical test (experiment 1 and later); until then it holds cash but
  still forecasts from code, so forecast scoring starts on day one.
- Book 2 trades only inside approved boundaries, so it also waits for a passed strategy; its AI forecasts can start
  earlier.
- Book 3 needs no historical test, only plumbing: paper account and fills (E1 fill model on A4 quotes), risk and
  validity code (C2, C4), decision records (D3), role agents (F1), cost tracking (F5). It can start first.
- Owner decisions D1 and D2 (`docs/AI_PLAN_REEVALUATION.md`) resolve per book: no AI authority in book 1; AI choices
  within boundaries in book 2; AI vetoes, entries and early exits in book 3; all inside the money limits. D4 (runtime and
  budget) must be decided before books 2 and 3 start.
- The implementation plan is rewritten for the three books (data, research engine, code roles and playbook mostly
  unchanged; paper desk per book; AI layer for books 2 and 3; forecast scoring; comparison report), and the GitHub
  issues are recreated from it as a clean set.

### 12.8 Honest limits
- Slow: trade-level proof takes many months; forecast scores come sooner but measure reading the market, not profit.
- A changing AI (new model versions) makes books 2 and 3 moving targets: each version is recorded and scored separately.
- Book 3's own strategies cannot be tested on history, so its early paper results are the first evidence of any kind.
- Three books need three times the paper bookkeeping and, for books 2 and 3, a monthly AI budget.

## 11. Closing the design

| Section | Claude | ChatGPT | Owner |
|---|---|---|---|
| 1 Goal and odds | Agreed; amended per review 10 (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 2 Edge map | Agreed; amended per review 10, E9 added (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 3 The team and how it works | Agreed; scorecards amended, 3.5 discovery engine added (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 3.5 Discovery engine | Agreed (covered by section 3) | Agreed as research framework (review 11) | Approved 12 Oct 2026 |
| 4 Two loops | Agreed | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 5 Playbook and decision record | Agreed | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 6 Evidence rules | Agreed; 2019-2023 and screen clarifications added (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 7 Red team and judge | Agreed (from review 9) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 8 Owner limits, risk and money | Agreed; brake action and basis defined, 8.1 portfolio risk added (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 8.1 Portfolio risk | Agreed (covered by section 8) | Agreed as research framework; proposed thresholds require calibration (review 11) | Approved 12 Oct 2026 |
| 9 Failure handling | Agreed; brake row aligned (v2.1) | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 10 Build order | Agreed | Agreed (review 11, v2.1) | Approved 12 Oct 2026 |
| 12 Three paper strategies (proposed v2.2) | Proposed: owner's idea, written up 12 Oct 2026 | | |

Both AIs agreed every section (ChatGPT review 11, Claude response 12). Review 11's clarifications (exact binomial
figures, experiment-specific significance test, fuller stress scenarios) are folded into 3.5 and 8.1 without changing
their substance. **Owner approved the framework on 12 Oct 2026 ("A, approve design v2.1 but wait for my decision for implementation"). Implementation, research experiments and building wait for the owner's separate go-ahead.** Approval covers the framework only: no strategy is proven, and
the proposed thresholds (e.g. Rs 15,000 exposure limits) are set from research before paper trading.
