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
