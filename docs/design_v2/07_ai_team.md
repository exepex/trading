# 7. The AI team, the devil's advocate and weighting by record

## 7.1 What stays (owner decisions)

The three approaches stay as decided on 13 Oct: **Rules** (Book 1, no AI), **Hybrid** (Book 2: the AI team works inside
rule limits) and **AI team** (Book 3: autonomous roles). Screens never name an AI model, nor "Claude". AI runs as cloud
routines fired from GitHub Actions on the owner's subscription (owner decision of 13 Oct 2026, "Architecture: fetch and
reason are separate"). The sealed-same-day forecast rule and its audit conditions (14 Oct) stay.

**Honest starting point:** there is no evidence yet that the AI books forecast better than the baselines; their live
forecasts began on 14 Oct 2026 (G5). Published comparisons of language-model forecasts of market moves are mixed
(some evidence). Every AI role must earn its cost on the record (F9), or it is dropped by the owner.

## 7.2 Roles (one routine prompt per role, versioned in D6's registry)

| Role | Does | Never does | Feeds |
|---|---|---|---|
| Forecasters (Hybrid, AI team) | Daily probabilities and variance forecasts from the sealed pack | See outcomes, other books' answers, `research/forecasts/` | Layer 2 |
| Volatility analyst | Reads the chain, skew, term structure, realised vs implied; writes a finding card | Decide trades | Books 2-3, idea cards |
| Macro and global-cues analyst | Overnight US move, crude, rupee, scheduled events | Same | Books 2-3, weather drivers |
| Positioning analyst | Participant OI (A8), FII/DII (P8) | Same | Books 2-3 |
| Equity research analyst | Results calendar and filings for stock-option ideas (R2) | Same | Factory |
| Portfolio manager (Book 3 only) | Combines findings into a decision inside the owner's limits | Exceed C2's limits (C4 blocks) | Layer 5 |
| Idea generator (head of desk) | Writes idea cards with "who pays" and the cost wall estimate | Run tests, read spent data for a new idea | Layer 4 |
| Devil's advocate | Attacks every call (section 7.3) | Change a registered decision | Layer 6 |
| Post-mortem writer | Turns the week's computed numbers into one page | Add a number not in the records | Layer 8 |

**Code roles, no AI (mandatory controls, never ablated):** data checks (C3), risk manager (C2), cost and tax accountant
(C1), hard validity (C4), the CUSUM and stop-rule meters.

**Keep it small (KISS).** The first AI roles to run are the forecasters (already built), the devil's advocate and the
post-mortem writer. The analyst roles start only with Books 2-3's trading decisions (slice "AI books trade", REPLAN),
because without a decision to feed they have nothing to be scored on.

## 7.3 The devil's advocate

**Purpose.** Every call is attacked before it reaches the owner: every `TRADE` card, every idea passing to registration,
every promotion proposal, every weekly post-mortem.

**Two parts.**
1. **Rule checks (code, can block).** Cost wall at today's quotes; bucket and account caps; event inside the holding
   window when not allowed; stale data; physical settlement; the card's evidence label matching its rung; the idea
   being a variant of a failed one (ledger search). A failure turns the card into `NO TRADE` with the reason.
2. **Objections (AI, cannot block).** In its own sealed session with its own prompt, it reads the card, the strategy's
   registration, the forecaster's calibration in this probability range, the weather and recent results, and returns
   **up to three** objections, each with the effect it predicts ("likely loss larger than modelled because ...").
   There is no quota: "no material objection" is a valid answer. They are printed on the card. The paper trade still
   follows the registered rules: if the advocate could veto, it would be an unregistered filter, and the record would
   no longer test the strategy.

**The advocate is scored too.**
- Each objection is written on the frozen 15:00 pack and recorded, with its independent issuance time (section 4.4),
  **before `decision_finalized_at`** (section 4.1's timing contract); on timeout the record says `advocate_unavailable`.
  An objection written after the outcome could be seen is invalid for scoring.
- An adjudication record says what the card did with it: shown only (always, today), or, in a later registered version,
  acted on.
- Scoring is paired and counterfactual: for each objection, the trade's result is compared with the matched shadow of
  not taking it, so both hits and false alarms count. A registered comparison then asks whether trades with an
  objection did worse than those without. If they did (section 5.5's rules), a new strategy version may use the
  advocate as a filter, tested forward like any idea (a correlation between objections and losses is not causal proof
  that a veto would help; only that forward test is); if not, its objections stay informational and its cost is weighed
  by F9.

## 7.4 Forecasters weighted by proven record: the house forecast

- **Rule, deterministic and frozen before the first house forecast** (proposal; reasoning plus strong evidence for the
  principle). Per question, at each quarterly review:
  1. The passing set is every registered forecaster version whose primary comparison passed section 5.5 (Holm, minimum
     effect, its own minimum sample) on the scored sample up to that review.
  2. Empty set: the house forecast is the primary baseline (5.3). One member: that forecaster. Several: the
     equal-weight mean of their probabilities (for variance questions, of their variance forecasts). Ties need no rule,
     since every member gets the same weight.
  3. On a day a member gives no forecast, the mean of the members that did; none did: the primary baseline.
  4. A member that changes version leaves the set; the new version re-enters only after it passes on its own forward
     record.
  5. The set and the weights hold until the next review; outside a review nothing changes.
- **A review is a change window, not a retune.** After a change, the house forecast's own score is judged on a new
  forward segment that starts at that review, never on the sample that chose it.
- If nothing ever passes, the card shows the baseline and says so.
- **Why not continuously estimated weights:** with small samples, estimated combination weights chase noise, and a
  simple average usually forecasts as well or better (strong evidence: the "forecast combination puzzle", Clemen 1989;
  Smith and Wallis 2009). Estimated weights may be proposed later as a registered version once samples are large.
- **Calibration repair:** a passing forecaster that is miscalibrated (calibration slope clearly not 1) may get a
  recalibration map fitted only on its past scored record, registered as a new version and tested forward.
- **The card always names the house forecaster's record** in the stated probability range ("said 0.6-0.7 on 140 days,
  happened on 64%"), so the owner sees calibration, not confidence.

## 7.5 What any AI role must never do

Place or prepare a real order; read a credential; see an outcome before it is scored; edit or delete a record; change a
rule, threshold or registered version; publish outside #fno-desk; name an AI model on a screen.

## 7.6 Cost and value

- **Allocation:** F8's decided formula (usage share, development shown apart, "allocated, not a bill").
- **Value:** F9's role ablation (S1 items still open; deferred until analyst roles exist).
- **Budget:** the monthly cap and its effect (`08_budget_and_stop_rules.md` section 8.1). When the cap is reached, AI
  roles stop in this order: analysts, idea generator, post-mortem writer (code still produces the numbers), devil's
  advocate objections (its rule checks are code and keep running), AI forecasters last.
