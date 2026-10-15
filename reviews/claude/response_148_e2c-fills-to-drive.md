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

## Answer to judge 148

| Finding | Accepted? | Change |
|---|---|---|
| Ruling: the dashboard read model is not public | **accepted** (I had checked it too: `PostgresPublisher` on `FNO_DB_URL`; the only GitHub commit is `PublicationInputsFile`, provenance hashes only) | The dashboard-contract bullet and criterion 6 are dropped. A Known-limits line says no later job may commit these fields to a public repository |
| Must-fix 1: the committed private packs would copy the downloaded account files every day | **accepted (strong: `private_pack.py`, `daily_steps.py:85`, `pack_store.py:28`)** | I chose the simpler option: `private.json` goes to Drive beside the account, and only its `.sha256` stays public (D3 records the pack's hash already). Leaving the account text out of the pack would change what the books read. The private packs are added to criterion 1's scan |
| Should-fix 1: daily readers missing | **accepted** | Named: the daily run, Book 1 with its pack, C4's `LedgerAccounts` (its cutoff filter keeps replays valid on the Drive copy), T1's card, E6, scoreboard B, Home, E1's account command and the shadow books. One shared download runs at the start of each run or command |
