# Epic D: playbook and decisions

Roles: portfolio manager (owner), options strategist, head of desk. Goal: the desk trades only tested strategies,
decides consistently, and records every decision so it can be reproduced (design sections 4 and 5). Template and
shared definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## D1. Playbook format

**User story:** As the portfolio manager, I want each approved strategy written as a versioned file with its payer,
rules, limits, evaluation plan and evidence, so that the desk trades only what was tested and any change is visible.

**Background:** Design section 5. A changed parameter is a new version and goes through research again.

**Scope.** In: schema, loader, validation, versioning, status changes. Out: deciding which strategy is approved (B5
and the owner).

**Expected design:** `playbook/<name>-v<n>.yaml`; `fno/playbook/schema.py` and `loader.py`. Fields: `name, version,
status (research | paper | paused | retired), payer, edge_family, structure (code, strikes rule, width rule),
entry_conditions (feature, operator, threshold), size_rule, funding (margin per lot, source, date), exits (time,
profit, loss, event), evaluation_plan (expected range, unit, review dates, pause rules), evidence (test results path
and commit, red-team note, judge verdict, owner approval date)`.

**Acceptance criteria:**
1. A file missing any field, or with an unknown feature or structure code, is rejected with the field named.
2. Two files with the same name and version are rejected; a changed parameter in an existing version is detected
   (stored hash) and rejected.
3. A strategy cannot have status `paper` unless all evidence fields are filled and the owner approval date is set.
4. A worked example file for experiment 1's best policy (if any passes) loads without errors.

**Test plan:** schema unit tests with valid and invalid files.

**Judge verifies:** edits a parameter in a committed version and confirms the loader refuses it.

**Depends:** B5 · **Size:** M · **Status:** later

---

## D2. Rule evaluation and allocation

**User story:** As the portfolio manager, I want the day's approved rules evaluated on measured inputs and a fixed
allocation rule to choose when several fire, so that daily decisions are consistent and comparable with no trade.

**Background:** Design sections 3.2 and 4: the rule, not a model, chooses strikes and size; allocation is a fixed
rule first; an unproven strategy holds at most 1 of 3 slots.

**Scope.** In: firing rules, ranking, slot limits, the no-trade option. Out: AI selection (later, by comparison).

**Expected design:** `fno/playbook/evaluate.py`: for each `paper` strategy, compute its features (B1) on today's data;
fire when all conditions hold; build the structure (B2 logic on live quotes); rank fired candidates by expected net per
rupee of maximum loss (from the strategy's tested P&L distribution), after C2 checks; open at most the free slots;
strategies with fewer than 20 paper trades limited to one open trade.

**Acceptance criteria:**
1. Given all conditions true except one, the rule does not fire and the unmet condition is recorded.
2. Given two fired candidates and one free slot, the higher expected net per rupee of risk is chosen and the other is
   recorded as "not chosen: slot".
3. Given a candidate with negative expected net after costs, no trade is chosen.
4. Given an unproven strategy with one open trade, a second trade of it is refused.

**Test plan:** unit tests with fixed features and quotes.

**Judge verifies:** re-runs one day's evaluation from its decision record and gets the same choice.

**Depends:** D1, C2, B1 · **Size:** M · **Status:** later

---

## D3. Decision record

**User story:** As the head of desk, I want one stored record per opportunity (what was seen, expected, decided and
why), so that every decision can be reproduced, reviewed and learned from.

**Background:** Design section 5 (decision record).

**Scope.** In: record format, storage, replay. Out: AI role cards (F1 adds them later).

**Expected design:** `journal/decisions/<date>/<strategy>-<n>.json` written by `fno/playbook/decision_record.py`:
`inputs` (each value with source and availability time, plus snapshot file hashes), `features`, `rule_result`,
`structure` (legs, prices, width, size), `expected` (tested P&L distribution summary: mean, 10th and 90th percentile,
worst), `risk` (C2 verdicts with numbers), `validity` (C4 result), `decision` (trade or no trade and reason),
`alternatives` (no trade, other candidates).

**Acceptance criteria:**
1. Every evaluated opportunity has a record, including no-trade outcomes.
2. Replaying a record's inputs through D2 reproduces its decision exactly.
3. Records are never edited after writing (a correction is a new record linked to the old one).

**Test plan:** replay test; immutability test.

**Judge verifies:** replays three random records.

**Depends:** D2 · **Size:** M · **Status:** later
