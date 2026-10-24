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
`model_served` and `session_id` (AI books, F1), `judge` (C4 result; F4 verdicts and links), `owner_override` (always
null: the owner never overrides a paper decision, DESK_DECISIONS "D4/D5: the five design questions accepted as
recommended" item 4; a non-empty value is refused for every book), `forecasts` (G3 link). Records live under `journal/<book>/decisions/<date>/...` and are
**committed before the execution snapshot** (E3).

**Acceptance criteria:**
1. Every evaluated opportunity has a record, including no-trade outcomes.
2. Replaying a record's inputs through D2 reproduces its decision exactly, including the rejected alternatives and
   every risk and validity reason.
3. A crash during writing leaves either the complete record or none (test kills the writer mid-way).
4. Records are never edited after writing (a correction is a new record linked to the old one).
5. A record whose commit time is after its day's execution snapshot is marked late and never filled (test).
6. The schema is versioned; every three-book field is present (null only where the book has no such field, e.g.
   `rule_default` for Book 3, and `strategy_id` with its spec hash on Book 3's day record "no_trade", which names no
   strategy) and validated; `owner_override` is null in every book.

**Test plan:** replay test; immutability test.

**Judge verifies:** replays three random records.

**Depends:** D2, E2 · **Size:** M · **Status:** done: judge 80 PASS (round 2 60ebd59), merged f314254 (claims: `reviews/claude/response_81_d3-decision-record.md`)

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
| C4's recorded pass (`fno/desk/recorded_c4.py`) | the collected run's record and its `edited` check | no: it follows the collector |
| D3's timing check (`fno/playbook/decision_timing.py`) | one given run | no, and it has no caller today |

**Ordering fact (strong evidence, read in code):** `DecisionStore.runs` sorts run folders by name, and run IDs are
`<date>-r<n>`, so `-r10` sorts before `-r2`. "First" and "latest" by folder name are therefore wrong from the tenth
run of a day. This story orders runs by their commit time (the commit that added `records.sha256`, E3's own timing
source), then by the run counter as a number, never by the folder name. Decision 61's ancestry order was dropped by
the owner's 15 Oct rule ("keep the design simple"): one runner per book and E5b's one-a-day check make commit time
enough. Known limits: two checkouts with skewed clocks deciding one book on one day could be ordered wrongly (E5b
prevents that second run); a run folder deleted or edited by hand after collection is reported only as "does not
match", with no finer reason (owner's simplicity rule).

**Scope.** In:
- **A correction run:** a run any of whose records has a non-null `corrects`. D3 writes a correction as its own run.
- **E3's collector** takes, for every book, the first committed original run in the shared order, when it is visible at
  the deadline (E3's visibility rule is unchanged) and committed before it. When that first run is late, nothing is
  taken: a run after it in the commit-time order is later still, so it can never replace it. The decisions step also
  records in the run log every correction run it saw for the day, and every other run that it did not take, each with its run
  ID, its commit and, for a correction, the record it corrects and its reason. These are shown, never collected.
- **Book 1's orders, exits and C2's view of the book** read the records of the run that opened each trade, and only
  for trades opened by fills: a chosen trade that never filled, or one in a run never collected, is not in the book
  (judge 125 minor 4). That run is the one E3's decisions
  step collected on the trade's entry day, named in that day's run log. The fill rows' `decision_id` is the record's
  opportunity ID (`fno/books/book1_orders.py:4`), which does not name the run, so the run log is the source. A
  record with the same trade ID in any other run, a correction included, is ignored and reported in one alert at each
  exit review while the trade is open
  ("a later record names trade t1; the trade follows its opening run"). When the entry day's run log is missing,
  names no run, or names a run whose files no longer match its `records.sha256` (checked from the run's own files,
  with no git history, so a scheduled session's shallow clone checks it the same way), the trade has no
  opening run: an alert names why, and nothing falls back to another run, least of all the latest record. Such a
  trade gets no time exit, and E4 holds it; E4's own risk-reducing exits still run for it (design 9): protection
  unverified orders its close, an expired leg goes to settlement, and an exit already ordered goes on. C2's view of
  the book refuses an open trade without terms (an input error, as before), so Book 1 opens nothing new until the
  record is put right.
- **One run order, one function (decision 60):** a single shared function orders a day's runs by commit time (the
  commit that added `records.sha256`), then by the run counter as a number. Runs not yet committed sort after every
  committed run, by counter. It lives beside `DecisionStore` (`fno/playbook/run_order.py`), and every reader that
  orders a day's runs uses it, with no sort of its own: E3's collector, the run log's list of other runs, and S1's
  `first_counted_decision`. Book 1's records need no order at all: they take the opening run by its ID from the run
  log, and list other runs naming a trade by day and counter, for the alert only. S1's code
  (`fno/evaluation/order.py`) is in no freeze: `research/evaluation/` holds no `FREEZE_v*.md` on `main`.
- **Scoreboard B** lists the day's corrections and uncollected runs apart (`uncollected_runs` per book, each with its
  day, run ID, commit and time, and for a correction its `corrections`: what it corrects and why), never in the
  scored results.
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
4b. An uncommitted run is never first counted (it has no commit). `first_counted_decision` gives the same results as
   today. `main` holds no committed decision run yet, so today's
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

**Depends:** D3, E3, S1, S2 · **Size:** S · **Status:** story text PASS (judge 125); built on
`story/d3b-first-timely-decision`, judge pending (response 125)

---

## D4. Book 2's authority envelope

**Repository:** trading

**Description:** As the owner, I want the actions Book 2's AI may take written as a frozen, machine-readable envelope
per playbook version and enforced by code, so that Book 2 tests "does AI judgement add value inside the same tested
strategy" and nothing else.

**Context and why:** Design 12.2 (each action `allowed`, `shadow-only` or `forbidden`, fixed before paper and
versioned with the playbook), 12.4 (C4 checks Book 2 against its envelope), design v2 03 (the owner never overrides
on paper: the only owner action on a book is S1's safety stop), REPLAN slice E. Story text written now (owner, 16 Oct
2026, "D4/D5 text only, no AI cost"); **code waits for slice E's trigger** (a strategy approved to paper, or an idea at
rung 2). Claims and questions: `reviews/claude/response_204_d4-d5-envelopes.md`.

**What exists today (read 16 Oct 2026, response 204):** a playbook version fixes one structure code, a discrete set of
wing widths (`StructureSpec.widths`), one lot count and, as its only machine exit, the time exit (`exit_terms.py`: the
profit, loss and event exits must read "none"). Strikes are set by code from the ATM strike; there is no strike set
and no exit set. C4 fails every Book 2 trade closed today (`WaitsFor("envelope", "D4")`, `fno/checks/wiring.py`).

**Scope.** In: the envelope schema, file, loader and check; C4's Book 2 mode; the envelope's hash as a D6 version
component and a D3 `served` key. Out: the AI that chooses (F5); new playbook format fields (D1).

**Expected design:**
- `playbook/<name>-v<n>.envelope.yaml`, one per playbook version, beside it. Each action of a closed enum
  (`fno/playbook/envelope.py`) has a status `allowed`, `shadow-only` or `forbidden`; an action not listed is
  `forbidden`. Envelope v1's actions and their default statuses (design 12.2, cut to what the playbook format can
  express today; the narrow v1 decided (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "Accept all five")):

  | Action | Default | What it may change |
  |---|---|---|
  | `follow_rule` | allowed | nothing: the rule default (D2) |
  | `choose_strategy` | allowed | which of the day's simultaneously eligible `paper` versions trades (D2's eligible set) |
  | `no_trade` | allowed | veto the rule's trade (a skip, valued 0 on scoreboard A) |
  | `choose_width` | allowed | a width from the version's own `widths` set |
  | `reduce_lots` | allowed | fewer lots than the version's `lots`, at least 1 (never more) |
  | anything else | forbidden | any threshold, feature, structure, strike, expiry, exit or strategy: a new playbook version through the research loop |

- `AuthorityEnvelope.permits(action, rule_default, version) -> Verdict` (allowed, shadow-only or forbidden, with the
  reason). The same function is called by F5 before the record is written and by C4 independently.
- C4: an `EnvelopeMode(ValidityMode)` replaces `WaitsFor("envelope", "D4")` in `fno/checks/wiring.py` (one line in
  the composition root). It runs the playbook mode's checks on the version the trade claims, then `permits`. Its
  proposal gets two fields, `action` and `rule_default` (`ValidityProposal`, C4's file, a judged change).
- **Whose envelope governs (judge 207):** the envelope of the playbook version actually traded governs every action
  of that trade, `choose_strategy` included. Picking version B over the rule default A needs B's envelope to allow
  `choose_strategy`, and B's statuses then apply to B's width and lots. Following the rule default uses A's.
- `shadow-only`: the account takes the rule default; the AI's action is recorded in D3's `chosen_action` with status
  `shadow`. **It is not scored until S3 reads it:** S3's `action_of` reads only `record["decision"]` (the account's
  action, `fno/scoreboard/matched_actions.py`). An S3 reading change (the shadow `chosen_action` as Book 2's action on
  scoreboard A) goes through the orchestrator to S3's builder at slice E. Until then a `shadow-only` action is listed,
  never scored, and scoreboard A scores the account's rule default.
- Each envelope's SHA-256 is a D6 component under the key `trade_envelope:<name>-v<n>`, one per playbook version
  Book 2 may trade, and the same key in D3's `served`. The word "trade" keeps it apart from Hybrid's forecast
  envelope (`fno/ai/envelope.py`). A changed envelope file differs from its registered component, so D6 marks the
  decision unscored, and C4 refuses it (fail closed).

**Acceptance criteria:**
1. Each row of envelope v1 has a test: an allowed action passes; a forbidden one is refused with its reason; an action
   absent from the file is forbidden.
2. A lot increase, a width outside the version's set, another structure, a strike other than the code's and a changed
   threshold are each refused by `permits` and by C4.
3. A `shadow-only` action leaves the account at the rule default and records the shadow action (D3 `chosen_action`
   with status `shadow`); until S3's reading change it is listed as unscored, never scored as the rule default's
   result under the AI's name (test).
4. An envelope file edited after its version was registered is refused: its hash differs from the D6 component (test
   on a temporary repository).
5. C4's Book 2 mode calls the same `permits` and blocks a forbidden action even when F5's own check was skipped
   (test with a fake decider).
6. With no `paper` version eligible, every action except `follow_rule` (which is then no trade) and `no_trade` is
   refused: the envelope can never create a trade the rules did not offer (test).
7. Every Book 2 record has `rule_default`, `chosen_action`, a non-empty `reason` and `authority_check` (the verdict);
   a missing one fails D3's validation (test).
8. With versions A (the rule default) and B both eligible, and envelopes that differ (A allows `choose_width`, B
   forbids it; B allows `choose_strategy`), choosing B with A's width set is refused, and choosing B at its own width
   passes: the traded version's envelope governs (test). Each version's envelope is checked against its own
   `trade_envelope:<name>-v<n>` component.
9. C4 verifies, independently of the decider, that the chosen version was in that day's eligible set (D2), that its
   envelope's hash matches its D6 component and the record's `served` key, and that the action is allowed (review
   130, point 3). Slice-E fixture: A forbids `choose_strategy`, B allows it; B can be chosen only when it is eligible
   that day and registered; an ineligible or unregistered B is refused (test).

**Test plan:** table-driven tests over every action and status; C4 tests with constructed proposals; a temporary git
repository for the hash check.

**Judge verifies:** submits a forbidden action, a lot increase and an edited envelope; all are refused by C4.

**Design requirements, where each goes (quality rule 2):**

| Requirement (source) | In D4 | Or out, with the reason |
|---|---|---|
| Choose among eligible approved strategies (12.2) | `choose_strategy`, criteria 1 and 8 (the traded version's envelope governs) | |
| No trade or veto (12.2) | `no_trade`, criterion 1 | |
| Delay entry the same day until 15:30 (12.2) | | Out: under E3's fixed timetable, a delay past the decision deadline is no trade that day, so it is `no_trade` |
| Strike or width from a pre-approved set (12.2) | width: `choose_width` | Strike: out until D1 gives a version a strike set (today strikes are set by code) |
| Reduce size, never increase (12.2) | `reduce_lots`, criteria 1-2 | |
| Choose or tighten an exit from a pre-approved set; early event exit (12.2) | | Out of v1: the only machine exit is the time exit, and S3 values only it. A later envelope version, after D1 adds an exit set and E4/S3 value it |
| Change any threshold, feature, structure or strategy: forbidden (12.2) | criterion 2 | |
| Rule default and AI action with reason in every record (12.2) | criterion 7 | |
| Fixed before paper, versioned with the playbook (12.2) | criterion 4 (a `trade_envelope:<name>-v<n>` D6 component per version) | |
| A shadow-only action is scored on scoreboard A (12.2) | recorded (criterion 3) | Scoring: out of D4. It needs S3 to read the shadow `chosen_action`, routed to S3's builder at slice E; unscored until then |
| C4 blocks independently (12.4) | criterion 5 | |
| The owner never overrides on paper; only S1's safety stop (design v2 03) | no owner action in the enum | D3 refuses any non-empty `owner_override` for every book (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "Accept all five"): a D3 code item at slice E, its builder settled then, **built before any Book 2 or Book 3 paper decision** (review 130, point 5) |

**Known limits (owner's simplicity rule, 15 Oct 2026):**
- Envelope v1 is narrow (no strike, exit or delay actions) because the playbook format cannot express them yet. Each
  later action is a new envelope version, so its record starts fresh.
- With `lots: 1` (the example version), `reduce_lots` has no effect; it matters only for versions with more lots.
- **What Book 2 measures (ChatGPT review 130, point 1):** with one approved strategy at one lot, the AI's only real
  interventions are vetoes and width choices. Results are labelled **"AI veto and width selection within the same
  registered playbook"**, never "AI judgement adds value" in general. Reports show the veto rate and the width
  changes, with the rule default as the paired control (scoreboard A). A zero difference is "inconclusive", not proof
  that the AI adds nothing.

**Depends:** D1, D2, D3, D6, C4 (with C4's owner's agreement to the `ValidityProposal` fields `action` and
`rule_default`), S3's reading of the shadow `chosen_action` (for scoring shadow-only actions) · **Size:** S · **Status:** story text for the judge (response 204), the owner's five answers in; code waits
for slice E's trigger

---

## D5. Book 3's constitution and strategy registry

**Repository:** trading

**Description:** As the owner, I want Book 3's hard rules frozen before its first counted decision and every strategy
it invents registered with its full specification before its first trade, so that Book 3 can invent strategies
without ever editing a rule after seeing the outcome.

**Context and why:** Design 12.3 (NIFTY options; holding up to 3 weeks; defined-risk structures only; decision with
the common cutoff; allowed sources listed; every trade's `strategy_id` registered with its spec and hash before its
first trade; a material change is a new `strategy_id`; Book 3 never changes risk limits, data-integrity rules, the
scoring protocol, its own evaluation criteria, or touches real money; red team and judge are evidence, not blocks),
12.4 (C4 checks Book 3 only against hard facts and owner constraints), F6 (registration precedes the first trade by at
least one session), design v2 03 (no owner override on paper; only S1's safety stop). Story text now, code at slice
E's trigger (as D4).

**What exists today:** C4 fails every Book 3 trade closed (`WaitsFor("constitution", "D5")`); `BOOK3_FOLDER = "book3"`
is reserved (`fno/constants.py`) and empty; C4 already refuses any trade whose maximum loss is not fixed at entry,
including a naked short leg (`validity_money.py`, `bounded_loss`); D3 has no constitution field, but `served` takes
any named component; D6 compares served components with the registered version.

**Scope.** In: the constitution file and its loader; the strategy registry, its registration and its check; C4's
Book 3 mode. Out: the AI that invents and decides (F6); matched shadows (F7).

**Expected design:**
- **Constitution** `book3/constitution-v<n>.yaml`, committed before Book 3's first counted decision and hashed as a D6
  component (`components["constitution"]`) and a D3 `served` key. Allowed keys only:
  - `underlying: NIFTY`; `expiry: monthly` (the only expiry the 3 pm recorder, E4 and S3 can price; decided (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "Accept all five"));
  - `structures`: all nine defined-risk codes C4 accepts (LC, LP, CDS, CCS, PDS, PCS, SF, SC, BF), decided (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "Accept all five");
    STR1's activation gates apply as for every book;
  - `max_holding_days: 21` (calendar days from entry to the planned exit; design's "up to 3 weeks"; decided (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`: "Accept all five"));
  - `sources`: the common and Book 3's private pack only (F1's isolation already enforces it);
  - `risk: risk.profiles.books` and `scoring: research/evaluation/PROTOCOL.md`: references, never numbers. Book 3 can
    change neither, because they are not in its file.
  A key outside this list is refused at load.
- **Strategy spec** `book3/strategies/<strategy_id>.yaml` in **the playbook format (D1)**, parsed by D1's schema, with
  its `parameters_sha256` as `spec_sha256` (no second format).
- **Registry** `book3/strategies/registry.csv`, append-only: `strategy_id, spec_sha256, proposed_on,
  registered_in_commit, model, prompt_version, role_set_version, new_or_reused, supersedes`.
  `fno/book3/registry.py`: `register(spec)` validates the spec against the constitution and appends a row;
  `require_registered(strategy_id, decision_day, decision_commit)` checks that the registration commit is a strict
  ancestor of the decision commit (D6's `_registered_before`, reused) and was proposed on an earlier session than the
  decision day (F6: no same-day invent-and-trade), and that the spec file's hash still matches. `register()` sets
  `proposed_on` itself, from the clock on the registration day (IST), and never takes it from the AI's spec
  (judge 207).
- C4: a `ConstitutionMode(ValidityMode)` replaces `WaitsFor("constitution", "D5")`: `require_registered`, the
  constitution's structure, expiry and holding checks, and the playbook mode's structure, width, lots and shape checks
  against the registered spec. C2's risk limits apply unchanged (Book 3 uses `risk.profiles.books`, as Books 1-2).
- A material change (any field in `parameters_sha256`) is a new `strategy_id` with `supersedes` naming the old one.
- **Many near-identical strategies (ChatGPT review 130, point 2):** every registered strategy also enters the strategy
  factory's G0-G6 trial ledger and its research-question family (design v2 3.1: membership is cumulative, so a
  variant stopped later still counts). Book 3 may choose among its registered strategies for paper, but **a
  confirmatory claim belongs only to a frozen selection policy registered as a version**, never to the survivor of
  many variants. There is no registration cap and no waiting period: both would be easy to game.

**Acceptance criteria:**
1. A decision with a `strategy_id` registered in a commit that is not a strict ancestor of the decision commit, or
   proposed on the decision's own session, is refused (temporary git repository). A spec that carries its own earlier
   `proposed_on` gets the registration day instead (test).
2. A spec file edited after registration is refused (hash).
3. A spec with a structure outside the constitution's list, a naked short leg, a non-NIFTY underlying, a weekly expiry
   or a planned exit over 21 days after entry is refused at registration, and again by C4.
4. Every Book 3 record names the constitution's hash in `served`; a changed constitution file differs from the D6
   component, so the decision is unscored and C4 refuses it (test).
5. Registry rows are never edited or removed (test against git history).
6. A constitution with a key outside the allowed list, or with a risk or scoring number in place of the reference, is
   refused at load (test).
7. Red-team and judge objections never block a Book 3 trade; C2 and C4 do (test with a fake objection).
8. Slice-E test: two variants registered on an earlier session, one chosen after the day's market data, never yield a
   single-trial confirmatory pass: both count in the question's trial family, and only a registered selection policy
   can make the claim (review 130, point 2).

**Test plan:** registry tests on a temporary git repository; spec and constitution validation tests; C4 tests with
constructed proposals.

**Judge verifies:** registers a strategy, edits its spec, and confirms the next decision is refused; registers one and
trades it the same session, and confirms that is refused.

**Design requirements, where each goes (quality rule 2):**

| Requirement (source) | In D5 | Or out, with the reason |
|---|---|---|
| NIFTY options (12.3) | constitution `underlying`, criterion 3 | |
| Holding up to 3 weeks (12.3) | `max_holding_days`, criterion 3 | |
| Defined-risk only, no naked short (12.3) | constitution `structures` and C4's bounded loss, criterion 3 | |
| Decision at about 15:00 with the common cutoff (12.3) | | Already E3's timetable for every book: nothing new here |
| Allowed data sources listed (12.3) | `sources` | Enforcement is F1's session isolation |
| `strategy_id` with full spec and hash before its first trade, with proposer versions, new or reused (12.3) | registry, criteria 1-2 | |
| A material change is a new `strategy_id` (12.3) | `supersedes`, criterion 2 | |
| Never changes risk limits, data rules, scoring, its own criteria (12.3) | references only, criterion 6 | Data rules: C3 applies to every book unchanged |
| Never touches real money (12.3) | | Nothing in the repository places orders |
| Red team and judge are evidence, not blocks (12.3) | criterion 7 | |
| No same-day invent-and-trade (F6) | criterion 1 | |
| The owner never overrides on paper; only S1's safety stop (design v2 03) | no owner action anywhere in D5 | D3's refusal of `owner_override`: as in D4 |

**Known limits (owner's simplicity rule, 15 Oct 2026):**
- Monthly NIFTY expiries only, because nothing else is recorded or priced; weekly options come with a new
  constitution version once A4/E4 record and price them.
- Exits are the playbook format's time exit only (as D4), so every Book 3 strategy holds to its planned exit.
- **What Book 3's results cover (review 130, point 4):** labelled **"monthly NIFTY defined-risk strategies with planned
  time exits of at most 21 days"**. Weekly expiries, faster reactions, stops and other underlyings are untested; a
  wider universe is a new constitution version, with its data.

**Depends:** D1, D3, D6, C2, C4 (with C4's owner's agreement to the `ValidityProposal` field `strategy_id`), B4/D6 (git
ancestry) · **Size:** M · **Status:** story text for the judge (response
204), the owner's five answers in; code waits for slice E's trigger

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

**Depends:** D3 · **Size:** S · **Status:** done: judge 78 PASS (round 2 e239ba1), merged c12137e (D3's record supplies `DecisionFacts`) (claims: `reviews/claude/response_76_d6-version-registry.md`)
