# Response 219: the F&O screens with real data (P2 rewritten, W3), story text and claims

Story: `docs/stories/W3-fno-screens.md`. Owner decision 16 Oct: all F&O screens now, through the existing Azure path.

## Claims

1. **No new path.** Every F&O page is one more `BlockBuilder` in the 07:10 `market-publish` run (validated against the
   pinned contract, one transaction, read back by hash) and is read by the dashboard's existing `PublicationReader`.
   Strong evidence: the job publishes about 1,245 pages a day today; the four `OMENIX_FNO_PG_*` settings are on Vercel.
2. **Real data, honestly labelled.** Weather has 2,409 real days, all back-fill (0 live); the card has 1 test delivery;
   the books have 0 open trades; no strategy has passed (54 trials); scoreboards have never run; budget has 1 usage
   row. Each screen shows exactly that, with empty and Example states where data is missing.
3. **Two privacy gaps found and fixed in the text** (strong evidence, read the code):
   - `ContractBroken` prints jsonschema's message, which quotes the failing value, into the public Actions log
     (`fno/market_read_models/contract.py:71`); P2 changes it to path and rule only before any private page.
   - The weather records carry each input's `reaches` colour; with 2,409 days of values that reveals the input levels
     the owner said are never shown. `reaches` is never sent.
4. **Private inputs stay in memory.** Drive-only inputs come through E2c's existing download, which stops the run when
   Drive cannot be read; a page is never built from a fallback value.
5. **Never sent:** strategy rules and thresholds, weather input levels, AI model names and session ids, the US cue.
6. **Open (reasoning only):** one 07:10 run shows the previous session; a second publish after the daily run is the
   owner's later call. The nav placement and route names are proposals the owner may move.

## Build order

Weather, Forecast lab, paper books, Strategy lab, data health, card, budget, scoreboards (the last waits for S2/S3
runs).
