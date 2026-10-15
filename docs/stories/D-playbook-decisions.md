# Epic D: playbook and decisions

Roles: portfolio manager (owner), options strategist, head of desk. Goal: the desk trades only tested strategies,
decides consistently, and records every decision so it can be reproduced (design sections 4, 5, 12.2, 12.3, 12.6
and 13.1 item 3). Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## D1. Playbook format

**Repository:** trading

**Description:** As the portfolio manager, I want each approved strategy written as a versioned file with its payer,
rules, limits, evaluation plan and evidence, so that the desk trades only what was tested and any change is visible.

**Context and why:** Design section 5. A changed parameter is a new version and goes through research again.

**Scope.** In: schema, loader, validation, versioning, status changes. Out: deciding which strategy is approved (B5
and the owner).

**Expected design:** `playbook/<name>-v<n>.yaml`; `fno/playbook/schema.py` and `loader.py`. Fields: `name, version,
status (research | paper | paused | retired), payer, edge_family, structure (code, strikes rule, width rule),
entry_conditions (feature, operator, threshold), size_rule, funding (margin per lot, source, date), exits (time,
profit, loss, event), evaluation_plan (expected range, unit, review dates, pause rules, and since E6 the machine-checked `catastrophic_loss_rs`), evidence (test results path
and commit, red-team note, judge verdict, owner approval date)`.

**Acceptance criteria:**
1. A file missing any field, or with an unknown feature or structure code, is rejected with the field named.
2. Two files with the same name and version are rejected; a changed parameter in an existing version is detected
   and rejected: approved versions and their SHA-256 are recorded in an append-only registry
   `playbook/registry.csv` (`name, version, sha256, status, changed_on, approved_by, evidence_commit`), whose past
   rows are never edited (a test compares it with git history).
3. Allowed status changes only: research -> paper (needs evidence and owner approval), paper -> paused (automatic on a
   hard-loss rule or owner), paused -> paper (owner approval only), any -> retired (owner). Each change is a new
   registry row.
4. A strategy cannot have status `paper` unless all evidence fields are filled and the owner approval date is set.
5. A worked example file (clearly marked `status: research`, not a passed strategy) loads without errors; no example
   claims a passed strategy unless one actually passed.
6. A strategy cannot reach `paper` unless every live feature it uses passed the B7 validation (gate checked by the
   loader).

**Test plan:** schema unit tests with valid and invalid files.

**Judge verifies:** edits a parameter in a committed version and confirms the loader refuses it.

**Depends:** B5, B7 · **Size:** M · **Status:** done (judge 67 with addenda 1-2 PASS; claims `reviews/claude/response_70_d1-playbook-format.md`). Follow-up for E6: auto-pause only a drifting approved version (paper → paused, one #fno-desk line) instead of refusing the whole playbook load

---

## D2. Rule evaluation and allocation

**Repository:** trading

**Description:** As the portfolio manager, I want the day's approved rules evaluated on measured inputs and a fixed
allocation rule to choose when several fire, so that daily decisions are consistent and comparable with no trade.

**Context and why:** Design sections 3.2 and 4: the rule, not a model, chooses strikes and size; allocation is a fixed
rule first; an unproven strategy holds at most 1 of 3 slots.

**Scope.** In: firing rules, ranking, slot limits, the no-trade option; the same evaluation is **Book 1's decision**
and **Book 2's rule default** (12.2: every Book-2 record holds the rule's default action). Out: AI selection (F5).

**Expected design:** `fno/playbook/evaluate.py`: for each strategy `paper` at the start of the decision day and not stopped since (amended 14 Oct 2026, orchestrator and judge 74: an approval counts from the next session, as in E2's common opportunity set; a pause or retirement stops new entries at once), compute its **15:00 live features** (the
validated live versions of B7, never the close-only research features) on today's snapshot; fire when all conditions hold;
build the structure on live quotes; run C2 checks; rank surviving candidates by score = (frozen expected net per
opportunity from the strategy's challenge results, recorded in its playbook file) / (maximum loss including costs);
maximum loss is always positive for these structures (amended 14 Oct 2026, judge 69, orchestrator's sign-off: a width whose entry prices put the position at or beyond its payoff bounds, a trade that cannot lose or cannot win, is skipped as bad prices and the next width is tried, exactly as the research did). A candidate
needs expected net above a no-trade threshold of Rs 0 after costs. Ties: lower maximum loss first, then earlier
expiry, then strategy name. Candidates compete for slots and cash/margin in rank order; each takes its margin from
available cash before the next is considered. The unproven limit is **per strategy**: a strategy with fewer than 20
completed paper trades may hold at most 1 open trade; the 3-slot limit is shared by all strategies.

**Acceptance criteria:**
1. Given all conditions true except one, the rule does not fire and the unmet condition is recorded.
2. Given two fired candidates and one free slot, the higher expected net per rupee of risk is chosen and the other is
   recorded as "not chosen: slot".
3. Given a candidate with negative expected net after costs, no trade is chosen.
4. Given an unproven strategy with one open trade, a second trade of it is refused.

**Test plan:** unit tests with fixed features and quotes.

**Judge verifies:** re-runs one day's evaluation from its decision record and gets the same choice.

**Depends:** D1, C2, B7 · **Size:** M · **Status:** done (judge 69 with addendum 1 PASS; merged 662784f; claims `reviews/claude/response_72_d2-rule-evaluation.md`)

---

## D3. Decision record

**Repository:** trading

**Description:** As the head of desk, I want one stored record per opportunity (what was seen, expected, decided and
why), so that every decision can be reproduced, reviewed and learned from.

**Context and why:** Design section 5 (decision record), 12.6 (every decision with its reasons committed to git
before any fill or outcome exists), 13.1 item 3 (input hashes and availability times, rule default, chosen action,
reasons, judge result, owner override) and 13.5 (both pack hashes, the model actually served). One record format for
all three books keeps scoreboards A and B comparable.

**Scope.** In: record format, storage, replay. Out: AI role cards (F1 adds them later).

**Expected design:** `journal/decisions/<date>/<run_id>/<opportunity_id>.json` written by
`fno/playbook/decision_record.py` atomically (write to a temporary file, then rename). `run_id` = date plus a counter;
`opportunity_id` = strategy, expiry and run; a second run on the same day with the same inputs is detected and
refused (idempotent). Header: `schema_version`, `run_id`, `opportunity_id`, SHA-256 of the code version (git commit),
`config.yaml`, the strategy file and every input snapshot. Body:
`inputs` (each value with source and availability time, plus snapshot file hashes), `features`, `rule_result`,
`structure` (legs, prices, width, size), `expected` (tested P&L distribution summary: mean, 10th and 90th percentile,
worst), `risk` (C2 verdicts with numbers), `validity` (C4 result), `decision` (trade or no trade and reason),
`alternatives` (no trade, other candidates). **Three-book fields:** `book` (`book1_rules | book2_hybrid |
book3_ai`), `version_id` (D6), `common_pack_sha256` and `private_pack_sha256` (E2), `rule_default` (Book 2: D2's
action), `chosen_action` with `reason`, `authority_check` (Book 2: D4), `strategy_id` and its spec hash (Book 3: D5),
`model_served` and `session_id` (AI books, F1), `judge` (C4 result; F4 verdicts and links), `owner_override` (link to
a written override, F4), `forecasts` (G3 link). Records live under `journal/<book>/decisions/<date>/...` and are
**committed before the execution snapshot** (E3).

**Acceptance criteria:**
1. Every evaluated opportunity has a record, including no-trade outcomes.
2. Replaying a record's inputs through D2 reproduces its decision exactly, including the rejected alternatives and
   every risk and validity reason.
3. A crash during writing leaves either the complete record or none (test kills the writer mid-way).
4. Records are never edited after writing (a correction is a new record linked to the old one).
5. A record whose commit time is after its day's execution snapshot is marked late and never filled (test).
6. The schema is versioned; every three-book field is present (null only where the book has no such field, e.g.
   `rule_default` for Book 3) and validated.

**Test plan:** replay test; immutability test.

**Judge verifies:** replays three random records.

**Depends:** D2, E2 · **Size:** M · **Status:** built on branch `story/d3-decision-record`; awaiting judge (claims: `reviews/claude/response_81_d3-decision-record.md`)

---

## D3b. A book's timely decision is its first original run; corrections are shown apart

**Repository:** trading

**Description:** As the portfolio manager, I want each book's decision for a day to be its first original run
committed before the deadline, and every correction to be recorded and shown with its reason but never traded or
scored as the decision. That way no later run, whether a rerun with fresher data, a second checkout or a correction,
can replace what the book decided in time (a look-ahead hole).

**Context and why:** Orchestrator decisions 58, 59 (b) and 60, from story E5b and judge 123. D3 allows a correction as a
new run linked to the record it corrects (D3 criterion 4; the `corrects` field, `fno/playbook/decision_record.py:93`,
None today: no correction writer exists yet). E3's collector, `D3CommittedDecisions.committed`
(`fno/desk/committed_decisions.py:36-41`), walks the day's runs from the last and takes the first one committed
before the deadline, that is, the **latest** timely run. So a correction or a second run committed before the deadline
becomes the day's decision. E5b prevents Book 1 from writing a second run (the prevention); this story is the
guarantee for every book, whatever writes the run.

**What reads the collector and the runs, and whether it depends on "latest" (checked in code on `main`):**

| Reader | What it reads | Depends on "latest"? |
|---|---|---|
| E3's decisions step (`fno/desk/daily_steps.py:97`) | `committed(book, day, deadline)`, written to the day's run log | **yes**: this is the rule changed here |
| E3's fills (`fno/desk/daily_run.py:57`, `daily_steps.fill`) | the run ID and commit recorded in the run log (`recorded`) | no: they read what the decisions step recorded |
| Scoreboard B (`fno/scoreboard/committed_runs.py` `runs`, `entry_decisions.py`, `sources.input_hashes`) | the run log's recorded run per book and day | no, but it inherits the collector's choice |
| S1's first counted decision (`fno/evaluation/order.py` `first_counted_decision`) | the earliest committed run of the first counted day | no: it already takes the first. It sorts run folders by name (see the ordering fact below) |
| Book 1's orders and exits (`fno/books/book1_records.py` `decided_trades`, `recorded_terms`, `decided_exit_days`) | **every** run's records, keyed by trade ID | **yes, by accident**: a later run's record with the same trade ID replaces the earlier one in the dict. So a correction would change a live trade's terms and time exit |
| The daily trade card (`fno/cards/`) | no decision run (it points to "the desk's decision records") | no |
| The packs (`fno/desk/pack*.py`) | no decision run | no |

**Ordering fact (strong evidence, read in code):** `DecisionStore.runs` sorts run folders by name, and run IDs are
`<date>-r<n>`, so `-r10` sorts before `-r2`. "First" and "latest" by folder name are therefore wrong from the tenth run
of a day. This story orders runs by their commit time (the commit that added `records.sha256`, E3's own timing
source), with the run counter as a number to break a tie, never by folder name.

**Scope.** In:
- **A correction run:** a run any of whose records has a non-null `corrects`. D3 writes a correction as its own run.
- **E3's collector** takes, for every book, the first non-correction run whose commit time is before the deadline
  and which is visible at the deadline (E3's existing visibility rule is unchanged). The decisions step also records
  in the run log every correction run it saw for the day, and every other run that it did not take, each with its run
  ID, its commit and, for a correction, the record it corrects and its reason. These are shown, never collected.
- **Book 1's orders and exits** read the records of the run that opened the trade. That run is the one E3's decisions
  step collected on the trade's entry day, named in that day's run log. The fill rows' `decision_id` is the record's
  opportunity ID (`fno/books/book1_orders.py:4`), which does not name the run, so the run log is the source. A
  record with the same trade ID in any other run, a correction included, is ignored and reported once as an alert
  ("a later record names trade t1; the trade follows its opening run").
- **One run order, one function (decision 60):** a single shared function orders a day's runs by commit time (the
  commit that added `records.sha256`), then by the run counter as a number. Runs not yet committed sort after every
  committed run, by counter. It lives beside `DecisionStore`, and all four callers use it, with no sort of their own:
  E3's collector, the run log's collected and listed runs, Book 1's records (`book1_records`) and S1's
  `first_counted_decision` (`fno/evaluation/order.py`; it is in no freeze, since `research/evaluation/` holds no
  `FREEZE_v*.md` on `main`).
- **Scoreboard B** lists the day's corrections and uncollected runs apart (a `corrections` list per book and day:
  run ID, corrects, reason), never in the scored results.
Out:
- writing corrections (no correction writer exists; D3's format stays);
- E5b's prevention (Book 1 never writes a second run).

**Acceptance criteria:**
1. With two original runs both committed before the deadline, the collector takes the earlier one by commit time, for
   each of three books (test).
2. A correction run committed before the deadline is never collected. The original run is collected, and the run log
   lists the correction with its run ID, commit, the record it corrects and its reason (test).
3. A day with only a correction run (its original late or missing) has no timely decision, and the book is late as
   today (test).
4. Runs `-r2` and `-r10` are ordered by commit time, then by counter as a number, never by name. There is one test
   per caller (the collector, the run log, `book1_records` and `first_counted_decision`), each with ten runs. Only
   the shared function sorts (a test fails if another caller sorts run folders itself).
4b. `first_counted_decision` gives the same results as today. `main` holds no committed decision run yet, so today's
   data is empty; a fixture with runs r1 to r9 on several days gives the same first counted decision under the old
   name order and the new order (test).
5. A later run or correction record naming an open trade's ID never changes that trade's terms or time exit. It is
   alerted once (test).
6. Scoreboard B shows corrections and uncollected runs apart, and its scored numbers are unchanged by them (test).
7. Every existing E3, S2 and Book 1 test still passes unchanged, apart from the tests that assert the "latest timely
   run" rule. Those are named in the claims with why each must change (e.g. `tests/timetable/test_parts.py:113`,
   which expects r2 over r1).

**Test plan:** unit tests on the collector with a fake commit source; a Book 1 replay with a planted correction; a
scoreboard B fixture with a correction day; broken-code proofs per criterion. No network, no Slack.

**Judge verifies:** plants a correction before the deadline, a second original run, a ten-run day for each caller, a
caller with its own sort, and a correction naming an open trade; checks each reader in the table.

**Quality rule 9:** it decides which decision trades, so after the judge's code PASS it goes to ChatGPT before the
merge.

**Depends:** D3, E3, S1, S2 · **Size:** S · **Status:** story text on `story/d3b-first-timely-decision`, for the judge's
story check (response 125)

---

## D4. Book 2's authority envelope

**Repository:** trading

**Description:** As the owner, I want the actions Book 2's AI may take written as a frozen, machine-readable envelope
per playbook version and enforced by code, so that Book 2 tests "does AI judgement add value inside the same tested
strategy" and nothing else.

**Context and why:** Design 12.2: each action is `allowed`, `shadow-only` or `forbidden`, fixed before paper starts
and versioned with the playbook. Defaults: choose among simultaneously eligible approved strategies (allowed); no trade
or veto (allowed); delay entry the same day until 15:30 (allowed, but see E3: a delay after the decision deadline means
no trade that day under the fixed timetable); choose strike or width from the playbook's pre-approved discrete set
(allowed); reduce size, never increase (allowed); choose or tighten an exit from the pre-approved exit set (allowed);
early event or news exit (allowed, recorded with evidence); change any threshold, feature, structure or strategy
(forbidden). Every Book-2 record holds the rule default and the AI action with its reason (D3).

**Scope.** In: envelope schema, file, loader, enforcement, versioning. Out: the AI that chooses (F5).

**Expected design:** `playbook/<name>-v<n>.envelope.yaml` beside the playbook file, hashed into `playbook/registry.csv`
(D1); `fno/playbook/envelope.py` with `AuthorityEnvelope.permits(action, rule_default, playbook) -> Verdict`. Actions
are a closed enum. An action `shadow-only` is recorded as a shadow decision (scored on scoreboard A) but the account
takes the rule default.

**Acceptance criteria:**
1. Each default row of 12.2 has a test: allowed actions pass, forbidden ones are refused with the reason.
2. A size increase, a strike outside the pre-approved set and a new threshold are refused.
3. A `shadow-only` action leaves the real decision at the rule default and records the shadow action.
4. Changing an envelope file after its version was registered is detected and refused (hash in the registry).
5. C4 (playbook mode) calls the same `permits` and blocks a forbidden action independently.

**Test plan:** table-driven tests over every action and status.

**Judge verifies:** submits a forbidden action and an edited envelope; both are refused.

**Depends:** D1 · **Size:** S · **Status:** later

---

## D5. Book 3's constitution and strategy registry

**Repository:** trading

**Description:** As the owner, I want Book 3's hard rules frozen before its first counted decision and every strategy
it invents registered with its full specification before its first trade, so that Book 3 can invent strategies
without ever editing a rule after seeing the outcome.

**Context and why:** Design 12.3: NIFTY options; holding up to 3 weeks; defined-risk structures only (no naked
short options); decision at about 15:00 with the common cutoff; allowed data sources listed. Every trade carries a
`strategy_id` whose full specification (entry, structure, size, exits) and hash are recorded before its first trade,
with the date proposed and the model, prompt and role versions that created it, new or reused. A material change
creates a new `strategy_id`. Book 3 may never change the owner's risk limits, data-integrity rules, the scoring
protocol, its own evaluation criteria, or touch real money. Red team and judge objections are recorded evidence, not
hard blocks.

**Scope.** In: constitution file, strategy registry, registration flow, checks used by C4 constitution mode. Out: the
AI that invents and decides (F6).

**Expected design:** `book3/constitution-v<n>.yaml` (market, horizon, structure rules, allowed sources list, limits
reference to C2, the scoring protocol reference S1), committed and hashed before the first counted decision;
`book3/strategies/registry.csv` (append-only: `strategy_id, spec_sha256, proposed_on, registered_in_commit,
model, prompt_version, role_set_version, new_or_reused, supersedes`) and one spec file per strategy
`book3/strategies/<strategy_id>.yaml`; `fno/book3/registry.py` with `register(spec)`, `require_registered(strategy_id,
before=decision_commit)` (git ancestry, like B4).

**Acceptance criteria:**
1. A decision using a `strategy_id` whose registration commit is not an ancestor of the decision commit is refused.
2. A spec file edited after registration is detected (hash) and the strategy is refused.
3. A spec with a naked short option or a horizon over 3 weeks is refused at registration.
4. The constitution's hash is in every Book-3 decision record; a changed constitution starts a new version (D6).
5. Registry rows are never edited (test against git history).

**Test plan:** registry tests on a temporary git repository; spec validation tests.

**Judge verifies:** registers a strategy, edits its spec, and confirms the next decision is refused.

**Depends:** B4 (git-ancestry pattern), C2 · **Size:** M · **Status:** later

---

## D6. Version registry and evaluation segments

**Repository:** trading

**Description:** As the statistician, I want every version of each book (playbook, envelope, constitution, model,
prompts, role set, source contract) registered before its first counted decision, so that results are always scored
per version and no version is declared after seeing its decisions.

**Context and why:** Design 12.6 (a change of model, prompt, role set, authority envelope or strategy starts a new
evaluation segment; an emergency substitution pauses scoring until recorded) and 13.5 (a version is registered and
committed before its first counted decision; an unplanned model fallback that day is "AI unavailable, unscored" and
pauses scoring). The dashboard and scoreboards report each segment separately (12.5).

**Scope.** In: registry, segment computation, scoring-pause state. Out: choosing versions (owner and research loop).

**Expected design:** `journal/versions.csv` (append-only: `book, version_id, starts_on, registered_in_commit,
components (json: playbook hashes, envelope hash, constitution hash, model id, prompt versions, role set, source
contract hash), reason`); `fno/books/versions.py` with `active_version(book, day)`, `segment_of(decision)`,
`scoring_paused(book, day)`. A decision whose served model or any component differs from the active version is
marked `unscored` and pauses scoring for that book until a new version row is committed.

**Acceptance criteria:**
1. A version registered in a commit after a decision cannot be that decision's version (git-ancestry test).
2. A decision with a served model different from the registered one is `unscored`, and later decisions of that book
   stay `unscored` until a new version is registered.
3. Segments are computed deterministically from the registry; scoreboards (S2, S3) group by them.
4. Registry rows are never edited.

**Test plan:** unit tests on a temporary git repository; segment computation tests.

**Judge verifies:** inserts a fallback decision and confirms it is unscored and scoring pauses.

**Depends:** D3 · **Size:** S · **Status:** built on branch `story/d6-version-registry` (D3's record supplies `DecisionFacts`); awaiting judge (claims: `reviews/claude/response_76_d6-version-registry.md`)
