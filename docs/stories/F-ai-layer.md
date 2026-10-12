# Epic F: AI layer for books 2 and 3 (cloud routines)

Roles: head of desk, all judgement roles, red team, judge, statistician, tax and cost accountant. Goal: Book 2 (AI
inside the authority envelope) and Book 3 (fully AI under the constitution) decide every day in isolated cloud
sessions, their AI roles' work is recorded as evidence, and each AI role is kept only if it adds net value after its
cost (design sections 3, 7, 8.1, 10, 12, 13.5, 13.6). Owner decision D4: AI roles run as scheduled Claude Code cloud
sessions; no AI API keys. Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

**Status note:** design section 12 and 13 are approved; the owner decides when books 2 and 3 start (design 12.9: D4
runtime decided; the start date and the owner's recorded monthly plan cost come before the first counted decision).

---

## F1. Isolated AI book sessions

**Repository:** trading

**Description:** As the statistician, I want each AI book to decide in its own cloud session that can see only the
common pack and its own private pack, with the model it actually used recorded and any breach detected, so that the
comparison between books is fair and the firewall is proven, not assumed.

**Context and why:** Design 13.5 step 3: each book decides in its own isolated sub-session with no shared
conversation, cache, memory, temporary files or another book's findings; both pack hashes in every decision. Model
identity: the served model is recorded; a mismatch with the registered version is "AI unavailable, unscored" (D6).
Failure or a usage limit gives "no decision (AI unavailable)". Cloud sessions can be created from a routine with the
`create_session` tool (the stock tool's routines already dispatch sessions this way); a session's served model and
transcript can be read back (`get_session`, `list_events`).

**Scope.** In: creating the per-book session, what it can see, collecting its decision, model identity, breach audit,
failure handling. Out: what the book decides (F5, F6).

**Expected design:** `fno/ai/session_runner.py` used by the daily run (E3): for each AI book, after the packs are
committed (pack commit `P`), create one cloud session on this repository at commit `P` with a **sparse checkout**
limited to `journal/packs/<date>/`, the book's own `journal/<book>/packs/<date>/`, its own versions (`playbook/` for
Book 2, `book3/` for Book 3), the role prompts `agents/prompts/` and the code it needs; the prompt names the book, the
version ID and the allowed paths. The session writes its decision record (D3 schema) and role cards (F2) and pushes
them to the branch `ai/<book>/<date>`. After the deadline, the runner reads that branch, validates the record, reads
the session's served model (`get_session`) and its tool calls (`list_events`), and copies the files into
`journal/<book>/` on `main`. **Breach audit:** any read, fetch or command touching a path or URL outside the allowed
set (including another book's files or this repository's other branches over the network) marks the decision
`firewall breach, unscored` and alerts. Model mismatch: `unscored` per D6. No session, a failed session, a usage limit
or no push before the deadline: "no decision (AI unavailable)".

**Acceptance criteria:**
1. A fake session that reads another book's file is detected from its event log and its decision marked `firewall
   breach, unscored`.
2. A fake session whose served model differs from the registered version gives `unscored` and pauses scoring (D6).
3. A session that pushes after the deadline is ignored; "no decision (late)" is committed (E3).
4. A failed or limited session gives "no decision (AI unavailable)", counted as no trade on scoreboard B and excluded
   from judgement scores on scoreboard A (S2, S3).
5. The session prompt contains no secret; the session has no broker credentials and no order function (test on the
   prompt builder and the environment it requests).
6. Both pack hashes are in the collected decision and match the committed packs.

**Test plan:** unit tests with a fake session API (event logs, served model, branches); one real dry run on a
non-counted day recorded in the conversation log.

**Judge verifies:** reads one real session's event log and confirms the audit result; checks the hashes.

**Depends:** D3, D6, E2, E3 · **Size:** L · **Status:** later

---

## F2. Role agents and finding cards

**Repository:** trading

**Description:** As the head of desk, I want each judgement role in an AI book to produce its finding card
independently before seeing any other card, so that each field's expertise reaches the decision without groupthink
and every claim can be checked.

**Context and why:** Design 3.1 (finding cards: observation with data, source and when it was known; interpretation;
measurable implication; confidence strong / some / reasoning only; counter-evidence; what would prove it wrong; or
"not applicable", never invented numbers), 3.3 (independent findings first), 3.4 (roles), 6 (historical AI replays
are exploratory only). Roles for the AI books: macro economist, market research analyst, positioning analyst
(after A8), volatility trader (interpretation), options strategist, F&O trader, behavioural finance, regulation.

**Scope.** In: role prompts, card schema, independent collection inside a book's session, card validation. Out: the
book's final decision (F5, F6), red team (F3), judge (F4).

**Expected design:** prompts versioned in `agents/prompts/<role>-v<n>.md` (part of the version, D6). Inside the book's
session, each role runs as a separate sub-agent given only the packs and its prompt; cards are written to the book's
branch before the book's decider reads them. Card JSON (schema versioned in `fno/ai/cards.py`): `schema_version,
book, role, decision_cutoff, observations[] (claim, value, source (pack path or URL), source_time, retrieved_at),
interpretation, implication (measurable condition and direction), confidence, counter_evidence[], missing_data[],
not_applicable (bool, reason), prompt_version, input_hashes`. Validation in code after collection.

**Acceptance criteria:**
1. A card with an observation without a source, or a `source_time` after the cutoff, fails validation and is excluded.
2. A card asserting a value for an input listed as missing fails.
3. The collection order proves independence: every card's file is written before the decider's first read of any card
   (from the event log), and no role sub-agent receives another card (test on the orchestration with fakes).
4. A role with nothing applicable returns `not_applicable` with a reason.
5. External sources (if the version allows any) are only those listed in the book's source contract (E2).

**Test plan:** schema tests; orchestration tests with fake sub-agents.

**Judge verifies:** samples a day's cards and checks that sources exist and say what the card claims.

**Depends:** F1 · **Size:** L · **Status:** later

---

## F3. Red team

**Repository:** trading

**Description:** As the owner, I want a red team on a different model from the author attacking every Book-2 and
Book-3 decision and every research thesis, so that luck, flattering periods and disaster cases are found before money
is at risk.

**Context and why:** Design 7 (a different model from the author; attacks every thesis), 12.3 (for Book 3 objections
are recorded evidence, not hard blocks). The red team cannot block a trade; only the judge and risk can.

**Scope.** In: attacks on daily AI decisions (inside the deadline) and on research theses (in the research loop).
Out: blocking (F4, C2, C4).

**Expected design:** `fno/ai/red_team.py`; runs as its own session (F1 pattern) on a model different from the book's
registered author model, reading the book's decision draft and cards; output: objections, each with the test or data
check that would settle it, status `open` or `resolved` (with evidence), the red team's model and the author's model.
Daily objections are committed with the decision; research objections in the research folder.

**Acceptance criteria:**
1. A red team model equal to the author's model makes the run fail and is reported.
2. Every objection names a test or data check; open objections stay visible to the judge, the dashboard and the
   monthly report, never silently dropped.
3. A red team that misses the deadline leaves the decision without objections and records "red team unavailable";
   it never delays the deadline.

**Test plan:** orchestration tests with fakes.

**Judge verifies:** confirms objections were answered or recorded as open.

**Depends:** F1, F2 · **Size:** M · **Status:** later

---

## F4. AI judge (parts 2 and 3), owner overrides and the monthly audit

**Repository:** trading

**Description:** As the owner, I want research sufficiency and interpretation checked by a model different from the
author, my written overrides recorded and scored separately, and the judge itself audited monthly, so that the judge
stays honest and I keep control.

**Context and why:** Design 7: three checks (hard validity is code, C4); the judge can block anything; fail = no
trade or back to the author; only the owner can overrule a judgement (checks 2 or 3), in writing, and overridden
trades are scored separately; no one overrules hard validity; monthly audit of a stratified sample plus seeded
known-answer cases. Per book: Book 2's judge failure means no trade (the account keeps no position; the rule default
is recorded as a shadow); Book 3's judge verdicts are recorded evidence, not blocks (12.3); Book 1's strategies were
judged at approval and its daily trades are checked by C4 only.

**Scope.** In: verdicts for Book-2 and Book-3 decisions inside the deadline and for research theses; the override
record; the audit. Out: hard validity (C4).

**Expected design:** `fno/ai/judge.py` as its own session (different model from the author); verdict JSON `check
(sufficiency | interpretation), pass, reasons, what_to_redo, model`. Overrides: `journal/<book>/owner_overrides.csv`
rows (`date, decision_id, check, reason, entered_by`) committed by the owner; an override can never target a C4 failure
(code refuses). Monthly audit command `python -m fno judge audit <month>`: 20% of approvals, 20% of rejections, 20% of
abstentions (at least 5 of each when available) plus every override, re-checked by the other model against
recalculated evidence; plus 10 seeded known-answer cases. A failed audit (any false approval on a seeded case, or a
false-approval rate above 10%) suspends the AI judge's approvals: Book 2 then takes no new AI-chosen trades until fixed.

**Acceptance criteria:**
1. A judge model equal to the author's model is refused.
2. A Book-2 decision failing the judge opens no trade; the same failure on Book 3 is recorded and does not block.
3. An override of a C4 failure is refused by code; an override of a check-2 or check-3 failure is recorded and the
   trade is tagged so S2 and S3 score it separately.
4. The audit reports false approvals and false rejections on the seeded cases; a failed audit suspends approvals
   (test).
5. A judge missing the deadline counts as a failed check for Book 2 (no trade) and "judge unavailable" for Book 3.

**Test plan:** tests with fake verdicts, overrides and seeded cases.

**Judge verifies:** (by the other model) the monthly audit numbers.

**Depends:** C4, F1, F2 · **Size:** M · **Status:** later

---

## F5. Book 2: AI decisions inside the envelope

**Repository:** trading

**Description:** As the owner, I want Book 2's AI to take, each day, the rule default or one permitted alternative
with its reason, so that scoreboard A can show whether AI judgement adds value within the same tested strategies.

**Context and why:** Design 12.1, 12.2 and 12.9 (Book 2: the actions in its envelope). Book 2 trades only strategies
that passed the historical test (12.11). Every record holds the rule default and the AI action with its reason.

**Scope.** In: Book 2's decider inside its session, use of cards and red-team objections, the envelope check, the
record. Out: changing the envelope (a new version, D4, D6).

**Expected design:** inside Book 2's session (F1): read the packs, the rule default (D2, precomputed by code into the
private pack), the role cards (F2); choose an action from the envelope's allowed set; the decision draft goes to the
red team (F3) and the judge (F4); the final record (D3) holds `rule_default`, `chosen_action`, `reason`,
`authority_check`, card and objection links, judge verdict. Code then runs C2 and C4 (playbook mode, envelope check)
before the deadline.

**Acceptance criteria:**
1. Every Book-2 record has both `rule_default` and `chosen_action` with a reason; a missing reason fails validation.
2. An action outside the envelope is blocked by C4 and the account takes no trade (or the rule default if the
   envelope says so); the attempted action is recorded.
3. `shadow-only` actions are recorded for scoreboard A while the account follows the rule default.
4. With no `paper` strategy, Book 2 records "no approved strategy" daily, like Book 1.

**Test plan:** tests with fake sessions covering each envelope action.

**Judge verifies:** replays three Book-2 records against their envelope and packs.

**Depends:** D2, D4, F1, F2, F3, F4 · **Size:** M · **Status:** later

---

## F6. Book 3: the fully AI system and its pilot

**Repository:** trading

**Description:** As the owner, I want Book 3 to invent its own registered strategies and decide daily under its
constitution, starting as a labelled pilot, so that we learn whether a complete AI system makes more net money under
the same risk budget.

**Context and why:** Design 12.1 (Book 3 answers a whole-system question; a Book-3 win is never claimed as "AI daily
judgement beats rules" unless scoreboard A shows it), 12.3 (constitution, strategy identity), 12.6 (common start;
earlier trades are pilot evidence), 12.11 (Book 3 starts as a pilot once its constitution, decision records, fills
and costs, C2 and C4 Book-3 mode, role agents and the forecast protocol exist). Book 3's strategies cannot be tested
on history (a model knows what happened later).

**Scope.** In: Book 3's decider, strategy proposal and registration flow, pilot labelling. Out: the constitution
itself (D5), matched shadows (F7).

**Expected design:** inside Book 3's session (F1): read the packs and cards; to use a new strategy, write its full
spec, which code registers (D5) **in a commit before the decision commit**; a strategy proposed today can be traded
at the earliest at the next session (registration precedes its first trade by at least one day, so no same-day
invent-and-trade, design 4). Decision record with `strategy_id` and spec hash; C2 and C4 (constitution mode). Every
Book-3 record before the common-start date (S1) is labelled `pilot`.

**Acceptance criteria:**
1. A Book-3 trade with an unregistered or same-day-registered strategy is blocked.
2. A strategy spec breaking the constitution (naked short, horizon over 3 weeks, non-NIFTY) is refused at
   registration.
3. Records before the common start are labelled `pilot` and excluded from head-to-head scoring (S2, S3) but kept and
   reported.
4. Red-team and judge objections are attached as evidence and never block a Book-3 trade; C2 and C4 do block.

**Test plan:** tests with fake sessions: new strategy, reused strategy, refused spec, pilot labelling.

**Judge verifies:** checks registration commits precede first trades for every Book-3 strategy in a month.

**Depends:** C2, C4, D5, D6, F1, F2, F3, F4, G1 · **Size:** L · **Status:** later

---

## F7. Matched shadow decisions for scoreboard A

**Repository:** trading

**Description:** As the statistician, I want Book 3 to commit, every day, a shadow decision on the common opportunity
set, so that all three books appear on scoreboard A, judged on the same opportunities.

**Context and why:** Design 12.5: scoreboard A compares decisions on the same eligible opportunities, same approved
strategy universe, same cutoff, fill model and costs, each committed independently and scored on a standardised
shadow account; books 1 and 2 meet this naturally; Book 3 also commits a matched shadow decision on the common
opportunity set every day. Owner requirement: all three books on both scoreboards.

**Scope.** In: Book 3's shadow decision on each common opportunity (take or skip, and the choice among the approved
strategies' permitted variants), committed with its real decision. Out: scoring (S3).

**Expected design:** the common opportunity set from E2; Book 3's session writes `shadow_decisions.json` (one entry per
opportunity, same action vocabulary as Book 2's envelope, without envelope limits) committed with its real decision
before the deadline; validated by code; missing entries count as "no decision" for scoreboard A.

**Acceptance criteria:**
1. Every common opportunity of the day has a Book-3 shadow entry or a recorded "no decision".
2. Shadow entries committed after the deadline are ignored.
3. Shadow entries never affect Book 3's real account.

**Test plan:** validation tests with fixture opportunity sets.

**Judge verifies:** compares a day's shadow file with that day's common opportunity set.

**Depends:** E2, F6 · **Size:** S · **Status:** later

---

## F8. AI usage and cost attribution

**Repository:** trading

**Description:** As the tax and cost accountant, I want each AI book's and role's usage measured and the owner's plan
cost allocated by a frozen formula, shown apart from any actual cash spend, so that AI costs count against profit
honestly.

**Context and why:** Design 8.1 (three ledgers; each AI role must earn more than it costs), 13.6 (three labelled
figures, never merged: actual cash spend, allocated plan cost "not a bill", incremental value from F9). Cloud routines
draw on the owner's Claude plan, not per-call billing (13.5). C1 already has `accounting/operating_costs.csv`.

**Scope.** In: usage capture per session (duration, sessions, tokens where available), the allocation formula, ledger
entries per book. Out: deciding to keep a role (F9, owner).

**Expected design:** `fno/ai/usage.py` reads each AI session's usage (`get_session`, `list_events`) into
`accounting/ai_usage.csv` (`date, book, role_or_bundle, session_id, model, minutes, tokens_if_available`); the owner
records the monthly plan cost (rupees) in `accounting/operating_costs.csv`; the allocation formula (frozen in S1) splits
it by measured usage; C1's account ledger shows allocated cost per book labelled "allocated, not a bill" and actual
cash spend separately.

**Acceptance criteria:**
1. Allocated costs for a month sum exactly to the recorded plan cost (test).
2. Allocated cost and cash spend are separate fields everywhere (ledger, scoreboards, dashboard).
3. A month without a recorded plan cost is flagged and allocated cost shown as unknown, never zero.

**Test plan:** unit tests on aggregation and allocation.

**Judge verifies:** recomputes one month's allocation.

**Depends:** C1, F1 · **Size:** S · **Status:** later

---

## F9. Role-value evaluation (does each AI role earn its cost?)

**Repository:** trading

**Description:** As the portfolio manager, I want each AI role or role bundle evaluated by a fixed, paired comparison
with and without it, so that a role is kept only if it adds measurable net value after its allocated cost.

**Context and why:** Design 3.1 (paired shadow decisions with and without a role; abstentions count), 10 (roles added
one at a time, kept only if they add net value), 13.6 (ablation where safe; inseparable roles evaluated as a bundle;
keep or drop only at predeclared review dates; control roles scored on prevented invalid actions, not profit).
ChatGPT review 24: allocated cost alone cannot prove value.

**Scope.** In: the ablation schedule, shadow decisions without a role, scoring, the review report. Out: removing a
role automatically (owner decides at a review).

**Expected design:** the evaluation (which roles, which are bundled, a rotation that ablates one role or bundle per day
to bound plan usage, the metric, the uncertainty rule, minimum applicable opportunities) is frozen in the evaluation
protocol (S1) before counting. On an ablation day the book's session also produces a shadow decision with that role's
card withheld (same packs, same deadline); the difference is valued with the E4 fill model on the day's execution
snapshot. Report per role or bundle: applicable opportunities, decisions changed, net difference, allocated cost (F8),
interval. Control roles: caught violations and prevented invalid actions.

**Acceptance criteria:**
1. Ablated shadow decisions use the same packs and snapshot as the real decision (hash test).
2. A role that cannot be separated is reported only as part of its declared bundle.
3. The report reproduces, from the records, a hand computation on a constructed example with a known answer.
4. No keep-or-drop proposal is produced before the predeclared review date or below the minimum sample.

**Test plan:** tests with constructed records.

**Judge verifies:** recomputes one role's score from the records.

**Depends:** F1, F2, F8, S1, E4 · **Size:** M · **Status:** later
