# Epic F: AI layer (on hold until the owner starts it)

Roles: head of desk, all judgement roles, red team, judge. Goal: add each AI role only if it adds net money after its
own cost (design sections 3, 7 and 10 step 4). Nothing here starts before the owner says so. Template and shared
definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## F1. Role agents

**User story:** As the head of desk, I want one AI agent per judgement role producing finding cards independently,
so that each field's expertise reaches the decision without groupthink.

**Background:** Design 3.1 and 3.3: finding cards; independent first reports; "not applicable" when the role has
nothing grounded to say. Historical AI replays are exploratory only (a model may know what happened later).

**Scope.** In: agents for macro economist, market research analyst, positioning analyst, volatility trader
(interpretation), options strategist, F&O trader, behavioural finance, regulation. Out: agents that place orders or
change limits, data or the playbook (never).

**Expected design:** `fno/agents/` with `RoleAgent` interface (`report(day_inputs) -> FindingCard`); prompts versioned
in `agents/prompts/<role>-v<n>.md`; card JSON: `role, observations (each with source and time), interpretation,
implication (measurable), confidence (strong | some | reasoning), counter_evidence, missing_data, not_applicable`;
agents run in parallel and receive only the day's inputs, never other cards; model and prompt version recorded.

**Acceptance criteria:**
1. Each card validates against the schema; an observation without a source is rejected.
2. No agent receives another agent's card before submitting (test on the orchestrator).
3. A role with no applicable input returns `not_applicable` with a reason instead of a forecast.
4. API keys only from the environment; cost of each call recorded (F5).

**Test plan:** schema and orchestration tests with fake model responses.

**Judge verifies:** samples a day's cards and checks sources exist and say what the card claims.

**Depends:** E1 · **Size:** L · **Status:** on hold

---

## F2. Red team

**User story:** As the owner, I want an agent on a different model from the author attacking every thesis, so that
luck, flattering periods and disaster cases are found before money is at risk.

**Background:** Design 7.

**Scope.** In: attacks on research theses and daily proposals. Out: blocking trades (only the judge and risk can).

**Expected design:** `fno/agents/red_team.py`; input: the thesis or decision record; output: objections, each with the
test that would settle it; model differs from the author's (checked).

**Acceptance criteria:**
1. The red team's model is different from the proposer's, or the run fails.
2. Every objection names a test or data check; objections are shown to the judge and recorded.

**Test plan:** orchestration tests with fakes.

**Judge verifies:** confirms objections were answered or recorded as open.

**Depends:** F1 · **Size:** M · **Status:** on hold

---

## F3. AI judge (parts 2 and 3)

**User story:** As the owner, I want research sufficiency and interpretation checked by a model different from the
author, audited monthly, so that the judge itself stays honest.

**Background:** Design 7: three checks (hard validity is code, C4); the judge can block anything; the owner can
overrule judgement checks only, in writing; monthly audit with seeded known-answer cases.

**Scope.** In: sufficiency and interpretation verdicts, audit. Out: hard validity (C4).

**Expected design:** `fno/agents/judge.py`; verdict JSON: `check (sufficiency | interpretation), pass, reasons,
what_to_redo`; audit command sampling approvals, rejections, abstentions and all overrides, plus seeded cases with
known answers.

**Acceptance criteria:**
1. A judge model equal to the author's model is refused.
2. Seeded known-answer cases: false approvals and false rejections counted and reported monthly.
3. Owner overrides are recorded and the affected trades scored separately.

**Test plan:** tests with fake verdicts and seeded cases.

**Judge verifies:** (by the other model) the monthly audit numbers.

**Depends:** C4, F1 · **Size:** M · **Status:** on hold

---

## F4. Role scorecards

**User story:** As the portfolio manager, I want each optional AI role scored by the net money it adds after its own
cost, so that roles that do not earn their keep are removed.

**Background:** Design 3.1: paired shadow decisions with and without the role on the same opportunities; abstentions
count; mandatory control roles are scored on correctness only.

**Scope.** In: shadow comparison, cost, report. Out: removing a role automatically (the owner decides).

**Expected design:** for each optional role, the decision is recomputed without that role's contribution on the same
records; difference in account net result minus the role's API cost, over applicable opportunities, with uncertainty.

**Acceptance criteria:**
1. The comparison uses the same prices and limits as the real decision.
2. The report shows, per role: opportunities where it applied, decisions it changed, net difference, its cost, and
   the uncertainty range.

**Test plan:** tests with constructed records where the answer is known.

**Judge verifies:** recomputes one role's score from the records.

**Depends:** F1, E3 · **Size:** M · **Status:** on hold

---

## F5. Operating-cost tracking

**User story:** As the tax and cost accountant, I want actual AI and data bills fed into the account ledger, so that
the desk's own running cost is counted against its profit.

**Background:** Design 8: three ledgers; each AI role must earn more than it costs.

**Scope.** In: per-call cost recording, monthly bills. Out: budgeting decisions (owner).

**Expected design:** each agent call records model, tokens and cost; monthly totals written to
`accounting/operating_costs.csv`, reconciled with the actual bill.

**Acceptance criteria:**
1. Monthly recorded costs reconcile with the provider's bill within 5%, or the difference is explained.
2. The account ledger (C1) shows the result after these costs.

**Test plan:** unit tests on the aggregation.

**Judge verifies:** checks one month's reconciliation.

**Depends:** C1 · **Size:** S · **Status:** on hold
