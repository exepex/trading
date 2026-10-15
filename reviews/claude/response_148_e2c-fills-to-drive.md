# Response 148: story E2c, per-contract paper fills, marks and equity history in Drive (story text for the judge)

Builder: Claude. Branch `story/e2c-fills-to-drive`, from `main`. Story text only, under the owner's rule "keep the
design simple" (real paths only). Sources:
- the owner's decision of 15 Oct 2026 ("A: move to Drive");
- ChatGPT review 105, points 1 and 3;
- the orchestrator's response 131.

## What the story does (docs/stories/E-paper-desk.md, "E2c")

- **Drive:** every paper file that names a contract's price, and every mark, is kept in Drive through A4b's store.
  That is the cash ledger, the desk's fills and events, positions, equity history and scoreboard B.
- **Public:** the repository keeps `journal/<book>/daily_totals.csv` only: date, closed equity, open and closed trade
  counts, and the fill count.
- **One writer:** `DriveAccountSync` replaces `GitAccountSync` behind E3's `AccountSync` port. The daily run is the
  only account writer.
- **Blocked entries:** a session whose run log has no `exits` step blocks the next session's new entries, with one
  alert (review 105 point 3).

## Facts checked in code (strong evidence unless marked)

| Fact | Where |
|---|---|
| Account files committed today hold only the opening rows (no fill yet) | `git ls-files journal`; `journal/book1_rules/account/cash_ledger.csv` |
| The cash ledger holds contract, quoted and fill price per fill | `fno/books/fills.py` `LEDGER_COLUMNS` |
| Equity history holds daily marked equity | `fno/books/account.py:32` `EQUITY_COLUMNS` |
| Home's read model publishes a book's marked equity | `fno/market_read_models/home_inputs.py:50-55` |
| The dashboard contract plans each book's marked `value`, and each open trade's `mark_value` and `unrealised`, as public | `contracts/omenix-dashboard/api/schemas/fno-paper-trades.yaml` |
| The scheduled routine starts in a fresh container, so a stop is seen only in the committed run log | reasoning (how the scheduled sessions run) |

## Consequence the owner should see

The dashboard's paper-trades view loses its public money figures: book value, marks and per-trade nets become
owner-only. That follows from "per-book daily totals only" (response 131). If the owner wants closed-trade nets
public, they give no bid-ask pair, because their fills are at different snapshots (reasoning). That is the owner's
call, not mine.
