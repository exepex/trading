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
