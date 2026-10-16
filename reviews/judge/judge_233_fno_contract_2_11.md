# Judge 233: dashboard contract 2.11.0, the card's per-trade loss cap (`trade.max_loss_cap`)

Dashboard `story/fno-contract-2-11` at f94f3bf (screens lead 01XFXpbkyixX7SuXeQCp5EnX), on main f4f7f40. Lane 1
(contract). Judge D, 16 Oct 2026.

**FAIL: one should-fix.** Everything else is met.

| Claim | Result | Evidence |
|---|---|---|
| 1. `FnoCardTrade.max_loss_cap` is new, required, INR Paper, from C5's `max_loss_per_trade_rs`; mockup 39 reads it | PARTLY | The field is required in `fno-card.yaml`. Trading's `config.yaml` sets `max_loss_per_trade_rs: 10000` for both `books` and `manual`. `const CAP = 10000` is gone, and the bar width and visible words read `T.max_loss_cap`. But the bar's `aria-label` in `39-trade-card/js/3-position.js:50` still says `of the Rs 10,000 cap`. See the finding. |
| 2. `maximum: 10000` stays the owner's ceiling, and the probe still bites | MET | Both `max_loss` and `max_loss_cap` keep `maximum: 10000`, and `exclusiveMinimum: 0` is on the cap. My planted breaks on `getFnoCard_india_trade` were each rejected by `check_fno_screens` (exit 1, the `payload/trade` problem): cap removed, cap 10001, cap 0. A config above Rs 10,000 fails validation and the page stays unpublished, which is a closed failure. The description says raising it is a contract change. |
| 3. Version 2.11.0; a 2.10 card with a trade is rejected; examples and regenerated files at 2.11.0 | MET | `openapi.yaml` 2.11.0 has its note. The other changes are version strings plus the new field in two examples (TRADE, WATCH). These all exit 0: `check_contract`, `check_fno_screens`, `examples`, `render_catalog` and `render_fno_catalog`. The card page is not published (P2f), so no live payload breaks. |
| 4. Menu groups: 39 `strategies`, 40 and 46 `markets` | MET | `PF.mount` `group` changes only in `9-mount.js` of 39, 40 and 46. This matches story W3 answer (a) (card in Strategies, weather in Markets). |
| Gates | MET | `sync-design` clean, `tsc` OK, `npm test` 520/520 (0 skipped). |

## Finding (should-fix)

**The cap bar's screen-reader label still copies Rs 10,000.** `3-position.js:50` reads
`'aria-label': \`${Math.round(share * 100)}% of the Rs 10,000 cap\``. The visible line beside it uses
`rs(c, T.max_loss_cap)`.

- **Path:** the owner lowers `max_loss_per_trade_rs` (allowed: the schema only caps it at 10,000), for example to
  Rs 5,000. The card then sends 5000. The bar and the visible words say "of the ₹5,000 a trade may lose", but a
  screen reader says "of the Rs 10,000 cap".
- **Why it matters:** this silent copy of the owner's number is exactly what the field was added to remove (claim 1;
  judge 224 addendum 3). W3f will build the screen from this mockup.
- **Fix:** use `rs(c, T.max_loss_cap)` in the label. The header comment's "against the Rs 10,000 cap" (line 1) may
  stay as description, or say "against the book's per-trade cap".

## Note

- The schema cannot check `max_loss <= max_loss_cap`. C2 sizing enforces it on trading's side. P2f's build should
  refuse a card whose `max_loss` is above `max_loss_cap`, since both come from the same records.
