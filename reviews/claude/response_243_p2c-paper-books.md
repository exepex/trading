# Response 243: P2c, the paper books page (`paper_trades`, contract 2.11.0 `FnoPaperTrades`)

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

## Part 2: closed trades and shadows (mapped as the screens lead answered, 16 Oct; `paper_trades_closed.py`)

- **Strategy label "Strategy <k>, version <n>", never the version tag** (screens lead, strong evidence: the only
  playbook name, `example-sc-iv-rich-no-event`, spells its entry filters). k is the order in which the strategy's
  name first appears in `playbook/registry.csv`, which is append-only with a history check (`fno/playbook/cli.py`), so
  k never moves. A trade or shadow whose strategy has no registry row stops the page, named; never a guessed label.
- **Structure in plain words**, the shape only, never a strike rule (SC's 2% offset and the widths stay off the
  screen). The table is at the top of `paper_trades_closed.py`, not in `fno/constants.py`: that file is at 348 of its
  350 lines, and these are this page's display words (CLAUDE.md: module-specific text is named at its module's top).
  Words sent to the screens lead for a beginner check. A code with no words stops the page, named.
- **Money:** gross, costs and net are C1's `trade_line` (costs = pads + every charge), rounded to the paisa; result
  from net (won > 0, lost < 0, flat).
- **Exit:** the desk's own rule name, the prefix of its `exit_ordered` reason: profit_target is take_profit,
  stop_loss is max_loss_exit, time_exit is time_exit; a settlement fill is expiry_settlement; anything else
  (protection unverified, an unwind) is other. safety_stop is never sent (no S1 stop exists).
- **Fills:** null for every trade until E8 records all three reaction times (E8 is not merged; its branch has the
  60-minute view only, and its outcome words differ from the contract's slugs: the screens lead takes that up).
- **Shadows:** each its own card, "Strategy <k>, version <n>", label shadow (B0's measurement label waits for
  R-factory), marks from its own account. None exists today.
- **brake.loss_from_high** now counts the closed trades: a losing trade moves it by exactly its net loss (test).

## What still fails closed

- **A book's open trade stops the page, named** by book and count, never an amount. Its `mark_value` and `unrealised`
  need the session's per-trade marks, and no record holds them: `AccountWriter.record_equity` has no caller, and the
  desk's marks live only in the run's memory (strong evidence: grep). This needs E3 to write a per-trade mark record,
  or the contract to allow null marks; raised with the orchestrator and the screens lead.
- **Risk (stated plainly):** that stop is the whole publication's (`market_run.py`), until the per-page hold (owner,
  16 Oct; its own story) lands. Home's books already stop the same way on an open trade. Today no strategy is
  approved, so no trade can open yet.

## Privacy (criterion 2)

The accounts are Drive only; they reach this run only through E2c's `download_private_records`, which already stops
the publish, named, when Drive cannot be read (its own tests). A planted value only the account holds reaches the
payload (which goes to Azure only) and nothing else: the build writes no file (the tree is compared before and after),
and the trade stop's message names no amount (tests).

## Tests (`tests/market_read_models/test_paper_trades_page.py`, 12)

Every account figure against the account's own rows and the config; capital before and after a top-up; a book not
opened; a closed trade against C1's trade line, labelled from the registry with no word of its tag; each exit; an open
trade stops the page, named without the amount; a missing registry row or structure stops it; a shadow's own card; a
losing trade moves the brake by its net loss; a planted Drive value reaches no file. 22 blocks, 1,273 pages a day.

## Addendum 1 (16 Oct): rebased on P11 and P2b; judge 248's finding fixed at its root

- **Merged in:** main, and story/p2b-forecast-lab, which carries P11 (judge 257 add. 2 PASS) and the 2.13.0 pin. So
  this branch merges after P2b. Pages a day: 1,275 (23 blocks plus page_holds).
- **Judge 248 (any trade or shadow stopped every page): fixed by the hold, not by a patch.**
  - The reader and the closed-trades module no longer raise `FiguresNotComputed`. They raise the page's own
    `PageCannotBeBuilt(reason)`.
  - The reader returns the page's inputs with `held` set, and the block raises `PageHeld`. Only `paper_trades` is
    held, keeping its previous dated page (`shows: previous_page`). Every other page publishes.
  - A shadow account and a closed trade are now built (part 2), so normal running holds nothing.
  - What still holds the page: a book's open trade (no per-trade marks yet), a trade or shadow whose strategy has no
    registry row, a trade with no known structure, and a brake history C2 refuses.
- **Reasons** are fixed sentences with no digit, so no book id or count. A test checks them against the pinned
  pattern. The open-trade one is the agreed sentence, word for word: "A book holds an open trade, and this page
  cannot mark it for the session yet".
- **Test (judge 248):** a held paper books page in a full MarketRun leaves every other page published, plus
  page_holds, with one alert line.
- **Words:** the structures now read sold or bought iron butterfly, sold iron condor (the screens lead's beginner
  check).
- **Known loss, stated plainly:** the held reason no longer names the book or the trade, so the alert does not say
  which one; neither does the run log. Only the desk's own records (E4's events, Drive) still do; the screen rule
  (no digits) forbids naming it here.

## Addendum 2 (16 Oct): judge 248 addendum 1, B0 is a measurement

Accepted and checked on main: `playbook/b0-monthly-sc-v1.yaml` has `edge_family: measurement`, and
`fno/playbook/measurement.py` (`is_measurement`) is R3's one source for that label. Every shadow was labelled
`shadow`, so from about 19 Oct B0 would have shown as a candidate, against owner decision 1 A ("never promoted").
- Each shadow's label now comes from its own version file through `is_measurement`: `measurement`, else `shadow`.
  The file is read through D1's loader (`PlaybookVersions`, wired in `wiring.py`).
- A version file that cannot be read holds the page ("A shadow account's version file cannot be read, so it is never
  given a label"); the label is never guessed.
- Test: B0 with its real version file and the real registry is "Strategy 1, version 1", measurement. A candidate is
  shadow, and an unreadable file holds the page.
