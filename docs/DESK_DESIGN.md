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
  (The removed old desk closed all trades when its kill switch fired; the new desk follows this rule.)
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

## 12. Three paper strategies: pure rules, hybrid, fully AI (v2.2, approved by the owner on 12 Oct 2026)

Status: **approved by the owner on 12 Oct 2026** after ChatGPT reviews 18-19 (answer:
`reviews/claude/response_23_2026-10-12-review-18.md`); now part of the approved design (v2.2). Owner's
aim: "we do not know whether AI or rules are smarter ... prove both, find where each is lacking, and get the best of
both", working as a team of roles. This section supersedes the D1/D2 recommendations of the
old AI-plan re-evaluation (removed in the clean-slate cleanup; in git history) for the three books (12.9).

### 12.1 The three books and the questions they answer
| | Book 1: pure rules | Book 2: hybrid | Book 3: fully AI |
|---|---|---|---|
| Who analyses | Code (statistics, tested formulas) | AI roles (finding cards, section 3) | AI roles |
| Who decides | Tested playbook rules only | AI, inside a frozen **authority envelope** (12.2) around tested playbook rules | AI, including designing its own strategies, inside the Book-3 constitution (12.3) |
| Evidence before paper | Historical test (sections 4-6) | Playbook tested on history; AI's changes only on paper | None possible (an AI's judgement on past dates is contaminated by hindsight) |
| Question answered | Do tested rules alone make net money forward? | Does AI judgement add value **within the same tested strategy family**? | Does the **complete AI system** (strategy invention + market reading + execution choices) make more net money under the same risk budget? |

Book 3's results are labelled as a whole-system result: a Book-3 win is never claimed as "AI daily judgement beats
rules" unless the matched comparison (12.5, scoreboard A) shows it.

### 12.2 Book 2's authority envelope (frozen per playbook version, machine-readable)
Each action is `allowed`, `shadow-only` or `forbidden`, fixed before paper starts and versioned with the playbook:
| Action | Default |
|---|---|
| Choose among simultaneously eligible approved strategies | allowed |
| No trade / veto an eligible trade | allowed |
| Delay entry (same day only, until the 15:30 close) | allowed |
| Choose strike or width from the playbook's pre-approved discrete set | allowed |
| Reduce size (never increase) | allowed |
| Choose or tighten an exit from the playbook's pre-approved exit set | allowed |
| Early event or news exit | allowed, recorded with its evidence |
| Change any threshold, feature, structure or strategy | **forbidden** (a new playbook version through the research loop) |
Every Book-2 decision record holds the rule's default action and the AI's action with its reason.

### 12.3 Book 3's constitution (frozen before its first counted decision)
- Market: NIFTY options; holding up to 3 weeks; **defined-risk structures only** (no naked short options); decision at
  about 15:00 IST with the common data cutoff; allowed data sources listed.
- **Strategy identity:** every trade carries a `strategy_id` whose full specification (entry, structure, size, exits)
  and hash are recorded **before its first trade**, with the date proposed and the model, prompt and role versions that
  created it, and whether it is new or reused. A material rule change creates a new `strategy_id`; rules are never
  edited after seeing an outcome.
- Book 3 may invent paper strategies; it may never change the owner's risk limits, data-integrity rules, the scoring
  protocol, its own evaluation criteria, or touch real money.
- Red team and judge review Book-3 strategies and decisions as evidence (sections 7, F2, F3); their objections are
  recorded, not hard blocks.

### 12.4 The owner's money limits and hard validity apply to all three
Enforced by code for every book (C2, C4): Rs 10,000 maximum loss per trade including costs; at most 3 open trades;
Rs 30,000 entry-blocking drawdown brake; portfolio stress; defined-risk only; never real orders. C4 has two modes:
books 1 and 2 are checked against their playbook; Book 3 is checked only against **hard facts and owner constraints**
(contracts exist, quotes and cutoff, payoff and maximum loss, charges, margin and stress, account limits, allowed market
and horizon, no prohibited structure). The quality of Book 3's thesis is judge and red-team evidence, not hard validity.

### 12.5 Two scoreboards
- **Scoreboard A, matched decisions (does AI judgement add value?):** on the same eligible opportunities, same
  approved strategy universe, same data cutoff, same fill model and costs, each book's decision is committed
  independently and scored on a standardised shadow account. Books 1 and 2 meet this naturally; Book 3 also commits a
  **matched shadow decision** on the common opportunity set every day.
- **Scoreboard B, whole systems (which complete system made more net paper money?):** each book's real paper account
  under its own permitted universe and the same owner risk budget.
- The two are never merged into one "AI beats rules" claim.
- **Owner's requirement (approval, 12 Oct 2026): all three books appear on both scoreboards, with every detail**, so the
  strategies can be compared from every angle: scoreboard A for all three (Book 3 through its matched shadow
  decisions) and scoreboard B for all three, each with the full reporting below and the daily forecast scores.
- Reported for both: raw account net, net per unit of risk used (maximum loss, stress usage, margin-days), trades,
  gross, execution costs, AI and data costs, net, and each version segment separately.

### 12.6 Fairness controls
- Separate Rs 5 lakh paper accounts per book (a per-account single-writer lock, story E1 criterion 9); same quotes (A4), fill model (E1), charges
  (C1) and decision time.
- **Common start:** the head-to-head trade comparison starts on a predeclared date when all three books can trade.
  Book 3's earlier trades are kept and reported as **Book-3 pilot evidence**, never as head-to-head evidence. Cash held
  by books 1 and 2 after the common start is an outcome; before it, it is not counted.
- **Independence and firewall:** no book sees another's decision of the day before committing; lessons or memories
  derived from another book's outcomes never enter a competing book during an evaluation window.
- **Versioning:** a change of model, prompt, role set, authority envelope or strategy starts a new evaluation segment;
  an emergency provider or model substitution pauses scoring for that book until recorded as a new version.
- Pre-commitment: every decision with its reasons is committed to git before any fill or outcome exists (D3).
- Each book's AI costs go to its own account ledger (C1, F5).

### 12.7 Daily forecasts: a secondary diagnostic
Trade profit decides; forecasts only diagnose market reading and cannot promote an unprofitable book. All books
answer five frozen questions every trading day, as probabilities:
1. P(NIFTY close in 20 trading days > today's close).
2. P(|NIFTY return over the next 20 trading days| >= 3%).
3. P(next-20-day annualised realised volatility > trailing 20-day realised volatility today).
4. P(India VIX close in 10 trading days > today's close).
5. P(next-20-day annualised realised volatility < today's 30-day at-the-money implied volatility) (the volatility
   premium at the core of edge families E1-E2).
Scoring: Brier score for all; log score with probabilities clipped to [0.01, 0.99]; calibration tables. Pairwise score
differences by forecast date with a moving-block bootstrap of block length 20 trading days (the targets overlap);
multiplicity across questions and pairs adjusted as fixed in the forecast protocol before scoring.
Baselines, each computed point-in-time by a frozen method: (a) the **risk-neutral** probabilities implied by NIFTY
option prices (labelled risk-neutral: option prices include risk premia and are not real-world probabilities); (b) a
historical base rate from a frozen rolling window; (c) for questions 3-5, a frozen simple statistical model. Book 1's
own forecasts come from a frozen point-in-time method, never refitted after outcomes.

### 12.8 Evaluation and stopping
- Primary verdict: net account result after execution and operating costs, within the risk budget, on scoreboards A and
  B; forecasts are secondary.
- Monthly report; the **first scheduled review is after 6 months of common-start trading**. Six months is a review date,
  not proof: promoting or combining anything requires the uncertainty criterion fixed in the evaluation protocol.
- No switch-off for statistical reasons before a scheduled review, **except**: the account brake (common to all), a
  strategy-level catastrophic loss rule, and any data, integrity or safety failure, which pause that book or strategy
  at once.
- Where each book fails is studied by the roles and becomes research questions.

### 12.9 Decisions D1 and D2 per book (supersedes the earlier recommendation)
Book 1: no AI authority (any AI view is a shadow record). Book 2: the actions in 12.2. Book 3: AI vetoes, entries and
early exits within 12.3 and 12.4. D4 (runtime and AI budget) is decided by the owner before books 2 and 3 start.

### 12.10 Combining the best
A combination is a new design, tested like any other on forward paper data it was not built from, judged and approved
by the owner. No book silently borrows another's decisions.

### 12.11 Timing and effect on the plan
Book 1 and Book 2 trade once a strategy passes the historical test; their forecasts start earlier. Book 3 starts as a
pilot once its constitution, decision records, fills and costs, C2 and C4 (Book-3 mode), role agents and the forecast
protocol exist. The implementation plan is then rewritten, reusing the approved A-D stories and adding book-specific
extensions, and the GitHub issues are recreated as a clean set.

### 12.12 Honest limits
Trade-level proof takes many months; forecast scores measure reading the market, not profit; changing AI versions
make books 2 and 3 moving targets (scored per version); Book 3's strategies cannot be tested on history; three books
need three times the bookkeeping and a monthly AI budget.

## 13. The end product: what "finished" means, how the owner sees it, where the AI runs (v2.3, revision 3, approved by the owner on 12 Oct 2026)

Status: **revision 3, approved by the owner on 12 Oct 2026** ("A, approve and write the full implementation plan"). Revision 1 (response 29) was reviewed in ChatGPT
review 24, revision 2 (response 30) in review 25 (both agreed with changes); revision 3 applies review 25's four points
(response 31), after which review 25 judged the design complete enough for the full implementation plan. Owner decisions (12 Oct 2026): web dashboard plus Slack; AI roles as cloud routines (D4
runtime); **one shared dashboard repository** serving the stock tool and this tool on separate screens, with both
repositories as backends; **Azure Database for PostgreSQL** as the shared data store. Sections 1-12 are unchanged.

### 13.1 Definition of done for the whole product
The product is finished when all of the following run every trading day without the owner doing anything, and the
first scheduled review (12.8) can be held on their records:
1. **Data:** NSE daily files 2019 to today on Drive with a passing coverage check (A1-A3); one versioned session
   calendar (A1) used by every component; the 3 pm quote recorder (A4); data checks before any decision (C3); the
   events calendar (A6).
2. **Research:** the research engine, ledger and protocol freeze (B1-B5); experiment 1 run on discovery and challenge
   data; the discovery engine (B6); at least one strategy approved through the research loop, or a documented "no
   strategy passed" result (a valid end: section 1, shut down if nothing is net profitable).
3. **Playbook and decisions:** versioned playbooks with evaluation plans (section 5); deterministic rule evaluation
   and allocation; one immutable decision record per opportunity, committed before any fill, holding input hashes and
   availability times, the rule's default action, the chosen action, reasons, the judge result and any written owner
   override (section 7); Book 2's authority envelope and Book 3's constitution and strategy registry, versioned with
   them.
4. **Three paper books** (12.1), each with its own Rs 5 lakh paper account and single-writer lock, the shared fill
   model, exits, risk manager (C2), validity checks (C4, both modes) and three ledgers (C1).
5. **AI layer** for books 2 and 3: role agents, red team, AI judge, matched shadow decisions, the firewall between
   books, version registration, cost attribution and the role-value evaluation (13.6).
6. **Forecasts** (12.7) for all books with the frozen baselines, and their scoring.
7. **Scoreboards A and B for all three books with every detail** (12.5), version segments, pilot vs head-to-head.
8. **Owner surfaces** (13.2-13.4): the F&O screens of the shared dashboard, the daily Slack message, the monthly
   report.
9. **Research feedback:** scorecards, judge audits and failures become research questions; any change reaches a book
   only as a new, owner-approved version, never by editing a live version (sections 4, 12.6, 12.8).
10. **Operations:** routines, alerts, failure handling (section 9), tests, and a judge pass on every story.
Real money, intraday decisions, other underlyings and stock options are **outside** this product; each would need its
own design and approval.

### 13.2 The dashboard: one shared, private web app
- **Architecture (owner decision):** a separate **dashboard repository** holds the web app (moved out of the stock
  tool, where it lives today as `web/`, a Next.js app on Vercel). It serves the stock screens (`/india`, `/us`) and
  the F&O screens (`/fno`) behind one login (Vercel Authentication, owner only). The stock repository and this
  repository are **backends only**: each publishes its own data; neither writes to the other or to the dashboard
  repository.
- **Data path:** after each run, this repository's code builds the F&O dashboard pages as **read-model rows** (the
  pattern the stock tool already uses: one row per page, keyed by page, with `as_of`, cutoff, built-at time,
  `schema_version`, `source_commit`, `payload_sha256` and the page payload as JSON) and writes them to its own area of
  the shared database (13.3). The dashboard reads the database only, never a backend repository.
- **Atomic publication (review 25):** each daily publication has a `publication_id` (the run ID, tied to the
  `source_commit` and the common cutoff). The backend writes and validates **all** F&O pages of a publication in one
  transaction into a history table keyed by (`product` = `fno`, `page_key`, `publication_id`), unique; then, in the
  same transaction, advances a single `fno.current_publication` row (publication ID, status, run ID, reason). The
  dashboard reads only pages of the current publication, so it never mixes two days. A failed or partial publication
  leaves the previous complete one current and records the failed run ID and reason.
- **Every number traces to a committed file:** the payloads are generated by code from committed repository records
  (decision records, ledgers, scoreboards, forecasts, data-health records); no AI writes or edits a number.
- **Data contract:** this repository owns a versioned JSON schema for its pages, with tests; the dashboard checks the
  version it expects; a breaking change is a new version.
- **F&O screens:** today per book (trade or no trade with reasons; Book 2's rule default vs AI action); open positions
  with marks, pending exits and days left; risk used per book against every owner limit (per-trade, 3 slots, brake
  distance, stress, exposure); **scoreboard A and scoreboard B, all three books, every detail in 12.5**; forecast
  scores against the baselines; the three ledgers with AI costs labelled as in 13.6; data health and alerts; version
  segments and the common-start date (pilot evidence apart); **judge results per book** (approvals, rejections,
  abstentions, owner overrides scored separately, hard-validity failures) and **drill-down to the evidence**: the
  hashes and commits of the common pack, the book's private pack, the decision, the fill snapshot and the version.
- **F&O freshness (not the stock app's age threshold):** freshness follows the versioned NSE session calendar (A1)
  and the run status: "publishing" while the daily run is in progress; "stale" when the latest completed trading day
  has no complete publication, showing the previous publication with the failed run ID and reason.
- **Access and freshness contract:** the publishing story verifies that the F&O screens and data are reachable only
  through the owner's login (an unauthenticated request is refused: test), that no secret, credential or broker
  identifier is ever in a payload, and that every screen shows its built-at time and source commit and **marks itself
  stale** when the latest completed trading day is not published. The repository records remain the source of truth;
  if access control cannot be verified, the screens are not published.
- Every screen states "paper trading only, not advice" and never shows a real-order instruction.
- **Migration (stock and dashboard work, outside this repository), in this order:** (1) provision the Azure roles and
  schemas; (2) the stock backend also publishes its read models to Azure while MotherDuck stays canonical; (3) the
  shared dashboard gains the Azure read path and contract tests; (4) old and new rows, payload hashes and API outputs
  are compared over representative pages and dates; (5) the new dashboard runs privately beside production; (6) the
  login and domain switch only after parity and freshness and error-path tests pass; (7) rollback to the old dashboard
  and MotherDuck stays available for a fixed period; (8) only then is `web/` removed from the stock repository, and
  MotherDuck retired later. No F&O launch depends on this cutover. The F&O screens are built in the dashboard repository; this
  repository's plan lists them as stories for that repository.
- **Repositories are public during development** (owner decision, to keep GitHub Actions free); they become private
  once stable. Until then the login protects the dashboard, not the repository contents.

### 13.3 The shared data store: Azure Database for PostgreSQL
- One managed Azure Database for PostgreSQL server (owner's Azure subscription; backups on). Separate schemas and
  **separate least-privilege roles** (review 25):
  - a **migration/owner role** per schema, used only to create and change tables, never by a running process;
  - **runtime writers** (stock, F&O): `CONNECT`, `USAGE` on their own schema only, and only the row operations their
    tables need; **no** `CREATE`, `DROP`, `ALTER`, no membership in owner or admin roles;
  - **dashboard runtime role**: `SELECT` only on the backends' read-model tables; row operations only on named `app`
    tables (inbox, assistant log); nothing else;
  - `CREATE` revoked on the database and the `public` schema for runtime roles and `PUBLIC`; default privileges set so
    new backend tables are readable only by the dashboard reader and writable only by their backend;
  - parameterised queries and verified TLS only; one credential per deployment, kept in that environment;
  - network access limited to the needed runtime paths where practical, with the public-access and firewall policy
    stated in the platform story;
  - tests run every role through its allowed **and forbidden** operations (DDL, cross-schema writes, reads it should
    not have, creating objects in `public`).
- Credentials live only in each environment (Vercel settings, routine environment), never in files.
- The `fno` schema is a **derived copy**: it can always be rebuilt from this repository's committed records; losing
  it loses no evidence.
- Moving the stock tool off MotherDuck is the stock tool's own project; the F&O tool never uses MotherDuck.

### 13.4 Slack and monthly report
- Slack (#fno-desk only): one message per trading day after the run (one line per book: decision, account value,
  brake distance; alerts; the dashboard link); a no-trade day still posts; failures post a short alert the same day;
  monthly headline numbers. Only channel `C0C89E8QCCD`, only `FNO_SLACK_BOT_TOKEN` or the Slack connector, never
  `SLACK_*` or #market-brief; text only; the poster refuses any other channel and any webhook (tests). Slack is a
  summary and alert surface, never the record.
- Monthly report `reports/<YYYY-MM>-scoreboard.md`, committed: both scoreboards for all three books, forecast scores,
  costs (labelled as 13.6), version segments, the judge and override audit, open research questions.

### 13.5 Where the AI runs (D4: cloud routines) and the daily protocol
- The daily run is a **scheduled Claude Code cloud session** (like the 3 pm recorder), started before 15:00 IST, on a
  fixed timetable frozen in the protocol (exact times calibrated with A4 and measured run times):
  1. **Common market pack** at the common data cutoff: market observations (daily files, quotes, VIX), session and
     event data, the common opportunity set for scoreboard A, and each item's source and availability time. It holds
     **no** book's decisions, positions, P&L, findings or memory. Hashed and committed.
  2. **Book-private pack** per book: that book's account, positions and open exits, its own past decisions, its frozen
     playbook and authority envelope (Book 2) or constitution and strategy registry (Book 3), and only the sources its
     version is allowed. Hashed and committed.
  3. Each book decides in **its own isolated sub-session** that sees only the common pack and its own private pack:
     no shared conversation, cache, memory, temporary files or another book's findings. Book 1 decides by code. Every
     decision records both pack hashes and is committed.
  4. **Decision deadline** (fixed time): a book without a committed valid decision gets a committed "no decision
     (unavailable or late)" and cannot join later that day.
  5. **Execution snapshot** at a fixed time after the deadline, whatever any book did: one fresh quote snapshot, and
     every timely decision is filled by the same fill model against the **same snapshot identifier and hash**. If that
     snapshot is invalid or incomplete, **no book opens new risk** that day, unless the protocol's retry (the same for
     all books) produces a valid one before the close. Risk-reducing exits run independently (section 9).
- **Model identity and versions:** a version (model, prompt, role set, source contract) is **registered and committed
  before its first counted decision**. Each decision records the model the session actually served; if it differs
  from the registered version (an unplanned fallback), that day's decision is "AI unavailable, unscored", and scoring
  for that book pauses until a new version is registered (12.6). A version is never declared after seeing its
  decisions.
- **Failure:** a failed session or usage limit gives "no decision (AI unavailable)": no trade on scoreboard B,
  excluded from judgement scores on scoreboard A, alerted. Code still runs risk-reducing exits.
- No AI API keys; secrets only in the environment; nothing places orders.

### 13.6 AI cost and whether each AI role earns its cost
- **Three labelled figures, never merged:** (1) **actual cash spend** that can be identified (none expected beyond
  the plan); (2) **allocated plan cost**: the owner's recorded monthly plan cost shared by measured usage (sessions,
  duration, and tokens where available) with a frozen formula, labelled "allocated, not a bill"; (3) **incremental
  value estimate** from the role-value evaluation below.
- **Role-value evaluation:** before a role or role group is counted, its evaluation is fixed: where safe, a paired
  **ablation** (the same eligible decisions with the role withheld, as a shadow decision) scored on the same outcome
  metric; roles that cannot be separated are evaluated and costed **as a bundle**, never credited individually.
  Keep or drop only at predeclared review dates with the uncertainty and sample rules of the evaluation protocol.
  Mandatory control roles (data, risk, cost, validity, the judge's hard checks) are scored on caught violations and
  prevented invalid actions, not on profit (section 3.1).

### 13.7 Honest limits
- Plan usage limits are outside our control: a busy day can make an AI book unavailable (handled in 13.5).
- Allocated AI cost is an estimate, and ablation estimates need many decisions before they mean anything.
- The F&O screens depend on the dashboard migration done in other repositories; until then the monthly report and
  Slack carry the results, and the database rows are ready.
- While the repositories are public, anything committed (decision records, logs, quotes) is visible to anyone. The
  privacy of the dashboard and database is no excuse to put secrets, personal data or broker identifiers in any
  record: the same rule applies to committed backend records.

### 13.8 What the implementation plan must carry (review 25)
- **Every story names its execution repository:** `trading` (F&O records, read-model builder and publisher, F&O
  migrations and contracts, routines, Slack); `agentic-stock-prediction` (stock Azure publisher, MotherDuck
  migration); `dashboard` (shared app, login, Azure read path, F&O screens, `app` schema writes); `platform` (Azure
  server, owner roles, schemas, grants, default privileges, network, backups). Only `trading` stories are built from
  this repository; the others are specified here and built in their own repositories.
- **Every cross-repository milestone has an integration acceptance test**, so three repositories that each pass
  cannot still fail as a product.
- **Dependency order:** canonical F&O records -> F&O read-model schema and publisher -> Azure platform contract ->
  dashboard read path -> F&O screens -> migration and cutover -> automated operations. The dashboard never becomes a
  second source of truth.

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
| 12 Three paper strategies (v2.2) | Agreed after review 18 revisions (response 23) | Agreed (review 19) | Approved 12 Oct 2026 |
| 13 End product, dashboard, data store, AI runtime (v2.3) | Revision 3 after reviews 24-25 (response 31) | Agreed with changes (reviews 24, 25); review 25: complete enough for the plan once its two should-fix points are applied (done in revision 3) | Approved 12 Oct 2026 (revision 3) |

Both AIs agreed every section (ChatGPT review 11, Claude response 12). Review 11's clarifications (exact binomial
figures, experiment-specific significance test, fuller stress scenarios) are folded into 3.5 and 8.1 without changing
their substance. **Owner approved the framework on 12 Oct 2026 ("A, approve design v2.1 but wait for my decision for implementation"). Implementation, research experiments and building wait for the owner's separate go-ahead.** Approval covers the framework only: no strategy is proven, and
the proposed thresholds (e.g. Rs 15,000 exposure limits) are set from research before paper trading.
