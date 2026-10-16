# Stories F6 and F7: Book 3's decision engine and its matched shadow file (design v2 rewrite)

**Why a file of its own:** `docs/stories/F-ai-layer.md` is 599 lines and its F6/F7 texts predate D4's action
vocabulary and D5's registry. The rewrite needs its interface table and gap lists; one file keeps them reviewable.
The F6 and F7 sections of `F-ai-layer.md` now point here. Builder: session_01KTAQCDjPkDBKwfCMhWphXb, branch
`story/f6-book3-engine`. Claims and questions: `reviews/claude/response_261_f6-f7-book3.md` (number from the orchestrator).

Roles: portfolio manager (Book 3's choice), options strategist (what a spec may say), risk manager (C2 and C4 stay the
only blocks), statistician (trial family, pilot, matched shadows), red team (objections are evidence only), data and
backtesting engineer (replay, timing).

## What exists, read 16 Oct 2026 (strong evidence: the files named)

- **D5** (`story/d5-constitution-code`, judge 263 add. 1 PASS, merges after D4): `fno/book3/constitution.py`
  (constitution file, its hash), `fno/book3/registry.py` (`register(raw_spec, provenance, constitution)` sets
  `proposed_on` from the IST clock and enters the research ledger's `book3_ai strategies` family;
  `require_registered(strategy_id, day, at_commit)`: committed, proposed before the day, spec unchanged, registry never
  edited), `fno/checks/validity_constitution.py` (C4 `ConstitutionMode`: registered spec, constitution, holding days,
  then the playbook mode's structure, width, exact lots and shape checks against the spec).
- **D4** (`story/d4-envelope-code`): `fno/playbook/envelope.py`: the closed actions `follow_rule`, `choose_strategy`,
  `no_trade`, `choose_width`, `reduce_lots`; a choice is `BookTerms(version, width, lots)` or `None` (no trade); the
  actions a choice uses are **derived from its terms against the rule default, never claimed by the decider**.
- **D2/D3:** `RuleEvaluator` (opportunity windows, entry conditions on live 15:00 features, `CandidateBuilder`: the
  structure code sets the strikes, the widest width within the Rs 10,000 cap, valid quotes only), `Allocator` (C2 per
  candidate), `DecisionRun` (records, `inputs.json`, replay, C4 through `validate_chosen`), `decision_timing.timeliness`
  (on time only if committed before the execution snapshot).
- **E2:** the common pack's `opportunities` (`fno/desk/opportunity_set.py`): every (approved `paper` version, expiry)
  of the day plus `no_trade`. Book 3's private pack already reads `journal/book3_ai/` and `book3/`.
- **S2/S3:** the common start and the pilot split are computed from the D3 records of all three books
  (`fno/scoreboard/entry_decisions.py:47`, `book_board.py:56`, `matched_board.py:68`); scoreboard A scores one lot
  per take (`PROTOCOL.md` `scoreboard_a_standardisation`).
- **Missing (CORE_ENGINE_GAP_AUDIT Part D):** the decider, the proposer, F7, the runner (F1t), F2 cards, the O1 step.
- **Not yet true on any branch:** `proposal_of` (C4's adapter) does not set `strategy_id`; D3's `RecordBuilder` takes
  `strategy_id` from the run, not per record, and Book 3's day record has no strategy.

## Division of work (F1t's story `docs/stories/F1t-ai-trading-runner.md`, `story/f1t-ai-trading-runner`; see "Interfaces")

| Part | Owner |
|---|---|
| Fire the routine (pointer: common pack hash, Book 3's private pack), `brief`, `seal`, `reveal`, receipts, judging the book-day (not fired, late, exposed, invalid, model mismatch or unknown, refused, promoted), the outcome record and alert, F1t's run check, the commit before E3's deadline, the O1 steps `ai_fire`/`ai_collect`, live switch, dispatching each book's `OrderBuilder` and `ExitRules` to E4/E8 in `fno/daily/wiring.py` (Book 3's own are F6's, design item 8); `seal` refuses private account figures in any answer text | **F1t** (session_01PLbKH15BXYucP6cT9xtoxK) |
| Book 3's prompt; the answer's schema and checks; registering proposals; Book 3's day sheet; the decision on D2/C2/C4/D3; the shadow file and its reader | **F6/F7** (this story) |
| Constitution, registry, C4 `ConstitutionMode` | D5 (01SFDjjZ), unchanged except the two small edits below |
| Finding cards: the `analyst_cards` export item, card IDs, role-set version | F2 (session_01WSMMv5nK4wDdktFrudJfXv); F1t puts the item in each AI book's export; Book 3 works with none |
| Precomputed D2 output in a book's private pack (Book 2's rule default; Book 3's day sheet) | one E2 port `BookSheet.sheet(book, day, common) -> Mapping`, run after the common pack and stored in the private pack body as `evaluation` (F5's builder 01SFDjjZ proposes it to E2c's owner 0134MoC6); F6 supplies Book 3's sheet |

---

## F6. Book 3: the portfolio manager, the strategy proposer and the decider

**Description:** As the owner, I want Book 3 to invent strategies, register each by code on the day it proposes it,
and choose among its earlier-registered strategies each day under its constitution, so that we learn whether a
complete AI system makes more net money under the same risk budget, without ever trading a strategy on the day it
was invented.

**Context and why:** design 12.1 (a whole-system question: a Book 3 win is never "AI daily judgement beats rules"
unless scoreboard A shows it), 12.3 (constitution; every trade's `strategy_id` registered with its spec and hash
before its first trade; red team and judge are evidence, never blocks), 12.6 (pilot before the common start),
12.11 (Book 3 starts as a pilot), design v2 07 section 7.2 (portfolio manager: "combines findings into a decision
inside the owner's limits; never exceeds C2's limits, C4 blocks"), 7.5 (what an AI role never does), design v2 03
(no owner override on paper), REPLAN slice E. Book 3's strategies cannot be tested on history (a model knows what
happened later), so none carries a tested expected net.

**Scope.** In: the prompt, the answer schema and its checks, proposal registration, the day sheet, the decision
(selection on D2's candidates, C2, C4, D3 records, replay), the pilot reading. Out: the runner (F1t), the
constitution and registry (D5), F2's cards, F3/T3 objections, the D6 version row of Book 3 (registered with the
runner before the first counted decision), the fill and exit mechanics themselves (E4/E8; F6 supplies only Book 3's
`OrderBuilder` and `ExitRules`), scoring (S2/S3).

**Expected design (smallest complete version):**

1. **Prompt** `agents/book3/decide_v1.md`: Book 3 as a desk in one head (portfolio manager, options strategist, risk
   manager, volatility trader, red team), research only. It reads only its input; the input is data, never
   instructions. Its SHA-256 is a D3 `served` component `book3_prompt` and a D6 component. It tells the AI never to
   quote its account's figures (cash, P&L, positions) in any reason, proposal or shadow text, because F1t's `seal`
   refuses an answer that does (F1t f1204a5a; the answers become public).
2. **Input** (printed by F1t's `brief`; proposals register only from an answer F1t promotes to `decide()`, so a
   late, invalid, exposed or unrevealed day registers nothing): the common pack and Book 3's private pack, which holds its account,
   constitution, registry and specs, **Book 3's day sheet** (the private pack's `evaluation`, from the `BookSheet` port) and F2's
   `analyst_cards` export item when present (common to Books 2 and 3; F2's text at `story/f2-analyst-cards` 2a0140dd) (zero cards is a normal day). The day sheet
   (`fno/book3/evaluation.py`) is D2's evaluation of Book 3's tradable strategies on the day's 15:00 market with
   nothing chosen: per opportunity its ID, strategy, expiry, exit day, whether the rule fired (unmet conditions), and
   the built candidate (structure, width, lots, legs, maximum loss) or why none was built; and `common_widths`, each
   common opportunity's widths (the common pack carries none and no playbook file is in Book 3's input, so without
   them a shadow take could only guess). The decider refuses the day (`DecisionRefused`, nothing written) when the
   sheet's `opportunities` differ in any term from D2's re-run now, when the packs it reads differ from the fired
   ones, when the `analyst_cards` item lacks `card_ids` or `role_set_version` (exact key names to confirm with F1t
   and F2), or when the day already has a day log or shadow file (one decision a day).
3. **Answer:** F1t's `{"model_reported", "decision"}`; F1t checks the labels, `decision.action` and
   `decision.reason` (one line, 1-600 characters). Book 3's `decision` (exactly these keys, checked by
   `fno/book3/answer.py`, registered with F1t as Book 3's shape check, so `seal` refuses a bad one before the
   deadline): `action` (`trade` or `no_trade`), `reason`, `trades` (list of `{opportunity_id, reason}`, non-empty
   exactly when `action` is `trade`), `proposals` (list of `{spec, supersedes, reason}`,
   `spec` being the D1 YAML text), `shadow` (F7's entries), `cards_used` (card IDs). Every reason is one line of 1 to
   600 characters. A wrong shape refuses the whole answer at `seal` (F1t: `invalid`, no trade). A trade naming an opportunity that is
   not a built candidate on the day sheet, or named twice, is refused alone and recorded as attempted; the rest of
   the answer stands. A card ID (F2's `<role>/v<n>/<day>`) not in that day's `analyst_cards` item is refused (the answer cannot
   cite evidence it was not given).
4. **Proposals** (`fno/book3/proposals.py`), each on its own:
   - Book 3's guards before D5: `status: research`, every `evidence` field null, `expected_net_per_opportunity:
     none` (nothing tested it), `catastrophic_loss_rs` at most the owner's per-trade cap
     (`risk.profiles.books.max_loss_per_trade_rs`, Rs 10,000), so a spec can never loosen E6's pause; only exits
     code enforces (the time exit, text exits exactly "none"), since Book 1's order replay refuses every order of a
     run whose version states another exit. Text that cannot be read at all (bad YAML, an impossible date, a field D1
     refuses) refuses that proposal only.
   - Then D5's `register()` (constitution check, `proposed_on` from the clock, the trial ledger). Provenance: `model`
     is `AcceptedDecision.registered_model` (F1t refuses a mismatch or `unknown` before the decider runs); `prompt_version` is
     `book3_decide_v1:<sha256 prefix>`; `role_set_version` is the `analyst_cards` item's registered role set (F2: role versions in
     role order joined with `+`, for example `volatility/v1`; `none` only when no role is registered, so a day with
     no valid card still names the set); `supersedes` from the answer. `new_or_reused` is set by code, never by the AI (agreed with D5's owner,
     16 Oct 2026): `reused` when the proposal names `supersedes` or its **rule key** equals a playbook version's;
     otherwise `new`. The rule key is the SHA-256 of what code trades by, from the parsed rule: the structure code,
     widths (as numbers, sorted), lots, the expiry window and time exit, and the entry conditions in any order. Free
     text (strikes and width rules, text exits) is left out, so new wording, spacing or number spelling cannot dodge
     it (self-review finding). D1's `parameters_sha256` covers the name and version too, so a copied rule under a new name
     always has a different `parameters_sha256` and an equality check on it could never fire. A proposal whose rule
     key equals an earlier registered Book 3 spec's is **refused** ("same rule as <id>: trade that one"), so one rule
     never enters the trial family twice under two names. The rule key is one function, `rule_sha256(strategy)`,
     beside `parameters_sha256` in D1's `fno/playbook/schema.py` (no other rule comparison exists today; anything that
     compares rules later uses it). A playbook version re-versioned with the same rule has one rule key, so a Book 3
     spec copying either reads `reused` (agreed with D5's owner).
   - A refused proposal never stops the day: it is listed with its reason in the day's proposal log
     `journal/book3_ai/proposals/<date>.json` (every proposal, registered or refused, write-once), returned in
     `DecidedRun.files` with the registry, spec and ledger and committed with the run (one commit is enough: a day-d
     proposal trades from d+1, when D5 checks ancestry). No cap on proposals (D5: a cap is easy to game; every
     registration is a trial).
5. **Tradable strategies** (`fno/book3/strategies.py`): the registry's specs proposed before the day whose
   `require_registered` passes at the decision base commit. They trade from the session after `proposed_on`, like
   D2's "a same-day approval trades from the next session". A spec proposed today is on no day sheet today.
6. **Decision** (`fno/playbook/selection.py`, shared with F5 for Book 2 if its builder agrees; `fno/book3/decider.py`, `fno/book3/decision_wiring.py`): D2's `RuleEvaluator` over the tradable
   strategies, with a **selection allocator**: the candidates the answer picked go to D2's `Allocator` (C2 and the
   unproven-version limit; the no-trade threshold off, since no Book 3 spec has a tested estimate); every other
   candidate is "not chosen by Book 3". Book 3 has **no daily width or lots choice**: the spec is the strategy
   (widest width within the cap, the spec's lots, C4's exact-lots check), and a different width is a new spec. C4's
   `ConstitutionMode` checks each chosen trade through D3's `validate_chosen`; `DecisionRun` writes the records under
   `journal/book3_ai/decisions/` with `inputs.json` holding the picks too, so `replay` reproduces the decision.
   Records: `strategy_id` and `strategy_spec_sha256` per opportunity record; `chosen_action` "trade" or "no trade";
   `reason` the answer's reason for a pick (else D2's outcome reason); the day record keeps D2's account of what was
   chosen, and the answer's `decision.reason` goes in the day log (`reason`), so D3's replay needs no AI text;
   `served` adds `constitution`, `book3_prompt` and F1t's decision version (`ai_decision_version`, F1t's run check); `rule_default` and `authority_check` null (D3 `NULLABLE`).
7. **Objections and cards are evidence only.** No objection or card is an input of the selection allocator, C2 or C4
   (D5 criterion 7 already proves C4; F6 tests the allocator).
8. **Orders and exits** (`fno/book3/orders.py`; the exits are Book 1's class wired in `fno/book3/decision_wiring.py`
   `build_book3_exit_rules`, no new file; F6 owns both, F1t only dispatches them per
   book in `fno/daily/wiring.py`). `Book3Orders(OrderBuilder)`: for a committed run, builds D2's evaluator with the
   `SelectionAllocator` from the picks stored in the run's `inputs.json` and the specs in the run's own playbook
   snapshot, and hands it to Book 1's `ReplayedOrders` (D3's replay, refused under other code; any difference refuses
   every order with `OrdersRefused`; only records whose committed `chosen_action` is "trade", so a C4 block is never
   ordered). Book 3's exit rules: Book 1's `PlaybookExitRules` over Book 3's store: each open trade exits on
   the time exit fixed at its decision, computed from the spec text as the run read it (`inputs.json`), never from
   today's `book3/strategies/` file; today's file is read only to alert.
9. **Pilot:** no stored label. Book 3's runs are D3 runs in the same store, so S2/S3's common-start rule (read from
   all three books' records) puts every Book 3 decision before the common start in the pilot section. A label stored
   at decision time could be wrong on the common start day itself (the other books may commit after Book 3).

**Interfaces (F1t's port as written in its story; confirmed to F1t, 16 Oct 2026):**

| Interface | Shape | Called by |
|---|---|---|
| `Book3Decider(AiBookDecider).decide(accepted: AcceptedDecision) -> DecidedRun` | writes one D3 run under `journal/book3_ai/decisions/` with C2 and C4 inside; `DecidedRun.files`: registry, specs, ledger, proposal log, F7's shadow file; `DecisionRefused` when no run can be written | F1t's `ai_collect` |
| Book 3's shape check and prompt path | registered with F1t's decision version (one line) | F1t's `seal` and `brief` |
| Book 3's `BookSheet` | D2's evaluation of the tradable strategies, nothing chosen | E2's pack step (above) |
| `proposal_of(...)` (C4's adapter) | sets `strategy_id_of(name, version)` for Book 3 | C4 |
| `RecordBuilder` (D3's file) | Book 3: `strategy_id` and spec hash per opportunity record (F6's edit); null on the day record only (D5 owner's `story/d3-no-owner-override`, b49abdde) | D3 |

Agreed with F1t (its text at e0ba1b43): Book 3's decision version declares its write paths `journal/book3_ai/`,
`book3/` and `research/ledger.csv`. F1t's rule, quoted from its text (c5c73568): "F1t commits only changes under
them. Just before `decide()`, F1t snapshots the bytes of every file under those paths; when the run check fails,
`DecisionRefused` is raised, or the decider raises anything else, it puts every such file back to that snapshot
(changed files rewritten, new files deleted), so nothing half-registered (a `registry.csv` row, a spec file, a ledger
row, a shadow file) can be committed later by accident. The snapshot, not `HEAD`, is the reference:
`research/ledger.csv` is shared with the research factory, and any change made before `decide()` (by anyone) is left
as it was. The daily run is one thread, so nothing else writes these paths during `decide()`." The shape check is `check_decision(decision) -> list[str]` (standard
library only), registered with the prompt `agents/book3/decide_v1.md` in F1t's `DecisionVersion`; `brief` hash-checks
and prints that prompt. `analyst_cards` is in Book 3's pointer, printed by `brief`, and carried in `AcceptedDecision` as fired
(card IDs, `role_set_version`, `input_sha256`; F1t at 0a466db6), which is what the decider checks `cards_used` against.

**Acceptance criteria:**
1. A proposal registered on day d is on no day sheet and no decision on d; it is on d+1's (temporary git
   repository, fixed clock). A strategy that is not registered, registered by a commit that is not an ancestor of the
   decision base, edited after registration or no longer readable is left out of the tradable set before D2 runs
   (listed in the day log's `excluded_strategies` with D5's reason; one damaged spec never stops the others), so a
   pick of it is only an attempt; C4's `ConstitutionMode` refuses it again independently (D5's tests).
2. A proposal whose rule key equals an earlier Book 3 spec's is refused; one equal to a playbook version's, or
   naming `supersedes`, is registered as `reused`; any other as `new` (a copied rule with a new name and new
   descriptive text is still caught).
3. A proposal breaking the constitution (structure outside it, weekly expiry, holding over 21 days), with `status`
   other than `research`, any filled `evidence`, an expected net other than `none`, or `catastrophic_loss_rs` above
   Rs 10,000 (and at Rs 10,000 exactly: accepted) is refused, listed in the proposal log with its reason, and the
   day's decision still runs.
4. The registry row's `model` is `AcceptedDecision.registered_model`, never a value from the `decision` object; the
   `prompt_version` names the prompt file's hash.
5. Every shape refusal (missing or extra key, a reason over 600 characters or with a line break, `action` `trade`
   with no trades or `no_trade` with some, a non-list `trades`) is refused by Book 3's shape check with what to fix;
   the decider raises `DecisionRefused` if a bad shape still reaches it (no run written); a refused pick (not a built candidate, duplicate) leaves the other picks standing and is recorded as
   attempted.
6. A picked candidate refused by C2 (for example the open-risk cap) is not chosen and its risk reasons are recorded;
   C4 blocks independently (fake answer through the real D2, C2 and C4 path).
7. Records: every Book 3 opportunity record passes D3's `validate_record` with `strategy_id`, `strategy_spec_sha256`,
   `served["constitution"]`, `served["book3_prompt"]`, the pick's reason as `reason`; `replay` of the run reports no
   difference, and reports one when `inputs.json`'s picks are changed.
8. With zero cards, zero registered strategies or zero candidates, the day is a valid "no trade" with its reason; a
   cited card that was not given is refused.
9. Objections never block: the same answer with and without a fake objection gives identical records.
10. Pilot: with Book 3 records from a day before every book's first on-time record, S2's common start excludes them
    and they read as pilot (test through `entry_decisions.common_start`).
11. End to end on fixtures: a fake session answer (one proposal, one pick of a strategy registered the day before,
    shadow entries) through `decide` writes the proposal log, the registry row, the D3 run and the shadow file, and
    C4 passes the pick.
12. `SelectionAllocator` (shared with F5): unpicked candidates read "not chosen by <book>" with no risk verdict; a Book
    3 pick with width or lots (no `rebuild`) is refused; with a fake `rebuild`, C2 runs on the rebuilt candidate and a
    rebuild raising `NotBuilt` leaves the pick not chosen with its reason; `attempted` lists every pick that was not a
    built candidate and every failed rebuild; a C2 refusal keeps D2's own reason text unprefixed (`slot:`, `cash:`,
    `risk:`, which S2/S3 match); `threshold` is a constructor argument (Book 2 on, Book 3 off); Book 1's
    `inputs.json` bytes are unchanged (no `selection` key).

13. Day sheet: Book 3's `BookSheet` returns D2's evaluation of the tradable strategies on the same 15:00 live
    features and market D2 reads at the decision (the same `LiveFeatureValues` and `Market` sources), with nothing
    chosen. It is built before the private pack is written and is inside the pack's body, so `private_pack_sha256`
    covers it (test: changing one sheet value changes the hash). A day with no tradable strategy gives an empty sheet.
    A pick not on that day's sheet is refused (criterion 5).
14. Orders: `Book3Orders` orders exactly the committed "trade" records of a run that replays. A run whose stored picks
    or spec snapshot were edited after commit gives `OrdersRefused` and no order. A C4-blocked pick gives no order.
    A "no trade" run gives an empty list.
15. Exits: each open Book 3 trade gets its time exit from the spec as the run read it. Editing today's spec file
    (its time exit included) or deleting it changes no exit. A deleted, unreadable or unenforceable file sends one
    alert; a valid edit sends none, since the exit never reads today's file (Book 1's rule, judge 400). A trade with no
    opening record gets no exit, with an alert.
16. Only promoted answers register: no proposal registers on a late, invalid, exposed or not-revealed day (test
    through F1t's judging with fake answers, once F1t's code exists; until then a decider test proves that
    registration happens only inside `decide()`).

**Test plan:** temporary git repositories for registration and ancestry; fake answers (good, bad shape, each refused
pick, each refused proposal); the real D2/C2/C4 path on a fixture market; replay; boundary cases at Rs 10,000 and 21
days; empty cases (no cards, no strategies, no candidates).

**Judge verifies:** registers a strategy and picks it the same day (refused), the next day (passes C4); edits the spec
(refused); feeds a malformed answer (no decision); compares the registry's `model` with the served one.

**Design requirements, where each goes (quality rule 2):**

| Requirement (source) | In F6 | Or out, with the reason |
|---|---|---|
| Book 3 invents its strategies (12.1, 12.3) | proposals, criteria 2, 3 | |
| Full spec and hash registered before the first trade (12.3) | D5's `register`, criterion 1 | |
| Proposer versions recorded (12.3) | provenance, criterion 4 | |
| No same-day invent-and-trade (12.3, first-plan F6) | criterion 1 | |
| Decision at the common cutoff (12.3) | the day sheet is D2 on the cutoff's market | the timetable is E3/F1t |
| Defined risk, NIFTY monthly, at most 21 days (12.3, D5) | D5 at registration and C4, criterion 3 | |
| Never changes risk limits or scoring (12.3) | `catastrophic_loss_rs` guard, criterion 3 | the rest is D5 (references only) |
| C2 and C4 block; red team and judge never do (12.3, 12.4) | criteria 6, 9 | |
| Portfolio manager combines findings (v2 7.2) | cards in the input, `cards_used`, criterion 8 | the cards themselves: F2 |
| Every Book 3 record before the common start is pilot (12.6) | criterion 10, read by S2/S3 | |
| Same fill model and exits as the other books (12.5, F1t) | Book 3's `OrderBuilder` and `ExitRules`, criteria 14, 15 | fills and exits themselves: E4/E8 |
| Decision on the same 15:00 data as the other books (12.3, 12.5) | the day sheet on D2's own sources, criterion 13 | |
| Only an answer received in time counts (F1, F1t) | registration inside `decide()` only, criterion 16 | the judging: F1t |
| A Book 3 win is not "AI judgement beats rules" (12.1) | | reporting: S2/S3's labels; F7 feeds scoreboard A |
| Model served recorded; a mismatch unscored (F1, D6) | `registered_model`, criterion 4 | the mismatch check: F1t's judging and D6 |
| Late or failed session gives no decision (F1) | shape refusal, criterion 5 | lateness and failure: F1t's judging table |
| The owner never overrides on paper (v2 03) | nothing in F6 reads an override | D3's refusal of `owner_override`: `story/d3-no-owner-override` (D5's owner, b49abdde, waits for judge E), a dependency before Book 3's first paper decision |
| Never names a model on a screen (v2 7.1) | | screens are out (no UI work) |
| A confirmatory claim only for a frozen selection policy (D5, review 130) | every registration is a trial (D5's ledger) | the claim rule: S1/S3 |

**Known limits (simplicity):**
- The spec's descriptive fields (`funding`, `expected_range`, `review_dates`, `pause_rules` text) are the AI's own
  words; no code reads `funding`, and `expected_range` is shown, never scored. The prompt says so and asks for them
  labelled as estimates.
- One width and lot rule per spec: a Book 3 that wants another width registers a new spec (a new trial).
- A strategy trades only on its window's first day for an expiry (D2's opportunity rule), so a spec must be
  registered before its window opens.

**Depends:** D4 and D5 merged, F1t (runner), the `BookSheet` pack port (F5's builder 01SFDjjZ, with E2c's owner
0134MoC6, who edit `fno/desk/packs.py` and `private_pack.py`; F6 supplies only Book 3's sheet), `story/d3-no-owner-override` (Book 3's day record; the `owner_override` refusal, before the first paper decision), E2, D2,
D3, D6, C2, C4 · **Size:** M · **Status:** story text for the judge

### F6 addendum 1: F4's evidence pointers (agreed with F4's builder 01AN94h4, 16 Oct 2026; F4 text `story/f4-ai-judge` 90066e7d)

F4's daily judge is code. For Book 3 its verdict is **evidence only, never a block** (design 12.3): `decide()` runs
whatever the verdict says. **Sequencing:** this addendum's code follows in one change after
`fno/judge/evidence.py` is on `main` (F6's code at e1c715e1 is built without it). Book 3 cannot go live before then:
F1t's live switch is null and slice E's trigger has not happened.
- **Shape:** Book 3's exact keys gain a top-level `evidence`, a list of 0 to 20 `{"pack": "common" | "private",
  "pointer": "<RFC 6901 JSON pointer>"}` with no values. `check_decision` adds
  `fno.judge.evidence.evidence_problems(decision.get("evidence")) -> list[str]` (standard library only; an empty list
  is acceptable; a missing key is passed as None and refused as "evidence must be a list").
- **Prompt lines:** cite a pointer for every number written in any reason; write numbers exactly as in the pack; never
  write a number in words. Account files are not citable: a pointer must reach a scalar, and a whole file's text is
  not one. Day-sheet values (`/evaluation/...`) are citable. A reason may cite a private pointer without writing its
  number, so no account figure is ever quoted (F1t's `seal` refuses one).
- **Record:** D3's existing `judge` field is set from `AcceptedDecision.judge` (the verdict file's path, added by F1t)
  through the run context.
- **Criterion 17 (with that change):** an answer without `evidence`, or with an entry F4's check refuses, is refused
  by the shape check. An accepted answer's records carry `judge` from `AcceptedDecision.judge`. The same answer with a
  pass or a fail verdict gives identical trades.

---

## F7. Book 3's matched shadow decisions for scoreboard A

**Description:** As the statistician, I want Book 3 to commit, every day, a take-or-skip decision on each common
opportunity, so that all three books are judged on scoreboard A on the same opportunities.

**Context and why:** design 12.5 (same opportunities, strategies, cutoff, fill model and costs; Book 3 also commits a
matched shadow decision every day), S1 `scoreboard_a_standardisation` (one lot, E4's fills, the strategy's own exit,
no account limits), D4 (a choice is `BookTerms` or `None`; its action is derived, never claimed).

**Scope.** In: the shadow entries in Book 3's answer, their checks, the shadow file, its reader in scoreboard A's
take-or-skip form, its timing. Out: scoring and S3's reading of the file (S3's builder, slice E); D4's action labels
on scoreboard A (derived by S3 with D4's derivation against the rule default when it reads them).

**Expected design:**
- **Entries:** for each common opportunity of the day (the common pack's `opportunities`, without `no_trade`):
  `{opportunity_id, action: "take" | "no_trade", width, reason}`. A take names a width from that version's own
  `widths` set (given to Book 3 in its day sheet's `common_widths`); no lots (scoreboard A trades one lot). In D4's terms a take is `BookTerms(version, width, 1)` and
  `no_trade` is `None`. There is no envelope: Book 3 may take an opportunity whose rule did not fire.
- **File** `journal/book3_ai/shadow/<date>.json` (`fno/book3/shadow_file.py`), canonical JSON, write-once, with the
  day, the common pack's SHA-256 and one entry per common opportunity. An opportunity the answer left out, an
  unknown ID (dropped), a duplicate, or a take with a width outside the version's set becomes `no_decision` with the
  reason, written by code. Written by Book 3's decider and committed with its run (`DecidedRun.files`), also when C2
  or C4 refuse the real pick (the shadow is independent of the account).
- **Reader** (`fno/book3/shadow_reader.py`): per opportunity `take` (with its `BookTerms`), `skip` or `not observed`
  (S3's `matched_actions` kinds). A file not committed before the day's execution snapshot (`timeliness`, D3's
  rule) reads as all `not observed` ("late"); a missing file is all `not observed` ("no decision").
- **Never the account:** nothing in the fill path reads `journal/book3_ai/shadow/`.

**Acceptance criteria:**
1. Every common opportunity of the day has exactly one entry: the AI's, or `no_decision` with its reason (missing,
   duplicate, width outside the set); an ID not in the common set is dropped and named in the file's `refused` list.
2. A file committed at or after the execution snapshot reads as all `not observed` (late); one committed before it
   reads as written (temporary git repository, times at, just before and just after the snapshot).
3. A shadow take changes nothing in Book 3's real decision: the same answer with and without shadow entries gives
   identical D3 records. When C2 or C4 refuse the real pick, the shadow file is still written as answered.
4. The file names the common pack's hash; a file whose hash differs from the day's committed common pack is refused
   by the reader (all `not observed`).
5. Empty cases: a day whose common set is only `no_trade` gives a file with no entries; a missing file reads as
   all `not observed`.

**Test plan:** fixture common sets (none, one, two versions; widths at the edges of a set); temporary git timing.

**Judge verifies:** compares a fixture day's shadow file with that day's common opportunity set; commits one late.

**Design requirements, where each goes:**

| Requirement (source) | In F7 | Or out, with the reason |
|---|---|---|
| A Book 3 decision on every common opportunity (12.5) | criterion 1 | |
| Same action vocabulary as Book 2, without envelope limits (first-plan F7) | D4's `BookTerms`/`None`, entries | D4's labels: derived by S3 when it reads them, never written by the AI (D4's rule) |
| Committed before the deadline; later ignored (first-plan F7, D3) | criterion 2 | |
| Never affects the real account (first-plan F7) | criterion 3 | |
| Missing entries count as no decision (first-plan F7) | criteria 1, 5 | |
| Scored on a standardised shadow account (12.5, S1) | one lot, no lots field | scoring: S3 |

**Depends:** F6, E2, S3's reading (slice E) · **Size:** S · **Status:** story text for the judge

---

## Open questions

1. **F1t (01PLbKH15): agreed** (above). **F5's builder (01SFDjjZ): agreed** one `SelectionAllocator` (F6 builds it: picks `Pick(opportunity_id, reason,
   width=None, lots=None)`, an optional `rebuild` for Book 2's width and lots, which Book 3 never passes, so a Book 3
   pick with width or lots is refused) and one `BookSheet` port (E2c's owner to agree who edits the pack files). **F2 (01WSMMv5): answered** (above).
2. **D5's owner (01SFDjjZ), answered 16 Oct 2026:** `new_or_reused` derived by code (above; the rule key replaces
   their `parameters_sha256` equality, which cannot fire because the hash covers the name). `proposal_of` sets
   `strategy_id` through one helper `strategy_id_of(name, version)` added to `fno/book3/registry.py` and used by
   `register` too (their agreement; `validity_adapter.py` is C4's file, a lane-1 edit in this branch). Book 3's day
   record with null `strategy_id`: done in their `story/d3-no-owner-override` (b49abdde), which also refuses any
   non-empty `owner_override`; F6 depends on it.
3. **To D4's owner:** none needed (F7 uses `BookTerms` only).
