# Response 239: P2c, the paper books page (`paper_trades`, contract 2.11.0 `FnoPaperTrades`), part 1: the accounts

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (P2 page builder), branch `story/p2c-paper-books`. Story:
`docs/stories/W3-fno-screens.md`, Part 1, build step 3. Lane 1. For judge D. The branch also pins contract 2.11.0 at
dashboard main e425aea (orchestrator: "Pin 2.11.0 together with your P2c work").

## The 2.11.0 pin (strong evidence: byte copies, `market contract-check`)

Five files changed, none added or removed: `fno-budget.yaml`, `fno-card.yaml` (the new required fields; neither page
is built yet), `fno-paper-trades.yaml` (only `pause_at`'s catalog note), `openapi.yaml` (the version and its 2.11 note)
and `examples/fno-screens.json`. contract-check: "pinned W11 contract 2.11.0 (commit e425aea33c4b): same as the
dashboard's".

## What part 1 builds (strong evidence: code and tests)

- **One account per book, never added across books** (`paper_trades_inputs.py`, `paper_trades_block.py`):
  - the marks: value, cash, open_trades and as_of come from the book's last `equity_history.csv` row on or before
    the session, the same source as Home's books (P10);
  - opening_value is the capital in force that day (opening plus top-ups written by the end of the day, E1b);
  - a book not opened yet shows its opening balance (config `paper_account_rs`).
- **Limits from the C5 profile, never typed:** `open_risk_cap` = `open_risk_cap_rs` (150,000) and `brake.pause_at` =
  `drawdown_brake_rs` (120,000), read through `profile_settings`.
- **brake.loss_from_high:** C2's own figures (`closed_equity_series`, `high_water_mark` with the owner's restarts,
  `equity_at`), so it is the loss the brake measures. It is 0 today: no book has closed a trade. A brake history C2
  refuses (a restart row on a day the brake was not in force) stops the page, named.
- **Empty lists:** shadows, open and closed are empty, which is the real state: 3 books, 0 trades, no shadow account.

## What part 1 does not build, and fails closed on (reasoning only: the mappings are with the screens lead)

- Any trade (open or closed, filled on or before the session) or any shadow account stops the page with
  `FiguresNotComputed`, named by book and count, never an amount. That is the same stop Home's books use for an open
  trade.
- **Risk (stated plainly):** that stop is the whole publication's (`market_run.py`: every page stays at its previous
  publication). So the trade mappings must land before a book's first paper trade, or the dashboard stops refreshing
  that day. Today no strategy is approved (Home: "no approved strategy" each day), so no trade can open yet. Home's own
  open-trade stop carries the same risk already.
- The ten mapping questions sent to the screens lead (16 Oct):
  1. marks;
  2. the entry maximum loss;
  3. the brake;
  4. strategy names, which are version tags only today;
  5. plain-word structures, which exist only as codes;
  6. exit names;
  7. E8's fills, unmerged;
  8. shadow labels;
  9. days to expiry;
  10. LM1's monitor fields.
  Part 2 builds them once answered.

## Privacy (criterion 2)

The accounts are Drive only; they reach this run only through E2c's `download_private_records`, which already stops
the publish, named, when Drive cannot be read (its own tests). A planted value only the account holds reaches the
payload (which goes to Azure only) and nothing else: the build writes no file (the tree is compared before and after),
and the trade stop's message names no amount (tests).

## Tests (`tests/market_read_models/test_paper_trades_page.py`, 6)

Every account figure against the account's own rows and the config; capital before and after a top-up; a book not
opened; a trade stops the page, named without the amount; a shadow stops it; a planted Drive value reaches no file.
22 blocks, 1,273 pages a day.
