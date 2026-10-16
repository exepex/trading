# Response 244: story P11, the per-page hold (story text for the judge)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/ph1-page-hold`. Lane 1. Asked by the orchestrator (16 Oct
2026): "Build the per-page hold as its own lane-1 story before the card page (P2f)", with the owner's decision (hold
only the card page and say so on screen) and judge 233 addendum 3's three conditions.

The text is `docs/stories/P-publishing.md`, section P11. In short:
- A block may raise `PageHeld(rule)`. Only that page is held, keeping the previous publication's row unchanged
  (visibly dated). Every other page publishes. One #fno-desk line and the run status name the page and the rule, never
  a value.
- No database migration: 002's check forbids a `reason_code` on a `published` row but allows its `reason`, and
  `pages_history`'s key lets a copied row keep its older `as_of` (strong evidence: `db/fno/migrations/`).
- Nothing else changes: every other failure still stops the whole run.

**Points for the judge (reasoning only):**
1. A held page keeps its old row rather than going absent, so the screen shows the last good card with its age.
   The owner's on-screen line comes from the screens lead's contract field.
2. Should a hold ever be allowed for other pages that stop the run today (the Forecast lab's year-end gap, an open
   paper trade)? I recommend each as its own owner decision, not by default: a hold hides a page's staleness only
   behind its freshness label.
3. The run is `published` even with a hold. The bell (W8) reads `reason`, so the dashboard can still show it.

Code follows only after the story text's PASS.

## Addendum 1 (16 Oct): the card's on-screen notice and the other users, before the judge's look

- **The card is shown held through its payload** (screens lead, contract 2.12.0 `FnoCard.withheld`). So
  `BlockBuilder.held(previous_payload, rule)` gives each block its held payload.
  - The default is the previous payload unchanged, so a held page keeps its row byte for byte.
  - The card's is the previous card with `withheld` set; its own session is never re-dated.
- **Users:** the orchestrator relayed the owner's principle ("treat them as holds unless the judge objects").
  - The Forecast lab's year-end answer day (judge 244);
  - the paper books page's open trade, or a trade or shadow it cannot label (judge 248);
  - proposed for the judge: Home's two existing whole-run stops, an open trade and an approved strategy's picks.
    The second is met on the day of the first approval, before any trade.

## Addendum 2 (16 Oct): Home's two stops become holds in this story

The orchestrator decided:
- Home's open-trade stop (`OPEN_TRADE_RISK`) holds the `risk` page;
- its approved-picks stop (`APPROVED_PICKS`) holds the picks page;
- both are built here;
- new acceptance criterion 8: P11 is merged before the first strategy approval, and a planted approval and a planted
  open trade each leave every other page published.

## Addendum 3 (16 Oct): judge 251 accepted: every hold is said, and no held page states a falsehood

**Accepted, checked against the code.** `home_blocks.py:15-17` already names "an empty panel that is no longer true"
as the reason it stops today, so a held copy of it would bring that back.

**Chosen: both, (b) for every page plus (a) where a payload would lie:**
- **(b), a generic notice:** a `page_holds` page in every publication (`[{page_key, since, rule}]`, empty on a normal
  day). It needs `FnoPageHolds` in the contract (the screens lead) and the W3 screens' rendering (the E4c/E4d
  builder). It is ordered before P2b's and P2c's rebase and before the first approval.
- **(a), per block:** `held()` returns the previous payload, or None for no row.
  - The Forecast lab and the paper books keep theirs: their old payloads stay true for their own session.
  - Home's picks and books drop theirs: the old payloads say "no approved strategy" and limit_used 0.
  - The card shows `withheld`.

**Contract bumps (the judge's note):** a held copy is validated against the current pin. A copy that no longer matches
gets no row, never a whole-run stop, and its alert line says so (criterion 10).

## Addendum 4 (16 Oct): the code (text PASS, judge 251 addendum 1)

Branch `story/ph1-page-hold`, main merged in.
- `fno/market_read_models/page_holds.py` (new): `PageHeld(rule)`, `page_holds_payload` (`since` carried while held,
  reset when a hold lifts and returns), `held_lines` (one line per held page, the copy-broken suffix), and
  `PageHoldsBlock` (its key and schema for the check; it is built by the publication, never from the rows, so it can
  never be held).
- `blocks.py`: `BlockBuilder.held(previous, rule)`, unchanged by default.
- `publication.py`: `build(rows, previous)` catches `PageHeld` per block and reads the current publication only when
  a page is held (`_once`).
  - A held copy keeps its previous row's session, cut-off, build time, code and payload, under the new publication.
    It is checked against the current pin.
  - A copy that fails gets no row and is listed in `broken`.
  - The publication ID covers the held copies.
- `market_run.py`: one alert per held page, the lines in the run status `reason` (`published`, no reason code), and a
  failed read of the current publication named as a publish stop. `postgres_publisher.current()` now wraps database
  errors as `PublishFailed`, as `stored()` does.
- `home_blocks.py`: Home's open-trade and approved-picks stops raise `PageHeld` with fixed sentences (no book name,
  count or strategy any more) and hold with no row (`HeldWithoutRow`).

**Not wired yet, stated plainly:** `PublicationBuilder(holds_page=...)` stays None in `wiring.py` until `FnoPageHolds`
is pinned (screens lead, 2.13.0). So this branch must not merge before that pin (judge note 1). Wiring it is one
line plus the pin.

**Tests:**
- `tests/market_read_models/test_page_holds.py`: criteria 1-5, 7, 9 and 10; `page_holds`' shape and its never-held
  rule; the `since` reset.
- `tests/market_read_models/test_home_blocks.py`: criterion 8, a planted open trade and a planted approval each
  hold only their page with no row, every other page published, one alert, the run status `published` with the rule.
- Criterion 6: the existing FiguresNotComputed, ContractBroken and crash tests stand unchanged.

## Addendum 5 (16 Oct): `page_holds` in contract 2.13.0's shape

The screens lead's `FnoPageHolds` (story/fno-contract-2-13 5c6fcdb, not merged yet) is
`{holds: [{page_key, since, reason, shows}]}`:
- `reason`, not `rule`: the privacy check refuses rule-named keys;
- `shows` is previous_page or nothing;
- no digit in a reason.
The payload now has that shape. Home's two reasons are reworded with no digit ("C2", "P10" removed), and a test
checks every hold reason in the code. The pin and the one-line wiring follow its merge.

## Addendum 6 (16 Oct): judge 255's three points

1. **Every hold sentence is digit-free.**
   - The card's reason is "A risk rule was broken: the risk sizing or the validity check let a trade past its book's
     per-trade cap"; "C2" and "C4" are gone.
   - Home's two reasons were reworded in addendum 5.
   - The final list went to the screens lead for the examples.
2. The keys are `reason` and `shows`, as in the code since addendum 5.
3. A test checks every reason against the pattern. It reads the pinned `FnoPageHolds.reason` pattern once 2.13.0 is
   pinned; until then it checks the same rule, no digit.

## Addendum 7 (16 Oct): one list of reasons, the screens lead's wording

The screens lead's plain wording is adopted exactly; the contract's examples (story/fno-contract-2-13 b8399c7) carry
the same three sentences, so there is one list:
- card: "A risk rule was broken: the sizing or validity checks let a trade past its book's per-trade cap"
- risk: "A book holds an open trade whose risk this page cannot compute yet, so nothing is shown rather than a wrong
  figure"
- today: "A strategy is approved, and this page cannot build its picks yet, so nothing is shown rather than an empty
  panel that is no longer true"
The story codes (C2, C4, P10, D3) stay in the code's comments.

## Addendum 8 (16 Oct): the pin head (judge 257's three points)

1. **Pinned 2.13.0 at dashboard main d53cefeb** (strong evidence: byte copies; contract-check "same as the
   dashboard's"). It includes the new schema file `api/schemas/fno-page-holds.yaml`; I checked that no `$ref` in the
   pinned files is left without a definition. `holds_page=PageHoldsBlock()` is wired in `wiring.py`, so every
   publication carries `page_holds` (1,273 pages a day on this branch).
2. **The tests use the real `FnoPageHoldsResponse`** (`FreePageHolds` is removed). Home's held test checks the published
   `page_holds` row. The reason-pattern test reads the pinned `^[^0-9]*$`.
3. **A paged block cannot be held:** `PageHeld` from a block stored one page per parameter is refused with a named
   `TypeError` (test with P9's chain rows).

Also fixed against the pinned schema: holds are listed oldest hold first (`since`, then page key), as `FnoPageHolds`
says.
