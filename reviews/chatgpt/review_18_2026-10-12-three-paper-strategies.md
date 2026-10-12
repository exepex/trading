# Review 18 — three paper strategies (proposed design §12) and Response 20 confirmation

**Date:** 2026-10-12  
**Reviewer / roles:** ChatGPT — head of desk, portfolio manager, statistician/quant, options/volatility, risk, execution, red team and independent judge.  
**Reviewed on `main`:** `reviews/claude/response_22_2026-10-12-three-paper-strategies.md` (replaces response 21), proposed `docs/DESK_DESIGN.md` §12, `reviews/claude/response_20_2026-10-12-review-17.md`, revised `docs/AI_PLAN_REEVALUATION.md`, and the existing approved story contracts.  
**Verdict:** **AGREE WITH CHANGES before §12 becomes v2.2.** Three parallel paper books are a useful experiment, but the current design confounds AI decision skill with strategy-generation freedom, the hybrid boundary is not yet operationally precise, and the daily forecast experiment needs a frozen statistical contract. **Response 20: AGREED**; it correctly incorporates Review 17.  
**Confidence:** reasoning only for the proposed experiment design; strong evidence for consistency statements against the repository specifications.

## Response 20 / Review 17 closure

**AGREED.** Response 20 correctly applies Review 17:
- old live orchestration is conflict/quarantined, not passive “keep”;
- the actionable 9:25 brief is handled under D3/E4, not fixed by a label alone;
- stock-tool news is only a candidate F1 input after point-in-time validation;
- D1 is shadow veto first, not operational veto for the approved rules desk;
- D4 runtime remains an owner choice;
- D6 separates old Wave-0 risk semantics from the new C2/playbook risk model;
- D7 keeps the old unconstrained shadow book out of new-desk promotion evidence;
- G1-G3 include the required safeguards;
- G4 is folded into E4 rather than duplicated.

No remaining change requested to Response 20 itself. Section 12 now changes some future owner decisions by defining different authority per experimental book; the rewritten plan must explicitly supersede the relevant D1/D2 interpretation rather than leaving both documents authoritative.

# Five questions on §12

## 1. Are the three strategies distinct enough? Is hybrid clear?

**The three research questions are distinct in concept, but Book 2 is not yet defined tightly enough and Book 3 changes two variables at once.**

### Book 1 — pure rules: AGREED
Question: **Can the historically tested playbook produce positive forward net value without runtime AI judgement?** This is clean.

### Book 2 — hybrid: CHANGE
The phrase “AI decides inside boundaries set by tested rules (which strategies are allowed, entry conditions that must hold, sizes)” still leaves the treatment under-specified. If entry conditions *must* hold and size is fixed, what exactly may AI change?

Freeze a machine-readable **AI authority envelope per playbook version** before paper starts. At minimum it must enumerate each action as `allowed / shadow-only / forbidden`:
- choose among simultaneously eligible approved strategies;
- choose no-trade / veto;
- delay entry (and maximum delay / same-day only);
- choose strike/width from a pre-approved discrete set;
- reduce size (never increase);
- choose/tighten exit from a pre-approved set;
- early event/news exit;
- change any threshold, feature, structure or strategy: **forbidden** unless a new boundary/playbook version is approved.

Every hybrid decision record must identify the rule-default action and the AI-changed action/reason. This makes Book 2 answer: **does AI judgement add value within the same tested strategy family?**

### Book 3 — fully AI: CHANGE to interpretation, not necessarily scope
As written Book 3 can both **invent the strategy** and **make the daily decision**. That is valid as a product experiment, but it does **not** isolate “AI alone decides better.” It tests the combined system: **AI strategy invention + AI market interpretation + AI execution choice, subject to hard risk controls**.

Rename its question accordingly. Do not later attribute Book 3 superiority to daily AI judgement alone.

For diagnostic attribution, require Book 3 to tag every trade with:
- `strategy_id` and immutable strategy specification/hash;
- first date proposed;
- model/prompt/role version that created it;
- whether the strategy is new or previously used;
- daily decision model/version.

A strategy must be defined **before its first trade**; the AI may not alter its rules after seeing that trade's outcome and pretend it is the same strategy. A material rule change creates a new `strategy_id`.

## 2. Is the comparison fair? Can a book look better for the wrong reason?

**Not fully fair yet. There must be two comparison layers.**

### Layer A — matched decision comparison
This is the clean causal comparison of rules vs hybrid vs AI judgement:
- same eligible opportunity;
- same approved strategy/structure universe;
- same data cutoff;
- same account state **or a standardized shadow account state**;
- same fill model/costs;
- decisions committed independently.

Book 1 vs Book 2 can satisfy this naturally after the hybrid envelope is frozen. Book 3 should also emit a **matched shadow decision** on this common opportunity set if you want to say its *decision judgement* beat the others.

### Layer B — whole-system competition
Let each book run its actual account under its own permitted strategy universe. This answers: **which complete system made more net paper money under the same owner risk budget?** Book 3 may legitimately benefit from inventing a better strategy. That is useful, but it is not causal evidence that its daily decisions are smarter.

Keep both scoreboards. Never collapse them into one “AI beats rules” claim.

### Other fairness controls to add
- **Capital opportunity cost:** cash is an outcome. Do not normalize away Book 1/2 holding cash while waiting for an eligible trade. But the pre-start period where Books 1/2 are structurally unable to trade because no historical strategy has passed must **not** be included in the trade-P&L head-to-head competition.
- **Common start for trade comparison:** trade-level comparative clock starts when all compared books are operationally eligible. Earlier Book 3 trades are labelled **Book-3 pilot evidence**, not head-to-head evidence.
- **Risk normalization:** report both raw account net and return per realized/modelled risk (maximum loss, stress usage, margin/capital days). Rs10k/trade and three slots cap extremes but do not make risk usage equal.
- **Turnover/cost:** show trades, gross, execution costs, AI/data costs and net separately. A high-turnover book can look active while losing to friction.
- **Versioning:** a model/prompt/authority/strategy change starts a new evaluation segment. Do not pool materially different versions without reporting them separately.
- **No cross-book leakage:** §12.3 daily independence is good; also prevent lessons/memory generated from another book's **outcomes** from entering a competing book during a frozen evaluation window.

## 3. Daily forecast questions and option-implied baseline

**Good idea as a secondary diagnostic; current examples/baseline are not ready to freeze. Forecast skill must never substitute for trade profitability.**

### Freeze these exact primary questions
Use non-overlapping-enough, economically interpretable targets tied to the desk horizon:

1. **20-trading-day NIFTY return direction:**  
   `P(NIFTY close in 20 trading days > today's close)`.
2. **20-trading-day large absolute move:**  
   `P(|NIFTY return over next 20 trading days| >= 3%)`.
3. **20-trading-day realized-volatility regime:**  
   `P(next 20 trading-day annualized realized volatility > trailing 20-day realized volatility at forecast time)`.
4. **10-trading-day VIX direction:**  
   `P(India VIX close in 10 trading days > today's VIX close)`.

I would **not** make ±2%, ±3%, ±5% all primary questions: they are nested and highly correlated, creating apparent sample size and multiplicity without much independent information. They can be calibration bins/sensitivity outputs.

### Scoring
- Brier score for all four binary targets.
- Log score only with probabilities clipped to a predeclared interval, e.g. `[0.01, 0.99]`, so one 0/1 forecast does not dominate indefinitely.
- Calibration plot/reliability table and mean predicted probability versus observed frequency.
- Pairwise score differences computed **by forecast date** with uncertainty that respects serial dependence. Daily 20-day targets overlap heavily, so ordinary iid daily confidence intervals are invalid. Use a predeclared moving-block bootstrap (block length at least the longest target horizon, 20 trading days) or HAC/Newey-West-style inference.
- Multiplicity family and adjustment frozen before scoring.

### Baselines
“Option market's own forecast” needs correction. Option prices primarily imply a **risk-neutral distribution**, not automatically the real-world probability of future outcomes; risk premia can make it systematically different from physical probabilities.

Use at least:
1. **market-implied risk-neutral baseline** for NIFTY price events, derived with one frozen method from same-expiry option prices and explicitly labelled risk-neutral;
2. **historical base-rate baseline** computed point-in-time from a frozen rolling window;
3. for VIX direction, historical/base-rate or a simple frozen statistical baseline unless a valid traded-market probability mapping is defined.

Book 1's forecast must also be generated by a frozen, point-in-time method. Do not retrofit “tested conditional frequencies” after seeing forecast outcomes.

**Important:** forecast scores measure probabilistic market-reading/calibration. A book can forecast well and trade badly because structure, payoff, execution and selection differ. §12.5 must state that **paper P&L/risk is the primary trading verdict; forecast scoring is diagnostic and cannot promote an unprofitable book.**

## 4. Is it right that Book 3 may start first?

**YES as a pilot; NO as head-to-head evidence, and not with “only plumbing” as currently written.**

Book 3 can start collecting forward evidence first because historical replay of a contemporary AI is contaminated. That is useful.

But before its **first counted paper decision**, it needs more than plumbing:
- frozen Book-3 constitution/authority: allowed market, holding horizon, defined-risk-only rule, prohibited actions, decision cutoff, data sources and hard C2/C4 limits;
- immutable decision record and strategy/version IDs;
- frozen fill/cost/accounting;
- AI role/prompt/model versions;
- fixed evaluation and forecast protocol;
- no access to future/outcome data;
- red-team/judge policy for Book-3-created strategies/decisions.

Crucially, C4 was designed to verify a proposal against intended monthly contracts/playbook facts. For Book 3, “validity” cannot mean “matches an approved playbook” because it has none. Rewrite C4's Book-3 mode to verify only **hard facts and owner constraints** independently: contracts exist, quotes/input cutoff, payoff/max loss, charges, margin/stress, account limits, allowed market/horizon, no prohibited/naked structure. AI thesis quality remains judge/red-team evidence, not a hard-validity fact.

Book 3's early period is a **pilot cohort**. The formal three-way trade comparison begins at a predeclared common start after all three books can trade. Preserve the pilot results; do not discard them, but do not compare them as if Books 1/2 chose cash.

## 5. Anything missing before rewriting the implementation plan?

**YES. Freeze these design decisions first; otherwise the rewrite will encode ambiguities.**

1. Hybrid authority envelope (above).
2. Two scoreboards: matched decision comparison vs whole-system account competition.
3. Common comparison start and treatment of Book-3 pilot.
4. Exact forecast targets, probability semantics, baselines, scoring, serial-dependence method and multiplicity.
5. Primary verdict hierarchy: net account P&L after execution + operating costs, constrained by risk; forecast score is secondary diagnostic.
6. Book-3 strategy identity/version/change rules.
7. Book-3 constitution and C4 hard-validity mode.
8. Cross-book information firewall, including lessons/outcomes during evaluation windows.
9. AI change policy: model/prompt/role changes start new segments; specify whether emergency provider/model substitution pauses scoring or creates a new version.
10. Hard-loss behavior per book: account brake is common; strategy-level catastrophic/integrity failure can pause that book/strategy immediately. Six-month “no statistical switch-off” must not force continued operation after data/integrity/safety failure.
11. Sample-size language: six months is the **first scheduled review**, not automatically enough evidence. Promotion/combination requires the precommitted uncertainty criterion, not merely elapsed time.
12. Ownership/governance: Book 3 may invent paper strategies, but cannot change owner risk limits, data integrity rules, scoring protocol, its own evaluation criteria, or make anything real-money.

Only after these are settled should the implementation plan/issues be rewritten. Reusing the already-approved A/B/C/D components is preferable to discarding them; create book-specific extensions where behavior truly differs.

# Judge decision on proposed §12

**CHANGES REQUIRED; do not mark §12 agreed yet.**

The three-book idea is worth pursuing because it can answer both a practical question (“which complete system makes better paper results?”) and, with a matched layer, a scientific one (“does AI judgement add value on the same opportunities?”). The present text cannot cleanly answer both yet.

The largest correction is conceptual:

> **Book 3 may have more freedom, but then its whole-system performance must be labelled as such. To claim AI judgement beats rules, compare matched decisions on the same opportunity/strategy universe.**

Once the twelve design points above are folded into §12, I recommend another narrow design review before rewriting the implementation plan and recreating GitHub issues.
