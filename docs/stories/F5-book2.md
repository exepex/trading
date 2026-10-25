# F5. Book 2: AI decisions inside the envelope (design v2)

**Repository:** trading · **Owner session:** session_01B3RARTgoiGJwBKXRCgGRe8 (from 25 Oct 2026; text by
01SFDjjZx7JYziM3jqJytG2z, out of reach) · **Judges:** the orchestrator's two (Book 2's paper trades) · **Status:**
story text PASS (judge 307 add. 5); revision for the owner's Q11 (25 Oct), below

**Description:** As the owner, I want Book 2's AI to take, each day, the rule default or one alternative its envelope
allows, with a reason, so that scoreboard A can show whether **AI veto and width selection within the same registered
playbook** beat the rules alone.

**Context and why:**
- Design 12.1, 12.2 and 12.9; design v2 `07_ai_team.md` 7.1 and 7.3; REPLAN: F5 kept for slice E, F3 becomes the
  devil's advocate (T2, T3), and F4 drops owner overrides.
- The owner's decisions:
  - DESK_DECISIONS "D4/D5: the five design questions accepted as recommended" (16 Oct), item 4: no owner override
    on paper;
  - "build Books 2 and 3 end to end": the orchestrator's assignment of 16 Oct.
- **Owner, 25 Oct 2026 (DESK_DECISIONS, "9 yes, 10 yes, 11 yes"):** Book 2's envelope v1 is approved (Q9); and Q11:
  "for Book 2 only, D2's registered research candidates count as eligible rule defaults; each trade labelled 'strategy
  not yet passed'; D2's unproven limit (fewer than 20 trades: at most 1 open trade); Book 1 unchanged. Paper only."
  Why it was needed (strong evidence, code on `main`): D2 trades only `paper` and `paused` versions and evaluates a
  registered `research` version as a shadow (`fno/playbook/activation.py`); the only rule, `b0-monthly-sc` v1, is
  `research` (`playbook/registry.csv`); and D4 refuses any trade the rules did not offer. Without Q11 Book 2 could
  never trade. See "Revision for Q11" below.
- This text replaces the earlier F5 text in `F-ai-layer.md`. That text predates design v2: it had the red team and
  owner overrides as inputs.

**What Book 2 measures (D4 "Known limits", ChatGPT review 130 point 1):** with the playbook's approved versions and
their lots, the AI's real interventions are vetoes, width choices, lot reductions and switching to another eligible
version. Every report names the estimand **"AI veto and width selection within the same registered playbook"**
(`BOOK2_ESTIMAND` in `fno/constants.py`, read by S3), never "AI judgement adds value". The rule default is the paired
control. A zero difference is "inconclusive".

## Revision for Q11 (25 Oct 2026): Book 2's tradable versions (round 2: judges 631 and 632)

- **One definition, used everywhere for Book 2:** `book2_tradable(playbook, day, pauses) -> tuple[Strategy, ...]`
  (`fno/book2/tradable.py`) is exactly D2's approved set for the day, `playbook.approved_on(day)` (`paper` at the
  start of the day and still `paper` through it; never `paused`, `retired` or drifted: a pause stops new entries at
  once, judge 632 B1), **plus** the research versions D2 forward-tests that day, `playbook.shadow_on(day)` (registered
  in `playbook/registry.csv` before the day; an unregistered research file is never included, as D1's loader rules),
  kept only while their status through the day is still `research`, **minus** every version Book 2's own research
  pause has stopped on or before the day (below). Book 1 never calls it: Book 1's approved set is unchanged.
- **Where it replaces the approved set (judge 632 SF1), without touching Book 1's path:** Book 2 reads the playbook
  through `Book2Playbook` (`fno/book2/tradable.py`), an adapter over D1's `Playbook` whose `approved_on(day)` returns
  `book2_tradable` and whose `shadow_on(day)` returns nothing. It is passed to D2's `RuleEvaluator.evaluate`
  (`fno/playbook/evaluate.py:50-53`, which reads `approved_on` and `shadow_on`) when Book 2's sheet is built, and to
  C4's proposal builder (`fno/checks/validity_adapter.py:52`, which reads `approved_on`) when Book 2's decider builds
  its proposals. Neither D2's nor C4's code changes; Book 1 keeps passing the plain `Playbook`. Because the adapter's
  `shadow_on` is empty, Book 2's sheet evaluates no shadow and writes nothing into D2's shadow books (no double
  evaluation); the research versions it trades are evaluated as Book 2 candidates in Book 2's own book.
- **The sheet** (Part 1) therefore has a registered research rule that fires with a valid candidate under Book 2's
  own limits in `opportunities`; it can be the `rule_default` and is `eligible` when it reaches C2. Each opportunity
  carries `strategy_status` (its registry status through the day).
- **C4** (Part 3, step 3): `EnvelopeMode` (D4's Book 2 mode) runs unchanged on proposals whose `approved` set comes
  from `Book2Playbook`, so its `permitted` check, the envelope, the eligible check and the `unproven` check all apply.
  The envelope of that version must be registered in D6 (approved v1 for `b0-monthly-sc` v1).
- **D2's unproven limit** applies as built: a version with fewer than 20 completed Book 2 trades holds at most 1 open
  trade (at D2 and again at C4's `unproven` check, Part 3 step 4). Every research version is unproven. The limit is
  **per version**: a new version number starts again at 0 trades (Claims, for the owner).
- **Book 2's research pauses (judge 632 B2; the owner's risk rules of E6 applied to the versions Q11 opens):** E6's
  `cumulative_losses` counts a research version only on its shadow account and `AutoPauser` pauses only `paper`
  versions (`fno/scorecard/pauses.py:85-118, 128-145`), so without this Book 2's only limit on a research version
  would be the 1 open trade. F5 adds `Book2ResearchPauses` (`fno/book2/pauses.py`), one more `Review` in E6's
  `reviews` step (`fno/daily/reviews.py`), counting only Book 2's own closed trades of each research version, from
  its first Book 2 trade:
  - **catastrophic loss:** one closed trade losing at least the version's `catastrophic_loss_rs`;
  - **cumulative loss:** the realised net of those trades at or below `-CUMULATIVE_CAPS` (3) times that cap (E6's
    own constants, imported, never copied).
  A trigger appends one row to `journal/book2_hybrid/research_pauses.csv` (version, day, reason; written once per
  version) and sends one alert. `book2_tradable` drops a version from the day of its row, so new Book 2 entries stop
  at once; its open trades keep their exits. The registry, D2's shadow and Book 1 are untouched. Only a new version
  number trades again (its count starts at 0, as above).
- **Label:** every D3 record that chooses a trade writes `served["strategy_status"]` (F1t revision 2's strategy label;
  F1t's outcome record says "strategy not yet passed" when the status is not `paper`). **F5's own refusal (judge 632
  m1, defence in depth):** Book 2's decider raises `DecisionRefused` before returning a run with a chosen record
  that lacks it; F1t's run check refuses the same again. The scoreboards report the two labels apart (S2, S3).
  **What to expect (judge 633's note, for the owner):** `b0-monthly-sc` lost Rs 34,486 over 60 opportunities in
  2019-2023 and, by its own research record, can never show an edge; under Q11 Book 2 may paper-trade it, so expect
  negative paper results on those trades.
- **Criterion 6 changes, on the owner's word:** "with no approved version" becomes "with no Book 2 tradable version
  (`book2_tradable` empty)". Nothing else passed is changed.

## Scope

**In:**
- Book 2's day sheet in its private pack (part 1);
- the answer shape and its check (part 2);
- the decider that turns an accepted answer into one D3 run with C2 and C4 inside (part 3);
- the estimand label.

**Out:**
- the runner, prompt versioning and firing, sealing and the deadline (F1t); Book 2's prompt lines below are F5's;
- the analyst cards (F2);
- the devil's advocate (T2, T3);
- the AI judge (F4);
- the envelope files and their versions (D4, D6);
- Book 3 (F6).

## Part 1: Book 2's day sheet (E2's `BookSheet` port, shared with F6)

- **The port is E2's** and E2c's owner (0134MoC6) builds it on `story/e2e-book-sheet`:
  - `fno/desk/book_sheet.py`: `BookSheet(ABC).sheet(book, day, common: CommonPack) -> Mapping`, JSON-ready.
  - `WrittenPacks` takes `sheets: Mapping[book, BookSheet]`. After the common pack is built, it runs each book's sheet
    and passes the result to `PrivatePackBuilder.build(book, day, evaluation)`, which puts it in the body as
    `"evaluation"`. A book without a sheet produces a byte-identical pack.
  - A sheet that raises: that book's private pack is not written, one #fno-desk alert names the book and the reason,
    and the other books' packs are still written.
  - Wiring: `SHEETS = {book: sheet}` in `fno/desk/pack_wiring.py`. F5 adds Book 2's line when it merges, and Book 3's
    sheet is F6's.
- **F5 builds only Book 2's sheet** against that port.
- **Book 2's sheet** (`fno/book2/sheet.py`): D2's `RuleEvaluator` at the cutoff over Book 2's tradable versions
  (`book2_tradable`, "Revision for Q11"), with
  Book 2's own book and counts. It writes:
  - `opportunities`: every book-mode outcome, with its ID, version, decision, reason, and built terms (width, lots,
    structure);
  - `rule_default`: the opportunity IDs D2 chose, each with its terms;
  - `eligible`: the versions that reached C2 (`DayEvaluation.eligible`).

  No journal file is written. The private pack stays out of git (only its `.sha256` is committed), so the sheet is
  never public (E2c's privacy rule and the owner's O9 rule).
- **Its own rules** (E2c's review points a and d):
  - it reads only its own book's folder and the playbook (`ALLOWED_FOLDERS` in `private_pack.py`);
  - it reads the market as the next point says.
- **The data it reads:** the common pack holds no per-contract quotes and no D2 features (E2b), so the sheet reads the
  market itself, through E2's `canonical_snapshot(day, common, quotes)` (`fno/desk/pack_snapshot.py`,
  story/e2e-book-sheet 2d5dbf65), which returns the pack's own snapshot or raises `NotThePacksSnapshot`. It reads only
  **the canonical 3 pm snapshot that the common pack names in its provenance**
  (`a4_snapshot`, `snapshot_id`), never "the latest". It admits only data available by the pack's cutoff, as the
  common inputs do, so the pack's no-look-ahead guarantee holds. C2's inputs (margins, limits) come from cutoff-time
  sources too.
- **Why in the pack:** Book 2's AI must see the rule default before it decides at about 15:00, and that snapshot
  exists only from the `pack` step (O1's builder, 16 Oct). There is no new daily step.
- **Its time comes out of a margin** (O1's builder): the pack step retries until 15:10 for the canonical snapshot, and
  `ai_fire`, right after it, fires at 15:07 at the latest. On a late-canonical day, every second the sheet takes comes
  out of that margin. The tests time the sheet at the playbook's most strategies (every approved version, each with
  its widths) and report the worst case. The budget is 5 s (reasoning only: D2 over a handful of versions is the same
  work Book 1's run does).

## Part 2: the answer (`fno/book2/answer.py`, standard library only)

- **Shape:** `{"action": "follow_rule" | "trade" | "no_trade", "reason": <one line, 1-600 characters>, "slots":
  [...]}`.
  - `action` and `reason` at the top meet F1t's base check at `seal` (story/f1t-ai-trading-runner f1204a5a: `decision`
    has `action`, text, and `reason`, one line).
  - `action` (judge 307 addendum 1) is `follow_rule` when every slot follows its default, including a day with no
    slots. Otherwise it is `trade` when any slot trades, and `no_trade` when none does. `check_decision` refuses an
    `action` that disagrees with the slots.
- **Evidence** (F4, story/f4-ai-judge 90066e7d, design 1-2): a top-level `evidence` key, a list of 0-20
  `{"pack": "common" | "private", "pointer": <RFC 6901 JSON pointer>}`, with no values, so no private value reaches
  the public reveal. Any action other than `follow_rule` departs from the rule and must cite at least one pointer
  (F4's code judge).
- There is one slot per rule-default trade, in the sheet's order:
  `{"default": <opportunity_id>, "action": "follow_rule" | "no_trade" | "trade", "opportunity_id": <id or null>,
  "width": <number or null>, "lots": <int or null>, "reason": <non-empty str>}`.
- When the rule default is "no trade", `slots` is empty. The AI can never trade when the rules offered none (D4).
- `check_decision(decision, sheet=None) -> list[str]` (the name in F1t's port) lists the problems, and an empty list
  means it is acceptable:
  - wrong types;
  - a missing reason, or a top-level reason that is not one line of 1-600 characters;
  - a top-level `action` that disagrees with the slots;
  - slots that do not match the rule default one to one;
  - two slots choosing the same opportunity;
  - with `sheet` given, an `opportunity_id` not in the sheet;
  - a malformed evidence list: `check_decision` calls F4's `fno.judge.evidence.evidence_problems(decision.get(
    "evidence")) -> list[str]` (standard library only), so `seal` refuses it early.
- **Book 2's prompt says** (F4):
  - cite a pointer for every number you write;
  - quote numbers exactly as the pack writes them;
  - never write numbers in words (one, two, half, twice);
  - write dates as the pack writes them, and cite them. The values the decision itself names outside its reasons and
    evidence (IDs, width, lots) count as allowed numbers, because `check_decision` and C4 check them against the
    sheet;
  - account cash and positions are not citable (whole-text files), while the day sheet's values under `/evaluation`
    are.

  F1t's `seal` calls it without the sheet. `seal` also refuses private account figures in any answer text (F1t,
  judge 301), because `reason` is copied into the public record. The decider calls it with the sheet. The envelope
  is **not** checked here: C4 does that.

## Part 3: the decider (`fno/book2/decider.py`, F1t's `AiBookDecider`; story/f1t-ai-trading-runner f1204a5a)

`decide(accepted: AcceptedDecision) -> DecidedRun` (F1t's hand-over port):

1. **Inputs only from code.**
   - The sheet comes from `accepted.private_pack`, whose hash F1t checks against the pointer.
   - `rule_default` and `eligible` come from that sheet, never from the AI.
   - The AI's answer is only its choice and reason.
   - A missing or malformed sheet raises `DecisionRefused`, so the day is `refused`.
2. **Picks.** Each slot becomes a `Pick(opportunity_id, reason, width, lots)` for F6's generic `SelectionAllocator`
   (`fno/playbook/selection.py`, story/f6-book3-engine):
   - `follow_rule`: the default's opportunity at its own terms;
   - `no_trade`: no pick;
   - `trade`: the named opportunity, at the named width and lots.

   The allocator runs with `threshold=True` and a `rebuild` from D2's `CandidateBuilder` for a changed width or lot
   count. C2 and the unproven limit then run on the picks **in D2's own rank order** (`Candidate.rank_key`), so one
   ordering rule serves every book (F6). The first pick of an opportunity wins. Every other candidate is NOT_CHOSEN
   "not chosen by book2_hybrid".
3. **C4 per chosen trade** (`EnvelopeMode`, D4):
   - the proposal carries `rule_default` (the slot's default terms) and `eligible` from the sheet;
   - `permits` derives the actions;
   - `shadow-only`: the account takes the rule default and the choice is written as a shadow record (D3 `mode:
     shadow`). The default the account takes goes through the same allocator, C2 and C4 in the same run, like any
     pick;
   - `forbidden`: no trade, and the attempt is recorded.
4. **The unproven limit, re-checked independently at C4** (judge 260 addendum 2: D4 option 2, kept for F5's
   switch-on). **`EnvelopeMode`** (Book 2's C4 mode) gains a check `unproven`. Its input is each version's completed
   and open paper-trade counts from E5's records, plus the book's trades chosen earlier the same day that passed C4.
   A pick that would hold more than the limit fails `unproven`, whatever the allocator said. Book 1's `PlaybookMode`
   is unchanged: a test runs Book 1's C4 cases and finds the same results as before.
5. **One D3 run** (`DecisionStore`, atomic), like Book 1's `DecisionRun`. Every record has:
   - `rule_default`, `chosen_action`, `reason` and `authority_check` as non-empty text (D4 criterion 7);
   - `model_served` (= `model_reported`) and `session_id` from `accepted`;
   - both pack hashes;
   - `owner_override` null (D3);
   - `judge` = `AcceptedDecision.judge`, the path of F4's verdict file, which F1t adds;
   - in `served`, the playbook, config and `trade_envelope:<name>-v<n>` of every envelope used. The envelope keys
     are passed in the run context's `"served"`, which `DecisionRun.decide` merges under its own keys (F6's change).

   The picks go in `inputs.json` under `selection`, so D3's replay rebuilds the allocator and reproduces every record.
6. **Evidence, not inputs.** The analyst cards (F2) and the devil's advocate's objections (T3) are linked in the
   record. They are never an input of the allocator, C2 or C4.
7. **Fills and exits** (F1t and judge 301: nobody owned them; judge 307). Book 2 reuses Book 1's classes,
   parametrised by book and evaluator, not copied, as F6 does for Book 3. F1t wires them per book in
   `fno/daily/wiring.py`.
   - **Orders:** `ReplayedOrders` (`fno/books/book1_orders.py`) replays Book 2's committed run through D2's evaluator
     with the `SelectionAllocator` rebuilt from `inputs.json`'s `selection`. It must reproduce the stored records
     exactly, so an entry order is never rebuilt from JSON by hand, and its entry limit is C2's own. A run that does
     not replay orders nothing. Only trades that passed C4 are ordered.
   - **Exits:** `PlaybookExitRules` (`fno/books/book1_exits.py`): each Book 2 trade exits by the time exit fixed at its
     decision, from the version file that run read. Today's version file is read only to alert, never to move an
     exit.
8. **Timing.** `decide()` runs in O1's `ai_collect` step, between 15:11:00 and E3's 15:12 deadline. It does not
   re-run D2; it reads the sheet. Its run time is measured in the tests on a realistic day and reported, with a
   budget of 30 s, half of F1t's 60.

## Acceptance criteria

1. Book 2's private pack holds the sheet: rule default, eligible set and outcomes. Book 1's pack SHA-256 is unchanged.
   No sheet file appears under `journal/`. A later capture planted in the store is not read: the sheet uses the
   snapshot the common pack names. A sheet that raises refuses Book 2's pack with a named reason and writes no partial
   pack, while Book 1's and Book 3's packs are still built.
2. `check_decision` refuses each malformed shape in the test plan, including a decision with no top-level `action`
   or `reason` and an `action` that disagrees with its slots. It accepts every slot action, and F1t's base check
   passes every decision it accepts.
3. Each envelope action works end to end on fake sessions:
   - `follow_rule` trades the default;
   - `no_trade` trades nothing;
   - `choose_width` and `reduce_lots` trade the rebuilt candidate;
   - `choose_strategy` trades another eligible version;
   - a `shadow-only` action makes the account take the default and writes the shadow;
   - a `forbidden` action writes "no trade, blocked by C4" with the attempt.
4. A choice of an approved version that did not reach C2 (the rule did not fire, its own threshold, or the unproven
   limit) is refused by C4. So is a pick that breaks the unproven limit, whatever the allocator did.
5. Every record passes `validate_record`, and D3's replay reproduces the run from `inputs.json`.
6. With no Book 2 tradable version (`book2_tradable` empty), Book 2 writes the day's "no trade" record ("no approved
   strategy"), like Book 1 (revised for Q11, owner 25 Oct).
7. A Book 2 decision failing C4 never becomes a fill (end-to-end negative test through E4).
8. `decide()` takes at most 30 s on the test day (measured and reported).
9. Book 2's entry orders and exits use Book 1's `ReplayedOrders` and `PlaybookExitRules`, parametrised, not copied.
   The evaluator `ReplayedOrders` replays is rebuilt with the `SelectionAllocator` and the stored `selection` picks, as
   F6's Book 3 orders are, never D2's plain evaluator, which would order the rule default:
   - a `choose_width` run orders the rebuilt width, not the default's;
   - a changed pick in `inputs.json` (the run no longer replays) refuses every order of that run;
   - AI terms blocked by C4, or `shadow-only`, are never ordered; for `shadow-only` the default is what is ordered;
   - editing today's version file moves no exit: the trade keeps the time exit fixed at its decision.
10. Book 1's C4 results are unchanged by the `unproven` check (Book 1's existing C4 cases rerun).
11. With `judge_blocks` set, the run holds no chosen book trade: it holds the "no trade, judge failed" (or "judge
    unavailable") record and the rule default as a shadow, with `judge` set to the verdict path.
12. O11's end-to-end replay (`tests/e2e_acceptance/test_expected_missing.py`): before F5 merges, its part of the
    strict xfails becomes a real check in the replay, as D3, D4, D5 and O1 did (judge 306's addenda):
    - `test_book2_decides_on_the_recorded_day_from_a_fake_ai_answer` (with F1t: whichever lands second turns it real);
    - Book 2's half of `test_books_2_and_3_fill_and_exit_in_the_daily_run` (with F6).

    Unsure cases go to O11's builder (01FWkBH4).

13. **Q11 (owner, 25 Oct).** With only the registered research version `b0-monthly-sc` v1 (status `research`): Book 2's
    sheet has its fired opportunity as `rule_default` and in `eligible`, and a `follow_rule` answer gives a chosen
    trade with `served.strategy_status` = `research`, passing C4 (`EnvelopeMode`'s `permitted` from
    `Book2Playbook`); a research file with no registry row is never in the sheet; a version that is `paper` at the
    day's start and `paused` that day is not in `book2_tradable` that day, nor a `retired` one; with that version
    holding 1 open Book 2 trade and fewer than 20 completed, a second pick fails D2's limit and C4's `unproven`
    check; Book 2's sheet writes nothing into D2's shadow books; Book 1's evaluation and C4 results on the same day
    are byte-identical to today's (Book 1 trades nothing from a research version) (tests).
14. **Book 2's research pauses.** One closed Book 2 trade of a research version losing at least its
    `catastrophic_loss_rs` (boundary: exactly the cap triggers, Rs 1 less does not), or Book 2's realised net on it
    at or below 3 times the cap (boundary both sides), appends one row to `research_pauses.csv` and sends one alert;
    a second run that day adds nothing; from that day the version is not in `book2_tradable` and a new Book 2 pick of
    it fails C4's `permitted`; the version's shadow trades and Book 1's records do not count and are untouched; a new
    version number trades again (tests).
15. **F5's own label refusal.** Book 2's decider refuses (`DecisionRefused`) a run with a chosen record lacking
    `served.strategy_status`, before F1t's check (test with F1t's check stubbed out).

## Test plan

- Fake `AcceptedDecision`s built from the test playbook and a recorded common pack.
- The sheet compared with D2's own evaluation.
- One test per envelope action and per refusal.
- Mutation checks on the eligible check, the unproven re-check and the shadow path.

## Judge verifies

- Replays three Book 2 records against their sheet, envelope and packs.
- Checks that nothing the AI wrote reaches `rule_default` or `eligible`.

## Settled (owner and orchestrator, 16 Oct)

1. **F4 is built before Book 2 switches on** (owner). A failed or unavailable judge means no trade for Book 2 that day,
   and the day is still recorded (agreed with F4's builder, story/f4-ai-judge 00f49a0c):
   - `decide()` always runs. `AcceptedDecision` gains `judge` (the verdict path) and `judge_blocks` (bool).
   - When `judge_blocks` is set, the decider writes a "no trade, judge failed" (or "judge unavailable") run, with the
     rule default as a D3 `mode: shadow` record and `judge` = the path, so scoreboard A keeps the paired day.
   - F1t's run check refuses a blocked run that holds any chosen non-shadow trade.
2. **One slot per rule-default trade** (orchestrator's ruling), keeping D4's one choice against one default.

**Depends:** D2, D3, D4 (merged), E2's `BookSheet` port (story/e2e-book-sheet), E5 (counts), F1t, F6's
`SelectionAllocator` · **Size:** M

## Claims

Text round 2 (judges 631 and 632, all accepted): B1, `book2_tradable` is `approved_on(day)` plus `shadow_on(day)`
still `research`, never `paused` or `retired` (criterion 13's paused-that-day case); B2, Book 2's research pauses
(catastrophic and cumulative, counted on Book 2's own trades from the first, criterion 14); SF1, `Book2Playbook` names
where the set replaces D2's and C4's approved set, with no shadow evaluated twice; m1, F5's own label refusal
(criterion 15); judge 631's notes: one name (`EnvelopeMode`), and for the owner, the 1-open-trade limit is per
version and a new version number starts again at 0; judge 633's note on `b0-monthly-sc`'s record is in the text.
Merge order: F5's code merges after F1t's code (the `AcceptedDecision`, run check and label) and F6's
`SelectionAllocator`.


### Code round 1 (story/f5-code, 25 Oct 2026)

Branch `story/f5-code`, stacked on `story/f6-on-f1t` (F6 round 2, which carries F1t round 2); it merges after both.

**Built, by criterion:**
1. **Sheet (1):** `Book2Sheet` (`fno/book2/sheet.py`) is the pack step's `BookSheet` for Book 2. It runs D2 at the cutoff
   on Book 2's own account and view, using Book 1's reader's `at_cutoff`. The sheet lists every opportunity with its
   version's `strategy_status` and `widths`, the rule default with its built terms, `eligible` and Book 2's pauses. It
   goes into the private pack under `evaluation` (`SHEETS[book2_hybrid]`, built on first use inside the per-book
   guard). Timed at 12 versions: about 0.08 s, against the 5 s budget.
2. **Answer (2):** `check_decision` (standard library only) checks the slots one to one against the rule default, the
   F4 evidence shape and the action against the slots. Two slots may not take one opportunity, and a `follow_rule`
   slot takes its default.
3. **Envelope actions (3):** each slot goes through D4's own `AuthorityEnvelope` and `resolve` (`fno/book2/slots.py`):
   - allowed: the choice is picked;
   - shadow-only: the account takes the rule default and the choice is kept;
   - forbidden: the choice is still picked, so C4's `EnvelopeMode` blocks it on its own and its record reads "no trade,
     blocked by C4".

   Tests cover follow_rule, no_trade, choose_width, reduce_lots, choose_strategy, shadow-only and forbidden.
4. **C4 (4, 10, 13):** `EnvelopeMode` gains an independent `unproven` check. Under 20 completed paper trades a version
   may hold at most one open trade, counting the trades that passed C4 earlier the same day.
   - The counts come from C4's adapter through a new `extra(outcome)` hook. They are asked exactly as D2's allocator
     asks them, and a replay reads the recorded counts, so it reproduces every result.
   - Without counts the check fails closed.
   - Book 1's `PlaybookMode` is untouched.
   - The C4 rule default for each pick is its slot's default terms from D2's rule-default evaluation, never the AI's
     (judge 260), and is stored with the pick in `inputs.json`.
5. **Records and replay (5):** every record passes `validate_record`, and D3's replay with Book 2's validator returns
   no difference. `authority_check` is the envelope's verdict per slot.
   - **A D3 gap fixed for Book 2 (strong evidence: `RecordBuilder` wrote `rule_default` = the book's own action):** a
     vetoed default read "rule default: no trade". `DayInputs` now carries Book 2's rule action per opportunity
     (`book2_rule_defaults`, written only when present, so Book 1's bytes are unchanged), and `RecordBuilder` and the
     replay use it.
   - So a veto reads rule default "trade" and chosen "no trade": the paired comparison scoreboard A needs.
6. **No tradable version (6):** an empty sheet gives the day's "no trade" record.
7. **C4 failure never fills (7)** and **orders and exits (9):** `Book2Orders` is Book 1's `ReplayedOrders`, rebuilt from
   the stored picks, their defaults and the recorded counts.
   - A choose_width run orders the rebuilt width.
   - Blocked choices are never ordered; for a shadow-only choice the default is ordered.
   - Any edit of `inputs.json` refuses every order.
   - Exits are Book 1's `PlaybookExitRules` over Book 2's records, from the version file the run read.
8. **Timing (8):** `decide()` on the test day: 0.125 s, measured (budget 30 s). F1t's hard time limit bounds a slow day.
9. **Judge (11):** with `judge_blocks` the run picks nothing (no chosen trade, `judge` set), and the day log keeps the
   rule default as the shadow.
10. **Q11 (13) and pauses (14):** Book 2's view and its research pauses (part 1). `Book2ResearchPauses` joins E6's
    `reviews` step only while Book 2 is live, and `research_pauses.csv` is committed by that step.
    `research_pauses.csv` is append-only and never back-dated (judge 632.1): a rewritten earlier row or a row dated
    before the last one refuses the read (`PausesRefused`), with tests.
11. **Label refusal (15):** Book 2's decider refuses a chosen record without `served.strategy_status`. Tested with
    F1t's check never reached.
12. **Through F1t:** real Book 2 days pass F1t's real `Promoter` and run check, labelled "strategy not yet passed"
    (research picked), "strategy passed" (paper only) or "" (no trade). A judge-blocked day passes F1t's block check.

**Q12, an assumption awaiting the owner (orchestrator, 25 Oct):**
- Text amendment, one line: *for Book 2 only, the no-trade threshold binds paper versions only* (`binds_paper`). A
  research version Book 2 may trade is allocated as D2's shadow test allocates it. Without this, D2 would refuse every
  research candidate for its missing estimate and Q11 would trade nothing.
- **What (A) measures:** whether Book 2's AI veto and width choices improve on a rule known to lose about Rs 386 per
  opportunity (b0-monthly-sc's research record). That comparison is the only thing that makes paper-trading a known
  loser worth anything.
- The records now hold what the comparison needs: per opportunity, the rule's action next to Book 2's, and in the day
  log each slot's default terms and choice.
- The rule's own result on the same days is that version's D2 shadow account (Book 1's run shadow-trades every
  registered research candidate).
- **Not built here:** the scoreboard view that lists vetoed days against that shadow result. That belongs to the
  scoreboard's story; F5 only records the inputs.
- If the owner says (B), it is a one-line change (`binds_paper` → `True`).

**Deviations and choices to check:**
- **Shadow records (asked of the orchestrator):** the text asks for a D3 `mode: shadow` record for a shadow-only choice
  and for the rule default on a judge-blocked day.
  - D3's shadow records are D2's shadow-book outcomes, which fill shadow accounts, so emitting them from Book 2 risks a
    fill path nobody owns.
  - Both cases are recorded in Book 2's day log (`journal/book2_hybrid/ai_days/<day>.json`) instead. Envelope v1
    allows every action, so the shadow-only case cannot occur under v1.
- `served.strategy_status` is run-level in D3: a run that picks any research version is labelled `research`
  (conservative: a paper trade in the same run then also reads "strategy not yet passed").
- **The prompt stays neutral on the rule's record** (it says what `research` means, not "this rule loses Rs 386").
  Telling the AI the rule loses would make the veto a reaction to the prompt rather than to the market. Reasoning
  only; the owner may prefer otherwise.
- **Shared code touched, each a small refactor with the callers' tests green:**
  - F6's fired-packs check moved to `fno/ai_trading/fired_packs.py`, shared by both deciders.
  - F6's `_parts` became `account_parts(root, market, book)`.
  - D2's `CandidateBuilder.build` now loops over the new `at_terms`, with the same messages; Book 1's tests are
    unchanged.
  - The allocator's `threshold` may be a per-candidate rule.
  - The test margin fixture gained a width-50 row.
- **Until F4's code lands, `NoJudge` blocks Book 2 every day** (F1t's rule, F4 owner decision 16 Oct). Switched on
  today, Book 2 would record "judge unavailable", no trade, every day. F4 must be built before Book 2's live date.

13. **O11 (12):** both of Book 2's strict xfails are real checks now, on the recorded day of 16 Oct
    (`tests/e2e_acceptance/book2_replay.py`):
    - Book 2's private pack carries `Book2Sheet`.
    - A follow-the-rule answer goes through F1t's real `Promoter` and run check into Book 2's real decider, C2 and C4
      (the version's envelope registered in D6).
    - E3's daily run collects run `r1`, fills its 4 legs with `Book2Orders`, reviews the exit ("held") with Book 2's
      exit rules and marks the trade, with no alert.
    - `Replay.daily_run` was split into `books()`, `orders()` and `commands()` for this, with no behaviour change.
    - Book 3's half stays a strict xfail under F6 (`test_book3_fills_and_exits_in_the_daily_run`). O11 went from 13
      xfails to 12.
    - F1t's sealing is not in this replay; its own end-to-end test covers it on E3's real run.

**A defect found by the replay, outside F5 (reported, not fixed here):** E3's `fills` result in the run log is keyed by
trade ID alone (`fno/desk/daily_steps.py:185`).
- Book 1 and Book 2 taking the same opportunity, the normal follow-the-rule day, give the same trade ID, so the run
  log keeps only one book's fill result.
- On 16 Oct both books filled 4 legs, and the log shows one entry.
- Each account's fill records are correct and each failure is still alerted. Only the run log and what reads it lose a
  line.
- Fix proposed for its owner (E3's run log, lane 1): key the result by book as `decisions`, `exits` and `trade_marks`
  already are. That touches the run-log schema read by about ten test files.
