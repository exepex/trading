# Response 261: stories F6 and F7, Book 3's decision engine and matched shadow file (story text)

Builder: session_01KTAQCDjPkDBKwfCMhWphXb · Branch: `story/f6-book3-engine` · Lane 1 (new stories) · Judge E.

## What this is

The story text only (quality rule 1): `docs/stories/F6-F7-book3.md`. F6 and F7's first-plan texts in
`docs/stories/F-ai-layer.md` now point to it. No code yet.

## Claims for the text check

1. F6 builds on D5 as merged (00a2995e). Proposals are registered by D5's `register()` on day d and trade from d+1
   only, through `require_registered` and C4's `ConstitutionMode`. Book 3's daily choice is a pick among D2-built
   candidates of its own registered specs. No daily width or lots change: the spec is the strategy.
2. F6 fits F1t's `AiBookDecider` port as written in F1t's story text (`story/f1t-ai-trading-runner`): one D3 run
   with C2 and C4 inside, extra files in `DecidedRun.files`, `DecisionRefused`.
3. F7 writes D4's `BookTerms` (or `None`) per common opportunity at one lot. It never writes D4's action labels; S3
   derives them when it reads, as D4's rule says.
4. Every requirement of design 12.1, 12.3, 12.5, 12.6, design v2 7.2 and 7.5 and the first-plan F6/F7 is in a
   criterion or out with its reason (the two gap tables).
5. Departures from the first-plan text, with their reasons:
   - No stored `pilot` label. S2/S3 derive pilot from all books' records, and a label written at decision time
     could be wrong on the common start day itself.
   - No separate registration commit. A day-d proposal trades from d+1, when D5 checks ancestry.
   - `new_or_reused` uses a rule key, not `parameters_sha256`. The D1 hash covers name and version
     (`fno/playbook/schema.py:108`), so equality on it could never catch a copied rule.

## Agreements and open points

- D5's owner (01SFDjjZ), 16 Oct 2026: `new_or_reused` derived by code; a `strategy_id_of` helper in
  `fno/book3/registry.py` used by `register` and C4's `proposal_of`; Book 3's day record may have a null
  `strategy_id` (their `story/d3-no-owner-override`, b49abdde, which also refuses `owner_override`). My correction
  of their hash-equality proposal was sent to them; their reply is pending.
- F1t agreed (its e0ba1b43): write paths restored on any failure; `check_decision` signature; `brief` prints `agents/book3/decide_v1.md`.
- F5 agreed: one `SelectionAllocator` (built here, with an optional `rebuild` for Book 2) and one `BookSheet` pack port (pending E2c's owner).
  (Book 2's rule default, Book 3's day sheet).
- F2 answered (its 2a0140dd): `analyst_cards` export item, card ID `<role>/v<n>/<day>`, role set joined with `+`.

## Known risks (said plainly)

- Strategy windows: D2 opens an opportunity only on the first day an expiry enters a spec's window. A Book 3 spec
  must be registered before its window opens, or it never trades that expiry. The prompt must say so. Reasoning only.
- Descriptive spec fields (`funding`, `expected_range`) are the AI's own estimates; no code reads `funding`.
- Book 3 cannot trade before slice E's trigger and F1t's live switch, so nothing here runs live soon.

## Judge 302 (Judge E): FAIL at 77a46c33, three should-fix and two minor findings, all accepted

I checked each finding against the code and the texts before accepting it.
1. **Orders and exits had no owner (accepted).** E3's fill path asks every book for an `OrderBuilder` and
   `ExitRules` (`fno/desk/daily_ports.py:125,149`). Only Book 1's exist (`fno/books/book1_orders.py`,
   `book1_exits.py`), and F1t only dispatches them. F6 now owns `Book3Orders` (Book 1's `ReplayedOrders` with an
   evaluator rebuilt from the stored picks) and `Book3ExitRules` (Book 1's `PlaybookExitRules` over Book 3's store and
   specs): design item 8, criteria 14 and 15.
2. **Restore rule (accepted).** My text said "tracked files to HEAD". F1t's text at c5c73568 restores to a byte
   snapshot taken just before `decide()`, so a ledger row written earlier by anyone survives. It is now quoted
   word for word.
3. **Day-sheet hook owner (accepted).** The `BookSheet` port is built by F5's builder with E2c's owner and is now
   in Depends; F6 supplies Book 3's sheet. New criterion 13: same 15:00 sources as D2, built before the private pack,
   inside its hash.
- Minor 1: proposals register only from a promoted answer (design item 2, criterion 16). F1t's judging decides
  promotion, so the full test runs once F1t's code exists. Until then a decider test proves registration happens
  only inside `decide()`; I say this plainly rather than claim more.
- Minor 2: F7's shadow file is written even when C2 or C4 refuse the real pick (F7 design, criterion 3).

## Code (story text PASS: judge 302 addendum 1 at b096a4a2; text addendum 1 for F4 at c625151e)

Branch `story/f6-book3-engine`. Gates on the final tree: `pytest -n auto` **7862 passed**, `ruff check` and
`ruff format --check` clean, `tools/check_imports.py` clean, `tools/check_records.py` clean.

### What was built, by criterion (code, then test)

| Criterion | Code | Test (tests/…) |
|---|---|---|
| F6-1 no same-day trade; unregistered or edited spec never trades | `fno/book3/strategies.py` (`on`), `fno/playbook/opened_playbook.py` (`approved_on`: strictly after the opening day) | `book3/test_strategies.py` (6+1), `book3/test_decider.py::test_a_proposal_registered_today…`, `…edited_after_registration…` |
| F6-2 rule key, refused copy, `reused`/`new` | `fno/playbook/schema.py` `rule_sha256(strategy)`, `fno/book3/proposals.py` | `book3/test_proposals.py` (four dodges, playbook copy, supersedes, re-versioned) |
| F6-3 guards (constitution, status, evidence, no estimate, cap at/over 10,000, unenforceable exits, unreadable text) | `fno/book3/proposals.py` `_guards`, `_problems` | `book3/test_proposals.py` |
| F6-4 registry `model` = registered model | `fno/book3/decider.py` (`register_all(... accepted.registered_model ...)`) | `test_decider.py::test_the_registry_row_names_the_registered_model…` |
| F6-5 shape refusals; refused pick alone | `fno/book3/answer.py` (standard library only), `fno/playbook/selection.py` (`attempted`, `NAMED_TWICE`) | `book3/test_answer.py`, `playbook/test_selection.py` |
| F6-6 C2 and C4 on picks | D2's `Allocator` behind `SelectionAllocator`; C4 `ConstitutionMode` through `proposal_of` (`fno/checks/validity_adapter.py` sets `strategy_id`) | `test_decider.py` (C2 slot refusal, C4 block on a damaged constitution) |
| F6-7 records and replay | `fno/playbook/decision_record.py` (`_strategy`), `decision_inputs.py` (`selection`, `opens`), `decision_run.py` (`selection`, `served` merge) | `test_decider.py` (validate_record, replay, edited `selection` found) |
| F6-8 zero cards, strategies, candidates; given cards only | `decider.py` `_cards` | `test_decider.py` |
| F6-9 objections never an input | no input path (the allocator, C2 and C4 take none) | `test_decider.py::test_shadow_entries_change_nothing…` (identical records) |
| F6-10 pilot read by S2 | no stored label; Book 3 runs in D3's store | `book3/test_pilot.py` (alone: pilot; all three on time: common start; late: pilot) |
| F6-11 end to end | `decider.py` | `test_decider.py::test_a_pick_of_yesterday_s_strategy…` |
| F6-12 shared `SelectionAllocator` | `fno/playbook/selection.py` | `playbook/test_selection.py` (12 cases incl. Book 1 bytes unchanged) |
| F6-13 day sheet | `fno/book3/evaluation.py` `day_sheet` (with `common_widths`); decider compares every term | `test_decider.py` (no sheet, other IDs, other terms) |
| F6-14 orders | `fno/book3/orders.py` (Book 1's `ReplayedOrders`, evaluator from the stored picks) | `book3/test_orders_exits.py` (ordered once, no trade, C4 block, edited picks or spec refuse, canonical rewrite still orders) |
| F6-15 exits | `fno/book3/decision_wiring.py` `build_book3_exit_rules` (Book 1's `PlaybookExitRules` over Book 3) | `test_orders_exits.py` (fixed exit, deleted spec alerts, no opening record) |
| F6-16 registration only inside `decide` | structural | `book3/test_wiring.py` (AST: only `Book3Decider.decide` calls `register_all`). The test through F1t's judging needs F1t's code: not yet possible |
| F7-1 one entry per opportunity | `fno/book3/shadow_file.py` | `book3/test_shadow.py` (missing, twice, widths at/just beyond the set, unknown IDs) |
| F7-2 late reads as not observed | `fno/book3/shadow_reader.py` (D3's `file_timeliness`) | `test_shadow.py` (at, 1 s after, 1 s before 15:15) |
| F7-3 never the account; written on a refused pick | separate path; decider writes it after the run | `test_decider.py` |
| F7-4 other pack, edited file | `shadow_reader.py` (bytes as first committed) | `test_shadow.py` |
| F7-5 empty cases | | `test_shadow.py` |

Prompt: `agents/book3/decide_v1.md`. Wiring: `fno/book3/decision_wiring.py` (builds on the repository: `test_wiring.py`).

### Broken-code proof (quality rule 4)

A script broke each criterion's code on purpose, ran its test and restored the file: **37 of 37 mutations caught**
(after one test was tightened: "same-day strategy tradable" first survived because D5 refuses it too; the test now pins
that a same-day spec is not yet open rather than refused). The script's list names each mutation, file and test.

### Self-review (quality rule 3): two independent agents, correctness and silent failures

Every finding was checked against the code before acting; all fixed with a test, except where said.
1. Unenforceable text exit registered, then every order of the run refused: **fixed** (guard, test).
2. Rule key on raw YAML dodged by wording, spacing, number spelling, condition order: **fixed** (key from the parsed rule; four tests).
3. An impossible date (`ValueError`) crashed the whole day: **fixed** (any unreadable text refuses that proposal only).
4. Shadow widths not in Book 3's input: **fixed** (`common_widths` in the day sheet; prompt says so).
5. Pack hashes overwritten, never compared: **fixed** (`DecisionRefused` when the packs read differ from the fired ones).
6. Day-sheet check compared IDs only: **fixed** (every term compared).
7. `DecidedRun.files` missed the registry, spec, ledger and C4 log: **fixed** (test lists them).
8. Duplicate pick or shadow entry refused the whole answer (story says alone): **fixed** (attempted / `no_decision`).
9. The answer's day reason not stored: **fixed** in the day log; the D3 day record keeps D2's text so replay needs no
   AI text. This is a small change to design item 6's wording, made in the story text.
10. `served` lacked F1t's decision version: **fixed** (`ai_decision_version`).
11. `\r` and other line breaks passed the one-line rule: **fixed** (`splitlines`).
12. A second `decide` wrote before failing: **fixed** (refused before anything is written).
13. Orders edit tests passed without an edit (non-canonical rewrite): **fixed** (canonical bytes; an unedited rewrite still orders).
14. Missing registered spec freed its rule: **fixed** (committed text read; missing everywhere refuses the day's proposals).
15. `analyst_cards` key names (`card_ids`, `role_set_version`) are this branch's assumption: **open**, asked of F1t
   and F2; an item without them is refused, never read as "no cards".
16. Shadow reader returns `{}` when no common pack exists: **kept, with the reason**. No common pack means no common
   opportunity exists for any book that day, so there is nothing to observe. The wiring reads the common pack
   from the working tree; with E2c packs move to Drive, so the reader's `common` source follows E2c's store when it lands.

### Real output sample (fixture dry run; test data, no live strikes, no post)

Made by `tests/book3/engine_builders.py` fixtures: one registered SC spec, a pick of it plus a pick of an unknown
opportunity, two proposals (a copy, and a copy with a stop text), and a shadow take at width 250.
- Record: `{"book": "book3_ai", "strategy_id": "b3-sc-v1", "chosen_action": "trade", "reason": "picked by book3_ai: pick b3-sc-v1:2026-11-27"}`, C4 mode `constitution`, ok.
- Day log: the unknown pick under `attempted_picks` ("not a built candidate today"); both proposals refused ("same rule as b3-sc-v1: trade that one"); `reason` "one built SC today; nothing else".
- Shadow: `sc-a-v1:2026-11-27` → `no_decision`, "width 250 is not in sc-a-v1's set [300.0, 200.0, 100.0]".

### Known limits (said plainly)

- Not runnable live yet: F1t's runner, E2e's `BookSheet` port (Book 3's sheet class plugs in when it lands) and F4's
  `evidence` (addendum 1) are not on `main`; F1t's live switch is null.
- Until E2e's shared snapshot helper lands, Book 3 reuses Book 1's input reader with a `book` argument (no copy).
