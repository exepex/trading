# Epic E: the daily paper desk for three books

Roles: head of desk, F&O trader, risk manager, portfolio manager, data engineer. Goal: every trading day at about
15:00, each of the three books (12.1) decides independently on the same data, its decision is committed, and all
timely decisions are filled by one fill model against one execution snapshot, each in its own paper account (design
sections 4, 8, 9, 12.4-12.6, 13.5). Story template, definition of done and the full story index:
`docs/IMPLEMENTATION_PLAN.md`.

Book names used everywhere: `book1_rules` (pure rules), `book2_hybrid` (AI inside the authority envelope),
`book3_ai` (fully AI under the constitution).

---

## E1. Paper accounts per book, with a single-writer lock

**Repository:** trading

**Description:** As the risk manager, I want each book to have its own Rs 5 lakh paper account that only one process
can write at a time, so that books never share money, positions or results, and a restart or a second run can never
double a fill.

**Context and why:** Design 12.6: separate Rs 5 lakh paper accounts per book. Moved here from the removed story E4
(clean-slate design, section 5): an operating-system lock with a lease per account, and safe restart. Three books, a
scheduled run, manual runs and retries can otherwise write the same account at once.

**Scope.** In: account files, positions, cash, closed and marked equity per book, the lock, restart. Out: deciding
(E5, F5, F6), filling (E4), risk rules (C2).

**Expected design:** `fno/books/account.py`: `PaperAccount(book)` stored under `journal/<book>/account/`
(`positions.json`, `cash_ledger.csv` append-only, `equity_history.csv`); definitions as C2 (closed equity, marked
equity, available cash). `fno/books/lock.py`: `AccountLock(book)` holding an exclusive operating-system lock on
`journal/<book>/account/.lock` with a lease (holder, start, expiry) written inside; a lock is released on exit or when
its lease expires and its holder process is gone; never while the holder is alive. Every write to an account goes
through `with AccountLock(book):`.

**Acceptance criteria:**
1. Each book starts at Rs 5,00,000 cash with no positions; the starting state is committed once.
2. Two processes writing the same book at the same moment: exactly one gets the lock, the other exits without writing
   (test with two processes).
3. Two books written at the same moment both succeed (different locks).
4. A lock left by a crashed process is released when its lease expires and its holder is gone; never while the holder
   is alive (test).
5. A restart after an interrupted write neither loses nor repeats a fill: writes are idempotent by fill ID (test kills
   the writer mid-way and restarts).
6. No code path lets one book read or write another book's account files (test: the account object refuses a path
   outside its book).

**Test plan:** multi-process lock tests; crash and restart tests; idempotency tests.

**Judge verifies:** starts two writers on one book and two on different books; reads the results.

**Depends:** C1 · **Size:** M · **Status:** done (judge passed, `reviews/judge/judge_1_e1_paper_accounts.md`)
`reviews/claude/response_37_2026-10-13-e1-paper-accounts.md`; awaiting judge)

---

## E1b. Capital top-up: the three books move to the Rs 20 lakh account

**Repository:** trading

**Description:** As the risk manager, I want each book's paper account to receive a dated capital top-up entry that
brings it to the owner's account size, with every reader treating it as capital (never as profit and never as a
closed-equity gain), so that the three books opened at Rs 5 lakh on 13 Oct 2026 can trade on the Rs 20 lakh account
without rewriting their history.

**Context and why:**
- Owner, 14 Oct 2026: "Paper account Rs 20 lakh, Rs 10,000 maximum loss per trade" (`docs/DESK_DECISIONS.md`).
- Owner, 15 Oct 2026, "2 B": "The three paper books move to Rs 20 lakh by a dated Rs 15 lakh top-up entry"; "A new E1
  entry kind; the 13 Oct opening rows stay as written" ("History is never rewritten").
- Story C5 (risk buckets, branch `story/c5-risk-buckets`) refuses every trade of a book whose capital differs from its
  profile's `paper_account_rs` (rule `paper_account`). The three committed books opened with Rs 5,00,000 on 13 Oct, so
  every book trade is refused until this story runs.
- Judge 105 minor 4: the paper-account rule must read the opening plus top-ups, and a top-up must never raise the
  drawdown brake's high-water mark (it is capital, not a gain).
- Brake scope (orchestrator, owner away, 15 Oct 2026, owner to confirm): the brake and caps apply per book, each book on
  its own Rs 20 lakh. So each book is topped up separately.

**Scope.** In:
- a new cash-ledger entry kind `capital_top_up` (constant in `fno/constants.py`), appended once per book by E1's writer
  under the book's lock, with its amount and the cash after it, and `filled_at` = the **write instant**, time-zone
  aware in IST (never a bare date: judge 110); never edits or removes an earlier row;
- the account's **capital** at an instant: the opening row plus every top-up written at or before that instant. For a
  decision it is the decision cutoff (E1, C2 and C4 alike), so a top-up written after a session's 15:00 decision never
  counts for that decision, live or in a replay; P10's end-of-day figures use the day's end. The account's cash,
  closed equity and marked equity include it. Only capital is cut at the decision time: fills are not, so rebuilding
  a whole account from the ledger as of a past time is not supported (ChatGPT review 111: the live run never shows
  an earlier decision a later fill, and Book 1 replays its decisions from stored inputs);
- every reader of the opening cash moved to capital:
  - E1's state and `positions.json`;
  - C2's risk view (closed-equity series, paper-account rule);
  - C4's own ledger read (its capital, cash, closed-equity series and paper-account check);
  - P10's Home figures (profit and loss against capital as of each day);
  - S2's reconciliation (cash change against capital);
- a command `python -m fno account top-up [--book ...]` that tops each book up to `risk.profiles.books.paper_account_rs`.
  The amount restores **capital**, not cash or equity: amount = target − capital, so realised losses before the
  top-up stay losses. It is computed, never typed. It is refused when the book is already at size, above it, or not
  started, or when the book has open positions (its marked equity would need marks). The equity history gets that
  day's row. The target is a setting: raising it later would allow a second top-up, which is a lane-1 config change
  and an owner decision, and the command's output line names any top-up beyond the first as "a further top-up";
- run once per book after the judge's PASS and the merge (lane 1: `journal/`, judged as data). Who runs it: the
  builder, per the owner's rule of 15 Oct 2026 ("1 B": builders run their own commands), accepted by judge 110
  addendum 1 under three conditions:
  1. from a clean checkout of `main` at or after the merge commit, with `python -m fno account top-up` only: no branch
     build, no hand edit; the output lines and the commit are recorded in the claims;
  2. the data commit holds only the command's own writes, per book: one appended `capital_top_up` row in
     `journal/<book>/account/cash_ledger.csv`, the rebuilt `journal/<book>/account/positions.json`, and that day's row
     of `journal/<book>/account/equity_history.csv`; no other file;
  3. run outside 14:50-15:30 IST on a session day, so it never contends with the desk for the account lock.

Out:
- withdrawals and any capital decrease;
- top-ups of the Manual account (none exists; MA1);
- S2's benchmark returns per rupee of capital (S2 change; noted: a capital flow must not count as return);
- any change to a frozen file.

**Design:**
- `fno/books/fills.py`: `top_up_row(entry_id, written_at, amount, cash_before)` (`written_at` time-zone aware);
  `CAPITAL_KINDS = (opening, top-up)`; fills stay `FILL_KINDS` only, so no position or trade ever includes a top-up.
- `fno/books/account.py`:
  - `PaperAccount.capital(at: datetime | None = None)`: the opening plus top-ups written at or before `at` (all when
    None; the opening row, dated by day, counts from its day). It replaces `starting_cash()`.
  - `AccountWriter.top_up(written_at, target)`: appends `top_up_<IST date>` for `target − capital`, refused as in
    Scope. Idempotent: the same day's entry already recorded returns False. Writes that day's equity row from the
    unmarked state (exact, as the book is flat).
- `fno/books/equity.py`: `account_state(capital, ...)`; the state's field renamed from `starting_cash` to `capital`,
  every reader updated.
- C2 `fno/risk/book_view.py`: the closed-equity series is the account's capital at the decision cutoff (the decision
  day at `DESK_DECISION_TIME`, IST) plus the cumulative closed profit and loss; the state's capital is the same. The capital is constant across the series, so a top-up shifts the whole series
  and never creates a new high; the brake measures drawdown of profit and loss only. `PaperAccountSize` compares
  capital.
- C4 `fno/checks/validity_account.py` (its own read, no E1 code): capital rows are the opening row (row 0) and every
  top-up row written at or before its cutoff (by the row's time-zone-aware instant). They count in cash and capital,
  never in trades: trades are read only from fill and settlement rows, wherever a top-up row sits between them. The
  closed-equity series uses the capital at the cutoff throughout, and the paper-account check compares that capital.
- P10 `fno/market_read_models/home_inputs.py`: `pnl = marked equity − capital(day)`.
- S2 `fno/scoreboard/reconcile.py`: the cash change is measured against capital.
- Wiring: the command in `fno/books/cli.py`, the target from `fno/composition.py` (`paper_account_rs`).

**Acceptance criteria:**
1. A top-up appends exactly one `capital_top_up` row to a started, flat book whose capital is below the books' size:
   amount = Rs 20,00,000 − capital (Rs 15,00,000 for a Rs 5 lakh book; it restores capital, not equity: a book with
   Rs 10,000 of realised losses still gets Rs 15,00,000 and keeps the loss), `cash_after` = cash before + amount,
   `filled_at` = the write instant in IST with its offset; every earlier row is byte-for-byte unchanged (test reads the
   file before and after).
2. Refusals, each with a named reason and nothing written: a book already at Rs 20 lakh (a second run: "already at
   size", idempotent), a book above it, a book not started, a book with an open position, a write without the book's
   lock.
3. Capital is the opening plus top-ups written at or before an instant: for the 13 Oct book topped up at 17:00 IST on
   session day T, capital is Rs 5,00,000 at T 15:00 (the decision cutoff, live and in any replay) and Rs 20,00,000 at
   T + 1 15:00; a top-up at 10:00 on T counts at T 15:00. Cash and closed equity include it; no trade, fill, position
   or C1 ledger line contains it (tests on E1's state, `positions.json`, `trade_positions` and C1's three ledgers).
4. C2 after the top-up: `paper_account` passes for a topped-up book and still refuses a Rs 5 lakh book; the drawdown
   brake is unchanged by a top-up:
   - a book Rs 1,30,000 below its high stays braked after a Rs 15 lakh top-up;
   - a book at its high does not get a higher high-water mark from it;
   - closed equity minus the high-water mark is identical before and after the top-up (tests at, under and over the
     Rs 1,20,000 brake).
5. C4 reads the same ledger independently and agrees with C2 on capital, cash, the brake and the paper-account check,
   at the same cutoff (test on one ledger: a 17:00 top-up on T refuses T's 15:00 decision in both and passes T + 1's).
   A top-up row between two fills is capital, never parsed as a fill (test). C4's independence test still passes.
6. P10 Home: on days before the top-up the book's `pnl` is 0 against Rs 5 lakh; on and after it, 0 against Rs 20 lakh;
   never −Rs 15 lakh (test over a date range).
7. S2's reconciliation still holds to the rupee with a top-up in the ledger (test).
8. The command tops up all three books (or `--book`), prints one line per book (topped up by Rs X at <instant> /
   already at size / refused: reason; a top-up when one is already recorded is named "a further top-up"), and exits
   non-zero if any book was refused.
9. No code path edits or deletes an earlier ledger row; a top-up never moves a position or touches another book's
   account (book firewall test).

**Gap list:**

| Requirement (source) | Criterion or reason out |
|---|---|
| Books move to Rs 20 lakh (owner 14 Oct; "2 B") | 1, 8 |
| A dated top-up entry, a new E1 entry kind ("2 B") | 1 |
| The 13 Oct opening rows stay as written; history never rewritten ("2 B") | 1, 9 |
| Rs 15 lakh per book ("2 B") | 1 (computed as size − capital, which is Rs 15 lakh for each committed book) |
| Paper-account rule reads opening plus top-ups (judge 105 minor 4) | 4, 5 |
| Top-up never raises the brake's high-water mark (judge 105 minor 4) | 4, 5 |
| Brake and caps per book (orchestrator, owner to confirm) | 1 (each book topped up separately), 4 |
| Single-writer lock and book firewall (E1) | 2, 9 |
| Point in time: a top-up counts only from its write instant, in E1, C2 and C4 (judge 110) | 1, 3, 5 |
| The amount restores capital, not equity (judge 110 minor 1) | 1 |
| A second top-up only by raising the setting: owner decision, lane 1 (judge 110 minor 2) | 8 (named in the output) |
| Capital flows are not returns (S2 benchmarks, design 03 change 4) | out: S2's change; recorded here so S2 inherits it |
| Withdrawals | out: no owner decision |

**Test plan:** `tests/books/test_top_up.py` (criteria 1-3, 8, 9); C2's `tests/risk/test_top_up_brake.py` (4); C4's
`tests/checks/test_validity_top_up.py` (5); P10 and S2 tests extended (6, 7). Every criterion broken on purpose once
(`PYTHONDONTWRITEBYTECODE=1`).

**Judge verifies:** tops up a copy of the three committed books and diffs the ledgers; plants a brake case (a book
Rs 1.3 lakh down) and checks that the top-up leaves it braked in C2 and C4; replays a 15:00 decision of the day of a
17:00 top-up in C2 and C4; runs Home over the top-up day.

**Depends:** E1, C1, C2, C4, C5 (the `paper_account` rule and the books profile), P10, S2 · **Size:** S · **Status:**
story text PASS (judge 110 addendum 1, 9e426e8); code built on `story/e1-topup` after C5's merge, judge
pending; the real-journal run after the merge (claims: `reviews/claude/response_110_e1-topup.md`, addendum 2)

---

## E2. Common market pack and book-private packs

**Repository:** trading

**Description:** As the head of desk, I want the day's shared market data frozen in one hashed pack and each book's
own state in a separate hashed pack, so that all books decide on identical market data and no book ever sees another
book's positions, decisions or memory.

**Context and why:** Design 13.5 steps 1-2 (ChatGPT review 24): the **common market pack** holds market observations
(daily files, quotes, VIX), session and event data, the common opportunity set for scoreboard A, and each item's
source and availability time, and **no** book's decisions, positions, P&L, findings or memory. A **book-private
pack** holds that book's account, positions and open exits, its own past decisions, its frozen playbook and envelope
(Book 2) or constitution and strategy registry (Book 3), and only the sources its version allows. Both hashes are in
every decision (D3). Firewall: 12.6.

**Scope.** In: pack builders, schemas, hashing, commit, the common opportunity set. Out: the decisions (E5, F5, F6).

**Expected design:** `fno/desk/packs.py`: `build_common_pack(day, cutoff) -> CommonPack` and
`build_private_pack(book, day) -> PrivatePack`, written to `journal/packs/<date>/common.json` and
`journal/<book>/packs/<date>/private.json` with SHA-256, then committed. **Common opportunity set:** every
(approved strategy, expiry) eligible today under its playbook version, plus a "no trade" opportunity, computed by code
from the playbooks (D1) so that all books are scored on the same set (S3). Source contract: each pack item lists its
source and availability time; an item available after the cutoff is refused. A private pack contains only paths under
`journal/<book>/`, `playbook/` (Book 2's own versions) or `book3/` (Book 3).

**Acceptance criteria:**
1. The common pack contains no field from any `journal/<book>/` path (schema test plus a test that plants a position
   and confirms it is absent).
2. A private pack never contains another book's data (test for each pair of books).
3. Building a pack twice from the same inputs gives byte-identical files and the same hash.
4. An input with an availability time after the cutoff is refused with its name.
5. The common opportunity set equals a hand computation on fixture playbooks and data.

**Test plan:** schema tests; leak tests; determinism tests.

**Judge verifies:** rebuilds one day's packs from committed inputs and compares hashes; greps the common pack for any
book field.

**Depends:** A3, A4, A6, A7, D1, E1 (D4 and D5 for the private packs of books 2 and 3) · **Size:** M · **Status:** done: judge 72 PASS (be9bc5e; delta b2749a6), merged b4f1e1b (claims: `reviews/claude/response_74_e2-market-pack.md`)

---

## E2b. Derived quote figures only in the committed packs and desk records

**Repository:** trading · **Lane:** 1 (the paper desk's committed records, the fill records E6 scores, a commit rule)
· **Branch:** `story/e2b-derived-packs` · **Claims:** `reviews/claude/response_118_e2b-derived-packs.md`

**Description:** As the owner, I want the paper desk's committed files (the daily common pack, the 15:15 capture
record and the paper fill rows) to hold no raw Groww quote values beyond the one price each paper fill must name, so
that the public repository never republishes Groww's bid, ask or quantities, while every book still decides and fills
on exactly the same, hash-proven quotes kept in Drive.

**Context and why:**
- Owner, 15 Oct 2026 (`docs/DESK_DECISIONS.md`, "8 A"): "The daily packs keep only derived quote figures; raw bid/ask
  stays in Drive, before the paper desk goes live". Changes E2's common pack (`fno/desk/snapshot_inputs.py`) and what
  E3 commits, through a lane-1 story before E3 goes live. Owner "6 A" (same day): raw Groww quotes go to Drive only
  (story A4b, branch `story/a4b-quotes-drive-only`, not merged).
- **Finding that shaped this story (builder, 15 Oct; strong evidence, tested):** the owner's example figures, the mid
  price and the bid-ask spread in %, give the raw quotes back exactly: mid = (b+a)/2 and s = (a-b)/mid, so
  a = mid(1+s/2) and b = mid(1-s/2). Option prices sit on 0.05 ticks, so even with s rounded to 2 decimals bid and ask
  were recovered exactly in 648 of 648 synthetic cases. Committing them per contract would meet "8 A" in form only.
- **Decision (orchestrator for the owner, who was away; response 113, 15 Oct 2026): option B.** The committed common
  pack holds no per-contract quote figure; it keeps the snapshot's identity and hashes, counts, the NIFTY spot, India
  VIX and NSE's futures levels. Readers keep reading the raw rows through the hash-checked quote store, as Book 1
  already does; books 2-3's per-contract inputs are decided when they trade (F5, F6). Fills: drop `quote_bid` and
  `quote_ask`; E6 reads the touch from the hash-checked execution snapshot; the fill price stays, and nothing beside it
  may reveal the other side. Add a commit guard.
- **Today (main at c428867):** `SnapshotInput` copies every option row's `bid`, `ask`, `bid_qty`, `ask_qty`, `valid`,
  `invalid_reason`, `spot` into `journal/packs/<day>/common.json` (`fno/desk/snapshot_inputs.py:20`, `:61-68`), which
  the daily run commits (`fno/desk/daily_steps.py:80-85`, `daily_run.py:76-81`); E3's 15:15 capture commits the raw
  quote CSV with its sidecar (`fno/desk/execution_capture.py:49`); E4 writes `quote_bid` and `quote_ask` into
  `journal/<book>/account/desk_fills.csv` (`fno/desk/records.py:29`, `:64`). No pack has been committed yet (no
  `journal/packs/`); the desk is not live (E3, judge 82).

**Readers of what changes (each must keep working):**

| Reader | Reads today | After E2b |
|---|---|---|
| C3 spot check, `fno/checks/market_checks.py:38-47` | each option item's `value["spot"]` (one spot per monthly chain; the two must agree within 0.2%) | the new `spot:<expiry>` items, one per chain, same values and rule |
| C3 schedule and capture checks, `fno/checks/schedule.py:27-33`, `validity_capture.py:21-31` | provenance `snapshot_id`, `csv_sha256`, `meta_sha256` | unchanged |
| Book 1, `fno/books/book1_inputs.py:37-57` | provenance hashes, then the raw CSV through the store | unchanged |
| AI books (F1, G5), `fno/ai/` | the forecast v2 pack `research/forecasts/live_v2/`, not the desk pack | unchanged (that pack is already derived: spot, VIX, futures, ATM IVs) |
| E4 fills, C4 evidence, scorecard marks, scoreboard | the raw snapshot by ID through the store | unchanged |
| E6 half-spread, `fno/scorecard/execution_costs.py:61-63` | `desk_fills.csv` `quote_bid`, `quote_ask` | the touch from the execution snapshot named in the fill row (`snapshot_id`, `quote_contract_id`), read through the store and hash-checked against the row's `snapshot_sha256` |

**Scope.** In:
- the common pack (schema version 2): no `option:` items. In their place, from the same canonical snapshot:
  - `spot:<expiry>`: the chain's NIFTY level (an index level; every row of a chain carries the same value: the 14 Oct
    capture has 22,620.00 on all October rows and 22,621.15 on all November rows). A chain whose rows carry more than
    one spot is refused, naming the expiry, never averaged;
  - `quote_counts`: `expected_contracts`, `recorded_contracts`, `valid_contracts`, `complete` (counts only);
  - unchanged: `india_vix`, `future:<expiry>` (`last`, `volume`: NSE's public levels, A4b's split), `session`,
    `close:<date>`, `event:...`, the opportunity set and the provenance with both hashes;
- C3's spot check reads the `spot:` items;
- `desk_fills.csv` without `quote_bid` and `quote_ask`; E6's half-spread reads the touch from the execution snapshot;
  a fill whose snapshot cannot be read or whose hash differs is reported as "touch unknown" and left out of the
  average, never counted as zero;
- E3's 15:15 capture commits its capture record and the sidecar only, never the quote CSV;
- a commit guard in the desk's committer (`GitCommitter`, used by the daily run and the capture): any path that is a
  Groww quote file (`<quotes folder>/groww/derivatives/quote-snapshots/**/*.csv`) is refused with the path named, and
  nothing is committed;
- tests that a committed common pack and a fill row hold no field named `bid`, `ask`, `bid_qty`, `ask_qty`,
  `quote_bid` or `quote_ask`, and that no value in the pack equals a row's bid or ask by construction (fixture with
  distinct prices).
Out:
- moving the raw quote files to Drive and the store's hash check: A4b;
- books 2-3's per-contract trading inputs: F5, F6 (decided when they trade);
- paper fills showing live strikes in the public journal: put to the owner by the orchestrator (outside E2b);
- the fill price itself, which is one side of one quote by design (E4 criterion 1): kept;
- a failed commit in `fno desk book1` (Book 1's decision, `fno/books/book1.py:74`) still ends in a traceback with no
  alert, as before E2b: that command is not the daily run; a follow-up for the orchestrator;
- **two stated exceptions** (three until story E4c removed the third), put to the owner together with the open
  question of whether paper fills should move to Drive at all (since answered: story E2c keeps the fill rows in Drive):
  1. *an unwound entry* (judge 118 SF1; orchestrator for the owner, response 113): when an entry fails after some legs
     filled (E4 criterion 2), each filled leg is traded back at the same snapshot (a protection bought at the ask and
     sold at the bid; a short already sold at the bid bought back at the ask), and `legging_cost_rs` in
     `desk_events.csv` is the spreads paid. Those rows publish both sides of each unwound contract. Since story E4c it
     is reached only through E4's guard (a fill failing after E4c's entry check passed: a defect, not a market case);
  2. *two accounts on opposite sides* (judge 118 addendum 1, confirmed by a test): E4 fills each account on its own,
     so when one account buys a contract and another sells it at the same execution snapshot (one closing while the
     other opens, or a book and a shadow), their rows together publish both sides of that contract;
  3. *(removed by story E4c)* protection unverified at the opening snapshot: such an entry is now refused before any
     leg fills (`protection_not_sellable`), so nothing is bought and closed at once;
- **known channels outside the fill rows (stated, not changed here; one owner question with the fills-to-Drive
  question):** scoreboard B (`research/scoreboards/B/<date>.json`, `fno/scoreboard/whole_system.py:60`) commits
  `raw_account_net_rs`, which marks open legs at the mid of the same 15:15 execution snapshot the fills used
  (`fno/scoreboard/daily_values.py:44-55`): for a single-leg trade on its entry day, mid = (board net - fill amount) /
  units and bid = 2 mid - ask (recovered exactly in review 2). `journal/<book>/account/equity_history.csv`
  (`marked_equity_rs - cash_rs`, `fno/books/account.py:153`) would leak the same way once anything calls it. Nothing
  is live, so nothing has leaked;
- **removed here (orchestrator decision 42):** the size shown at the touch in E4's no-fill reason ("size N at the
  touch is below M units"), written to `desk_events.csv` and used again in pending-exit reasons; it now reads "not
  enough size at the touch for M units" (`fno/desk/pricing.py:19`);
- **removed here (orchestrator decision 45):** a refused entry's "net entry Rs X at the touch is worse than the
  approved Rs Y by Rs Z" reason and the `shortfall_rs` column of `desk_events.csv`. For a single-leg structure (LC,
  LP in STR1) X is one contract's ask, and the mids are public, so the bid follows; for a spread X less the net at the
  mids gives the sum of half-spreads; and Z with the committed approved limit gives X back. The reason is now the fixed
  text "entry_worse_than_approved: entry price at the touch worse than the approved limit". Schema change:
  `desk_events.csv` loses the `shortfall_rs` column (nothing read it; no `desk_events.csv` is committed yet, the desk
  is not live). If research needs the figure, it goes to a Drive-only record, not git (not built here);
- **removed here (orchestrator decision 48):** the "net Rs X if closed now reaches the target/stop Rs Y" reasons of
  E4's exit rules (`fno/desk/exit_rules.py`), written to `desk_events.csv` as `exit_ordered`. X is worked out at the
  touch of every leg, so if a leg then stays pending, X less the other legs' published close fills gives that leg's
  touch at a snapshot where it did not fill. They now read "profit_target: the net if closed now reaches the profit
  target" and "stop_loss: the net if closed now reaches the stop loss". The "every leg closed; net Rs N" reason stays:
  N is the sum of the trade's published fills;
- **kept, by decision (orchestrator for the owner, response 113):** the per-contract mids and implied volatilities of
  the 14:55 canonical snapshot in Book 1's D3 decision inputs (`fno/playbook/decision_codec.py:15-27`) and C4's
  `snapshot_mid` per leg (`fno/checks/validity_market.py:46`): derived figures the letter of "8 A" allows, which alone
  give neither bid nor ask, and no exact pairing with the 15:15 fills was found;
- NSE's public chain (`research/data/quotes/nse/`): public NSE data;
- the forecast v2 pack and its frozen code (G1 v2): already derived, not touched.

**How it fits with A4b:** E2b merges only after A4b (criterion 3 reads the 15:15 quote file from Drive). Both stories change `fno/desk/execution_capture.py` the same way (commit only what the
repository holds); whichever merges second keeps one version. Before A4b merges, the 15:15 quote CSV stays only in the
run's local quote folder (not committed), so a capture made before A4b cannot be replayed from the repository; the
desk is not live, so no counted day depends on it. After A4b, the CSV is in Drive and every reader gets it through
the hash-checked store. The guard and the derived pack work the same with either store.

**Requirements map (quality rule 2):**

| Requirement (source) | Where |
|---|---|
| Packs keep only derived quote figures; raw bid/ask stays in Drive ("8 A") | criteria 1, 2; per-contract figures left out by decision B |
| ... and what E3 commits ("8 A") | criteria 4, 5 |
| The AI books read the derived pack ("8 A" row) | criterion 7 (they read the derived forecast v2 pack; the desk pack holds nothing per contract) |
| Before the paper desk goes live ("8 A") | criterion 5: the guard stops a live run from committing a raw quote file |
| Raw quotes to Drive only ("6 A") | out: A4b |
| E2 criteria 1-5 (no book data, determinism, cutoff refusals, opportunity set) | criterion 6 (E2's tests still pass on schema 2) |
| E4 criterion 1 (fill price = the snapshot's ask or bid, snapshot hash in the row) | kept; criterion 3 |
| E4 criterion 2 (a failed short leg unwinds the protection, legging cost recorded) | changed by E4c (decision 43): kept only as a guard, so the unwind exception occurs only through it (criterion 3) |
| E6's half-spread paid (criterion 3 of E6) | criterion 3 |
| C3's spot rules (2% from the previous close, 0.2% chain agreement) | criterion 2 |
| One spot per recorded chain (orchestrator's decision 4, review 2 finding 6) | criterion 2 |
| Other committed figures that could reveal a quote (review 2) | Scope "Out": known channels, kept mids (exception 3 removed by E4c) |

**Acceptance criteria:**
1. A common pack built from a canonical snapshot holds no `option:` item and no field named `bid`, `ask`, `bid_qty` or
   `ask_qty`; with a fixture whose bids and asks are all distinct from every spot, count and level, no value anywhere
   in the pack equals any row's bid or ask (test). It holds `spot:<expiry>` per chain, `quote_counts`, `india_vix`,
   `future:<expiry>`, and the provenance's snapshot ID and both hashes; `schema_version` is 2. A day without a canonical
   snapshot is refused on a session day exactly as before (E2, judge 72). A chain with two different spots is refused
   with its expiry (test).
2. C3's spot check gives the same results from the `spot:` items as before from the option items: the 2% limit at,
   just under and just over; the 0.2% agreement at, under and over; no spot (tests). New (orchestrator's decision 4):
   one spot per recorded chain. The chains are those the sidecar asked for (`expiries`; the rows when an older sidecar
   has none). A chain whose rows carry no spot, or that has no rows at all, keeps its `spot:` item with no value, and
   a refused `spot:` item counts as missing; C3 names the chain and fails, so the 0.2% agreement is never skipped
   (tests).
3. `desk_fills.csv` has no `quote_bid` or `quote_ask` column. Apart from the two stated exceptions (an unwound
   entry, only through E4c's guard; two accounts on opposite sides of one contract at one snapshot; the third,
   protection unverified at the opening snapshot, was removed by E4c), no committed desk fill row lets a filled
   leg's other quote side be worked out: tests build E4's outcomes (opened, closed at a later snapshot, pending exit,
   a time rule at the opening snapshot, partial fill) and find that within one account only the unwound legs give
   both sides (since E4c, only through its guard), that unverified protection at the opening snapshot is never bought
   (E4c), and that two accounts on opposite sides do. E6's half-spread from the execution snapshot equals the old
   figure on the same fixtures; a fill whose snapshot is missing or whose hash differs counts as "touch unknown" (excluded from the
   average, never zero), and the scorecard report prints how many fills were "touch unknown"; a settlement row (no
   quote) is excluded as before (tests). **Depends on A4b:** E6 reads the 15:15 quote file from Drive through A4b's
   hash-checked store, so E2b merges only after A4b.
4. E3's 15:15 capture commits its record and the sidecar, never the quote CSV; the record still holds both hashes, so
   the fill can prove which quotes it used (test).
5. The committer refuses, before running git, any commit whose paths include a Groww quote file, naming the path; the
   sidecar `.meta.json` and the `.canonical` marker are allowed; a path outside the quotes folder with a `.csv` name
   is allowed. Paths are compared after resolving them, so an upper-case `.CSV`, a `../` path into the folder and a
   symlink pointing into it are refused too. Because a commit takes the whole index, every commit through `Git`
   (the daily run's committer and the account sync) also checks every staged file after its add: a folder holding a
   quote file, or a quote file staged earlier by anything else, is refused, this add is undone and nothing is
   committed. An account write checks the whole index before it applies anything (judge 118 addendum 2), so a
   refusal there is an `AccountWriteRefused` the fill and exit steps handle ("not filled", an alert, the other books
   and the exits go on) and the journal is untouched (tests: refused, allowed, mixed list, empty list, `.CSV`, `../`,
   symlink, folder, earlier-staged file, account write before apply, the daily run's fill and exit steps). The guard
   is path-based on purpose: the desk's writers never copy or rename a raw file, so the only way a raw quote reaches a
   desk commit is the quote folder itself; a staged deletion there is refused too (test), which is safe because A4b's
   removal of the old raw file is its own commit and never goes through the desk's `Git`. Any failure of the daily
   run's committer (this refusal, a failed pull, a push rejected three times) is raised as `CommitFailed` and handled
   at one place, the run's step (judge 118 addendum 3; decision 44): one alert naming why (the refused file named),
   no later step, nothing committed (a push rejected three times leaves its one commit local and unpushed, which
   refuses every later account write until it is resolved by hand), and `fno desk run` ends on that line with exit
   code 1, never a traceback (tests with the real `GitCommitter` in a run: staged raw file, unreachable origin,
   rejected push; a commit failing inside a step; the command). The alert says "exits not reviewed today" when the
   stop comes before the exits, and gives the hand fix: remove the cause, then rerun `fno desk run` (for a rejected
   push, "the rerun pushes the local commit"). The rerun never repeats a step (judge 118 addendum 4; decision 47).
   Before every commit, the run keeps a local, git-ignored marker (`journal/runs/.pending_commit.json`) holding the
   commit's paths, their SHA-256 and its message. A failed commit leaves the marker, and the rerun's first act commits
   those files exactly as they are on disk. If one is missing or changed, the rerun stops with an alert naming it
   instead, and nothing is regenerated (a later pack or capture, or decisions collected after the deadline, would not
   be what happened). A commit that failed inside a step (D6's registry, the 15:15 capture record) is committed the
   same way; that step is not recorded, so the rerun runs it again. Book 1's version keeper then finds its version
   registered. The capture takes a second snapshot: it is committed beside the first, and the fills read the latest
   one inside the execution window (after `fills_by`, C3 refuses it as outside its window, so nothing fills); none had
   been made. The committer also pushes a commit left unpushed even when it has nothing new to commit
   (tests with the real `GitCommitter`: a stop at the pack and one at the decisions, each committed byte-identical on
   the rerun with one build or collection, one capture and four fills; a tampered pending file; a rejected push of
   the last step, pushed by the rerun).
   **A rerun in a fresh checkout** has no marker and starts from what was committed (judge 118 addendum 6). Fills
   are idempotent by `trade_id` against the committed journal (each account write is pushed by itself), so nothing is
   filled twice, and exits work from the journal's open positions. A decisions step run again after the deadline
   makes every book late: fail closed, visible in the no-decision files, and it loses that day's entries. The pack
   rebuilds byte-identical (E2 criterion 6). Before A4b, the 15:15 quote file is absent in a fresh checkout, so the
   rerun's log can say "not filled" for a trade that was filled (a report mismatch, not a fill); after A4b the
   snapshot is read from Drive.
   **Nothing the run did not make is pushed** (decision 51). Before every push attempt, the raw-quote guard checks
   every file the push would change on origin (`origin/<branch>..HEAD`, deletions too). Before the pull, an unpushed
   commit the run did not make is refused, naming its message and files, through the same handler (one alert). Both
   writers use the same `Git.unpushed()`: account writes refuse any unpushed commit, and the run's commits allow only
   the run's own stuck commit, told apart by the pending marker: its message, and only the marker's files, each with
   the content the marker recorded (SHA-256). A merge
   left by a retry's pull is not counted: what it brings in is checked commit by commit, and its files by the guard
   (tests with real git: a stray raw-file commit refused with origin unchanged, by each layer alone; a stray commit
   without quotes; one copying the run's message with other files; the run's own stuck commit pushed after origin
   moved on, through a merge).
6. E2's own criteria still hold on schema 2: no book data, byte-identical rebuilds, cutoff refusals named, the
   opportunity set unchanged (existing tests, updated only where they name option items).
7. No reader of the committed pack uses per-contract quote figures (a test lists every `option:` lookup in `fno/` and
   finds none); the AI books' pack reader is unchanged.

**Test plan:** unit tests per criterion with positive, negative, boundary and empty cases (quality rule 5); a fixture
snapshot with distinct prices for the "no raw value" scan; the existing E2, E3, E4, C3 and E6 suites; mutations per
criterion (quality rule 4); a real-output sample of a schema-2 pack built from the committed 14 Oct sidecar and its
quote file (quality rule 6; the sample shows the pack's derived items only).

**Judge verifies:** rebuilds a pack from a fixture and scans it for raw values; recomputes one half-spread from the
snapshot by hand; plants a raw quote path in a commit; checks that the 15:15 capture commits no CSV.

**Depends:** A4b (merged first), E2, E3, E4, E6, C3 · **Size:** S · **Status:** story text for the judge's check
(quality rule 1); no code yet

---

## E3. Daily timetable: deadline, execution snapshot and exits

**Repository:** trading

**Description:** As the owner, I want one fixed daily timetable (packs, decisions, a hard decision deadline, one
execution snapshot, fills, exits), so that a slow or failed book can never delay or change the others' fills, and
every timely decision is filled against exactly the same quotes.

**Context and why:** Design 13.5 steps 4-5 (ChatGPT review 24): a book without a committed valid decision by the
deadline gets a committed "no decision (unavailable or late)" and cannot join later; the execution snapshot is taken at
a fixed time whatever any book did; every timely decision is filled against the same snapshot identifier and hash; if
the snapshot is invalid or incomplete, no book opens new risk unless the same retry for all books gives a valid one
before the close; risk-reducing exits run independently (section 9). The 3 pm recorder (A4) already captures a
canonical snapshot in 14:55-15:10.

**Scope.** In: the timetable, the orchestrator, the deadline, the execution snapshot, no-decision records, the exit
review, idempotent runs. Out: how each book decides (E5, F5, F6), the fill model itself (E4).

**Expected design:** `fno/desk/timetable.py` with the frozen times in `config.yaml` `desk.timetable` (this story adds
the key, with tests): pack build (about 14:58, after the canonical quote snapshot), decision deadline (proposed 15:12),
execution snapshot (proposed 15:15, a second recorder capture with its own ID and hash, same A4 rules), fills by
15:20, exit review, publication (P3). For AI books the decision deadline is a **receipt deadline** measured by the
server-side time of the session's output (F1), followed by a **promotion deadline** by which the runner has
validated, checked (C2, C4) and committed it; both come before the execution snapshot. **No new fill without a
completed C4 pass** on the committed decision, for every book. Times are calibrated from measured run times before the first counted day and
frozen in the evaluation protocol (S1). `fno/desk/daily_run.py` (`DailyRun.run(day)`): idempotent per day (a run ID
per day; a second start sees the completed steps and does nothing), each step recorded with its time. A decision
committed after the deadline is ignored and a "no decision (late)" record is committed for that book.
**Across containers (13 Oct 2026, from E1):** E1's operating-system lock protects one machine only; cloud routines run in
separate checkouts. Every account write therefore runs as: pull, write under `AccountLock`, commit, push; if the push is rejected, drop the unpushed local account commit, reset to the new `origin/main` and re-apply the same fills (E1 makes fills idempotent by fill ID; a plain pull merge-conflicts on `cash_ledger.csv`, judge 1). E1's 600-second lock lease can block a retry in the same container inside the fills window: set the lease for E3's timetable, not by default.

**Acceptance criteria:**
1. Given a book that has not committed by the deadline, a "no decision (late)" record is committed for it, and the
   other books' fills happen at the scheduled snapshot unchanged (test with a fake slow book).
2. All timely decisions of a day reference the same execution snapshot ID and hash (test).
3. Given an invalid or incomplete execution snapshot, no book opens new risk; the one common retry is attempted for
   all books together; exits still run (test).
4. Given a non-session day (A1 calendar), nothing runs and nothing fails.
5. Restarting the run the same day after any step repeats nothing already done (test kills it after the fills).
6. Every step's start and end time, inputs and result are written to `journal/runs/<date>.json` and committed.
7. A decision without a completed C4 pass is never filled, for any book (test per book).
   **C4 at the fill (judge 83 ruling):** the fill reads the committed D3 record's completed C4 pass
   (`validity.c4`, written by C4 inside the decision run against the decision's own capture); it never runs C4 again
   against the 15:15 execution capture, whose quotes differ and would fail every leg's price check. A missing, empty,
   failed or edited record is never filled (`fno/desk/recorded_c4.py`).

**Test plan:** an end-to-end test over 5 simulated days with fakes: normal day, slow book, failed snapshot, holiday,
restart after fills.

**Judge verifies:** reads one week of run files and checks the order of commits (decisions before the snapshot, the
snapshot before fills).

**Depends:** A4, A7, C3, C4, D3, E1, E2, E4 · **Size:** L · **Status:** built, not live (judge 82): no `desk run` command, no routine, no E5 orders or exit rules and no C4 yet; branch `story/e3-timetable` (claims: reviews/claude/response_84_e3-timetable.md)

---

## E4. Fill model and exits

**Repository:** trading

**Description:** As the F&O trader, I want paper fills and exits priced only from valid quotes in the execution
snapshot, protection first and last, with pending exits when quotes are missing, so that paper results are as close
to real trading as the data allows and never use an invented price.

**Context and why:** Design 6 (stale prices never fill), 8 (protection bought first and sold last; a missing
protective leg means close; margin tracked apart), 12.6 (same fill model for all books). Groww gives no quote
timestamp, so a fill from Groww data carries `quote_age_unknown` (A4). The research tested next-day-close fills; this
15:00 desk is judged on its own forward record, never assumed equal to the backtest.

**Scope.** In: entry fills, partial fills, exits, pending exits, legging cost, the fill record. Out: choosing what to
trade (deciders), risk (C2).

**Expected design:** `fno/desk/fills.py`: a leg fills at the ask (buy) or bid (sell) of a valid quote (A4 rule) in the
execution snapshot, only if the quote's size covers the lots; otherwise it does not fill. Legs in order: protective
legs first, then short legs; a protective leg that does not fill means nothing opens; a short leg that does not fill
after the protection filled means the protection is sold back at its bid (legging cost recorded) and the trade is "not
opened: partial fill". Exits: short legs bought back first, then protection sold; a leg without a valid quote becomes
a **pending exit** with an alert, retried at the next scheduled snapshot; never a last or stale price. A position whose
protection becomes unquotable is marked `protection_unverified`, blocks new risk for that book and is exited at the
next valid quotes. Every fill row: book, decision ID, snapshot ID and hash, leg, side, price, size, charges (C1),
`quote_age_unknown`.

**Acceptance criteria:**
1. Each fill price equals the snapshot's ask (buy) or bid (sell) for that leg, with the snapshot hash in the row.
2. Partial fill: a failed short leg after filled protection unwinds the protection and records the legging cost; the
   trade does not open.
3. Missing exit quotes give a pending exit and an alert, never a fill from last or stale data.
4. A position whose protective leg is unquotable is marked `protection_unverified`; that book opens no new risk until
   it is resolved; it is recorded closed only when every exit fill is recorded.
5. An exit rule reached closes the trade at the next valid quotes and records it.
6. The fill code never calls an order function (test with a provider fake that fails on any order call).

**Test plan:** unit tests per case with fixture snapshots.

**Judge verifies:** recomputes one day's fills from its snapshot by hand.

**Depends:** A4, C1, C2, E1 · **Size:** M · **Status:** done (judge 68 with addendum 1 PASS; merged 129e4a4; `fno/desk/`, claims `reviews/claude/response_71_e4-fill-model.md`)
`reviews/claude/response_71_e4-fill-model.md`)

---

## E4c. Refuse an entry unless every leg fills and the protection can be sold back, at the entry snapshot

**Repository:** trading · **Lane:** 1 (fills and entries). **Quality rule 9 applies:** after the judge's PASS and
before the merge, ChatGPT reviews it as a second reviewer for money; its points are checked with evidence, and any
change made because of that review returns to the judge before the merge (`docs/JUDGE.md`).

**Description:** As the risk manager, I want the desk to check, before any leg fills, that every leg of an entry can
fill at the execution snapshot and that every protective (bought) leg can also be sold back there. When any check
fails, nothing is bought. The paper account then never pays the spread twice for a trade it cannot hold, and the
public record never shows both sides of a contract from a failed entry.

**Context and why:**
- **Decision 30** (`reviews/claude/response_113_autonomous-decisions.md`), from E2b's builder review (finding R2-1):
  this is E2b's exception 3, "protection unverified at the opening snapshot".
- **Decision 43** (judge 120, should-fix 1; orchestrator, option A): the same check covers every leg's opening side,
  so design 3.2's "all legs fill at one snapshot or none" is met in full.

At the execution snapshot the daily run fills entries first and then reviews exits at the same snapshot
(`fno/desk/daily_run.py`, steps `fills` then `exits`). Two paths waste money today:
1. **Protection that cannot be sold back.** The exit review marks a position `protection_unverified` when a
   protective leg's sell-back does not fill there (`fno/desk/exits.py`, `price_leg(..., leg.side(opening=False),
   ...)`). It then orders the exit at once:
   - short legs are bought back at the ask;
   - other protective legs are sold at the bid;
   - the unsellable protection stays a pending exit.
2. **A leg that cannot fill after the protection is bought.** E4 fills legs in order, protection first
   (`fno/desk/entries.py`). When a later leg does not fill, every leg already filled is unwound at the same snapshot
   (E4 criterion 2), and the legging cost is recorded. The later leg can be a second protective leg or a short leg
   whose bid size is too small.

Both paths are a certain loss of the spread with no purpose. Their fill rows publish both sides of each contract
traded back. On paper every quote of the snapshot is known before the first fill, so both can be refused in advance.
C5 (on its branch, `story/c5-risk-buckets`) counts a trade opened and closed in the same session against the day's
Rs 50,000 new-risk cap ("3 A"). Path 1 therefore also uses up that budget.

**What already refuses, and what does not (strong evidence: code read, existing tests):** A4's validity rule
(`fno/desk/snapshot.py`, `ExecutionQuote.a4_problem`) makes a quote unusable on **both** sides when:
- there is no bid;
- the bid is 0;
- either size is 0 or missing;
- the book is crossed;
- or the contract had no trade today.

So for a protective leg with **no bid, a bid of 0 or no bid size**, the buy side fails too and E4 already opens nothing
(`tests/desk/test_entries.py::test_a_protective_leg_without_a_valid_quote_opens_nothing`). Path 1 is reached only by a
**valid two-sided quote whose bid size is above 0 but below the units held** (E2b's pinned test uses a bid size of 1
against 65 units).

**This changes E4's passed criterion 2 (decision 43, recorded here because lane 1 cannot reopen it silently).**
Criterion 2 ("a failed short leg after filled protection unwinds the protection and records the legging cost") stops
being a normal path. With every leg checked before any fill, no paper partial fill can happen at one snapshot. Why:
- design 3.2's "all legs fill at one snapshot or none";
- decision 30's "a certain loss of the spread with no purpose";
- no partial path left for the public record to show;
- paper fills all happen at one snapshot, so trying leg by leg gains nothing.

The unwind code stays only as a **defensive guard**: if a fill fails after the checks passed (a defect, not a market
case), the filled legs are still unwound as E4 built them, and a test drives that guard. E2b's exception 1 (an unwound
entry) then occurs only through the guard. E6's legging-cost figure, fed by the normal path today, then stays at zero
unless the guard fires; that is stated in E6's report as a known effect, not a change to E6.

**Scope.** In:
- **The entry check, before any leg fills.** In `EntryDesk.enter`, after C3's checks and E4's existing refusals, at
  this execution snapshot:
  - every leg's opening side must fill: a valid A4 quote whose size at the touch covers the units (`price_leg` on the
    opening side: the ask size for a bought leg, the bid size for a sold leg);
  - every protective (bought) leg's closing side must also fill: the same quote's bid size covers the units
    (`price_leg` on the closing side).

  On any failure nothing fills, and the trade is recorded `not_opened` with one reason code:
  - `protection_not_buyable`: a protective leg's opening side fails;
  - `protection_not_sellable`: a protective leg's closing side fails;
  - `short_leg_not_sellable`: a short leg's opening side fails.

  Each reason names the contract and the units. It holds no quote figure.
- **Order of checks, fixed:** C3 data checks → E4's refusals (`refusal`) → the entry check (the legs in E4's order,
  protective first; for each leg its opening side, then for a protective leg its closing side) → E4's entry limit →
  fills. When more than one fails, the first in this order is recorded.
- **The unwind as a guard:** E4's unwind runs only if a fill fails after the entry check passed. It keeps its legging
  cost and its pending-exit path (a leg it cannot trade back stays an exit order).
- **What is recorded:**
  - one desk event (`not_opened`, the reason code, the snapshot ID and hash);
  - no fill row, no E1 ledger row, the account unchanged.

  Neither the reason nor the alert holds a quote figure (no bid, ask or size number), only the contract and the units
  held. This follows E2b's rule that no committed desk record reveals a quote.
- **What is alerted:** one #fno-desk line per refused entry, through the daily run's existing `AlertSender`, of the
  form "F&O paper desk <book>: trade <id> not opened: <reason code> (<contract>, <units> units): information, no
  action" (design 6.5: the first line says what to do). Without the token the daily run's one sender (story O1's
  `ReportedAlerts`) prints it once, "alert NOT sent: <reason> | <text>", and the run goes on.
- **Tests in lane 1 that change on purpose (stated, not loosened):**
  - `test_a_short_leg_failing_after_protection_unwinds_at_the_same_snapshot_with_its_legging_cost`: now expects
    `not_opened` with `short_leg_not_sellable`, nothing bought and no legging cost. Its unwind assertions (order,
    prices, legging cost) move to the new guard test, unchanged;
  - `test_a_second_protective_leg_failing_unwinds_the_first_and_nothing_opens`: now expects `not_opened` with
    `protection_not_buyable` and nothing bought;
  - `test_an_unwind_leg_without_bid_size_stays_as_an_exit_order`: the pending-unwind path is kept and driven through
    the guard (a fill failing after the checks passed), with the same assertions;
  - `test_a_leg_fills_only_when_the_size_at_the_touch_covers_its_units`: the same outcomes, with the new reason text;
  - E2b's `test_unverified_protection_at_the_opening_snapshot_closes_there_the_third_exception`: now expects
    `not_opened` and no row revealing both sides. E2b's story text then lists two exceptions, not three, with
    exception 1 reached only through the guard (edited in E4c's code commit, after E2b merges).

Out (with reasons):
- **A spread-width threshold** ("bid present but the spread is too wide"). None is set; the orchestrator agrees: none
  until there is evidence. No registered source names a maximum spread. A wide spread with enough size can still fill
  and be sold back, so it causes no same-snapshot close. The cost of crossing a wide spread on entry is already bounded
  by E4's entry limit (the net entry at the touch must be no worse than the entry C2 approved). Any width threshold is
  a new rule for the owner to set, with A16's measured spreads as its evidence: open question 1.
- **Short legs' buy-back depth at entry** (the ask size of a sold leg). It causes no same-snapshot close: the exit
  review does not judge price rules at the opening snapshot. A later exit waits as a pending exit (E4 criterion 3):
  open question 2.
- **Later snapshots.** `protection_unverified` on a position opened earlier stays exactly as E4 built it (block new
  risk, alert, exit at the next valid quotes).
- **E8's code.** E8 is not built. Its per-R fills (R = 5, 30 and 60 minutes) inherit this check: its story must call
  E4c's function at each R snapshot (gap list).
- **The size figures in E4's other reasons.** "size N at the touch is below M units" publishes a quote size in
  `desk_events.csv`. That finding went to E2b's current fix round (decision 42 in response 113). E4c's own reasons and
  alerts never carry it (criteria 5 and 7).

**Design:** one small function in a new module `fno/desk/entry_check.py`, for example
`entry_problems(snapshot, legs, units) -> list[str]`, built on E4's `price_leg`, so E4c adds no second pricing rule.
`EntryDesk.enter` calls it at the fixed point; E8 will call the same function. The three reason codes are constants in
`fno/constants.py`. No new composition root and no new wiring, since `EntryDesk` already receives its inputs. The alert
is sent from `fno/desk/daily_steps.py`, which already holds the `AlertSender`.

**Gap list:**

| Requirement (source) | Where |
|---|---|
| Refuse an entry whose protection cannot be sold back at the entry snapshot (decision 30) | criteria 1, 2 |
| Check every leg's opening side too; any failure, nothing bought (decision 43, judge 120 should-fix 1) | criteria 1, 3, 4 |
| E4 criterion 2 (unwind after a failed short leg) | changed by decision 43: kept only as a guard, criterion 8 |
| Exception 3 removed (E2b text and its pinned test); exception 1 only through the guard | criterion 6, criterion 8 |
| "A protective leg that does not fill means nothing opens"; protection bought first and sold last (E4 design, design 8) | criteria 1, 3, 4 |
| All legs fill at one snapshot or none (design 3.2): no leg fills unless every leg can, and no protection is bought that cannot be sold back | criteria 1, 3, 4, 8 (fully covered: no partial fill remains outside the guard) |
| When protection cannot be verified, the desk blocks new risk, alerts and never fabricates a close (design 6.1a) | criteria 1, 7; later snapshots unchanged (criterion 9) |
| Alerts: the first line says what to do (design 6.5) | criterion 7 |
| No quote revealed by a committed desk record or alert (E2b) | criteria 5, 7 |
| Cases: no bid, bid 0, bid present but too wide, a one-leg trade, a multi-leg STR1 structure (orchestrator) | criteria 2, 3; width: Out, open question 1 |
| E2b's exception 2 (two accounts on opposite sides) | unchanged; not an entry failure |
| The size figures in E4's existing reasons (finding) | Out: E2b's fix round, decision 42 |
| C5's buckets and the new risk per day ("3 A") | criterion 10 |
| E8's 5, 30 and 60-minute fills (design 03 item 2) | criterion 11 (one shared check, inherited); E8's code: Out |
| E4 criterion 6: never an order call | criterion 12 |
| Engineering standards (CLAUDE.md) | criterion 13 |

**Cases** (fixture: the short iron fly of `tests/desk/builders.py`, 65 units. The protective legs are 25200 CE and
24800 PE; the short legs are 25000 CE and 25000 PE):

| Case | Quote | Today | With E4c |
|---|---|---|---|
| Positive | every leg valid; each size covering 65 units on its opening side, and each protective bid size too | opens | opens |
| Boundary at | a protective bid size of 65 | opens | opens |
| Boundary just over | a protective bid size of 66 | opens | opens |
| Boundary just under | a protective bid size of 64 | opens, then closed at the same snapshot (exception 3) | `not_opened`, `protection_not_sellable`, nothing bought |
| Negative | a protective bid size of 1 (E2b's case) | exception 3 | `not_opened`, nothing bought |
| Protective ask size short | valid quote, a protective ask size of 64 | `not_opened` (the leg does not fill) | `not_opened`, `protection_not_buyable` (by size), nothing bought |
| No bid | a protective bid empty | `not_opened` (A4: one-sided) | `not_opened`, `protection_not_buyable` (A4 makes the quote unusable both ways), nothing bought |
| Bid 0 | a protective bid of 0 | `not_opened` | the same as no bid |
| No bid size | a protective bid above 0, bid size 0 | `not_opened` (A4: no size) | the same as no bid |
| Second protective leg not buyable | 24800 PE missing | 25200 CE bought, then unwound (legging cost) | `not_opened`, `protection_not_buyable`, nothing bought |
| Short leg's bid size short | a short leg's bid size of 64 (boundaries 64, 65, 66) | protection bought, short leg refused, unwound (legging cost) | at 64: `not_opened`, `short_leg_not_sellable`, nothing bought; at 65 and 66: opens |
| Short leg A4-invalid | a short leg `valid: false` | protection bought, then unwound | `not_opened`, `short_leg_not_sellable`, nothing bought |
| Wide spread, enough size | for example bid 40, ask 71 on a protective leg | opens if within the entry limit | unchanged: no width rule (Out) |
| One-leg trade (STR1 LC or LP) | the bought option's bid size below the units | opens, then closed at once | `not_opened`, `protection_not_sellable` |
| Multi-leg STR1 (SF, SC, BF, the verticals) | any one leg short on its checked side | exception 3 or an unwind | `not_opened`; no leg bought |
| Guard | a fill fails after the entry check passed (test double) | n/a | E4's unwind runs as before: legging cost recorded; a leg it cannot trade back stays an exit order |
| Empty: no protective leg | an order with no bought leg (a naked short) | C4 refuses it before the desk | the check covers only the short legs' opening side; it never replaces C4's refusal, which stays the guard |
| Empty: no quote at all | a protective contract absent | `not_opened` | `not_opened`, `protection_not_buyable` |
| Prices unverified (C3) | any | `refused` before pricing | unchanged (C3 first) |
| Rerun of the same trade | any | the recorded outcome | unchanged |

**Acceptance criteria:**
1. Before any leg fills, the entry check runs at the execution snapshot: every leg's opening side, and every
   protective leg's closing side. Any failure makes the entry `not_opened` with `protection_not_buyable`,
   `protection_not_sellable` or `short_leg_not_sellable`. No fill row, no E1 ledger row; the account is unchanged.
2. Boundaries and structures:
   - a size equal to the units passes; units - 1 is refused; units + 1 passes, for a protective bid, a protective ask
     and a short bid;
   - every leg of a multi-leg structure is checked, and one failing leg refuses the whole structure;
   - a one-leg bought option behaves the same.

   Tested with the fly, and with STR1's codes once STR1 is merged (with the fly alone if it is not).
3. A protective leg that cannot be bought (no quote; A4-invalid: no bid, bid 0, no size, crossed, no trade today; or
   an ask size below the units) gives `protection_not_buyable` before any leg fills, including a later protective leg.
   There is no unwind and no legging cost. A short leg that cannot be sold gives `short_leg_not_sellable` in the same
   way.
4. The order of checks is C3 → E4's refusals → the entry check (legs in E4's order: opening side, then a protective
   leg's closing side) → the entry limit → fills. A case failing two checks records the first. A rerun returns the
   recorded outcome.
5. The refusal's reason and its event hold no quote figure: no bid, ask or size number (a test reads
   `desk_events.csv` and finds none of the snapshot's figures in the row).
6. Exception 3 is gone. E2b's scenario (the fly with a wing's bid size 1) gives `not_opened`, and no committed row
   reveals both sides of any contract. E2b's story text lists two exceptions, exception 1 only through the guard.
7. One #fno-desk alert per refused entry through `AlertSender`, ending "information, no action", and holding no quote
   figure (a test checks the sent text against the snapshot's figures). Without the token O1's `ReportedAlerts` prints
   it exactly once, "alert NOT sent: <reason> | <text>", and the run continues to its exits (tests with a fake sender
   and with none).
8. Guard (E4 criterion 2, changed by decision 43): if a fill fails after the entry check passed, E4's unwind still
   runs. Legs are traded back short first and protection last, the legging cost is recorded, and a leg it cannot trade
   back stays an exit order (tests drive the guard with a test double; the moved assertions are unchanged).
9. Later snapshots: a position opened earlier whose protection becomes unquotable is still marked
   `protection_unverified`, blocks new risk and exits at the next valid quotes, exactly as before (existing tests stay
   green unchanged).
10. C5: a refused entry writes no E1 ledger row, so `RiskBook.session_trades` (built from E1's ledger) does not count
    it toward the Rs 50,000 new risk of the day. Within the decision run that chose it, D2's same-session choice
    already counted it, which is conservative. Tested once C5 has merged; until then, by the empty ledger.
11. E8 hook: the check is one function (`fno/desk/entry_check.py`) that `EntryDesk` calls. A test calls it on a second
    snapshot to show it depends only on the snapshot it is given, so E8 can apply it at each R.
12. Never an order: the provider fake fails on any order call (as E4 criterion 6).
13. Engineering: constants in `fno/constants.py`, no file or class over 350 lines, interfaces unchanged, ruff, the
    import check and the full suite pass.

**Test plan:** unit tests with fixture snapshots (`tests/desk/builders.py`):
- each case of the table, at the boundaries (64, 65 and 66 units: a protective bid, a protective ask, a short bid);
- the guard driven by a test double;
- the five existing tests named in Scope, changed as stated, with no assertion dropped (the unwind assertions move to
  the guard tests).

The builder also follows quality rules 3-6: two independent review agents, a planted break per criterion, and a real
refusal sample from a dry run on a fixture snapshot (no live strikes).

**Judge verifies:**
- plants a size of units - 1 on each checked side of each leg in turn, and on a one-leg trade;
- that no fill row is written, and that neither the event nor the alert holds a quote figure;
- that the guard still unwinds with its legging cost and its pending path;
- that later-snapshot `protection_unverified` is unchanged;
- the order of the checks, the alert with and without a token, and that E2b's third exception is gone.

**Depends:** E4 (merged), A4, **E2b (its code must merge first: E4c changes E2b's pinned test and its story's
exceptions)**, C5 (criterion 10's test), STR1 (criterion 2's codes; the fly covers the rest if STR1 has not merged) ·
**Size:** S · **Status:** code on `story/e4c-protective-leg-refusal`, for the judge (text PASS judge 120 add. 1;
ChatGPT review 104 accepted the text; claims in `reviews/claude/response_184_e4c-entry-check.md`).

**Open questions for the owner (reasoning only, no change in E4c):**
1. Should a maximum entry spread exist (for example, a ratio of the spread to the premium)? E4c sets none. The
   evidence for a value would come from A16's recorded spreads.
2. Should a short leg's buy-back depth (ask size) also be required at entry? It causes no same-snapshot loss, but an
   exit may wait for depth.

**Known limits (ChatGPT review 123, response 192; text only, no code change):**
- **Shared displayed size.** `entry_problems` checks one entry's legs on their own. Two entries of the same book on
  one contract at one snapshot could each pass against size they would have to share. This predates E4c. Book 1
  trades nothing today (no approved strategy), but its orders are every traded opportunity of the day
  (`fno/books/book1_orders.py`), so two approved strategies whose legs share a contract could reach it. Fixed by story
  E4d (orchestrator, 15 Oct 2026): a book's entries at one snapshot are checked together.
- **One immutable snapshot.** The check and the fills read the same recorded snapshot, so the order book cannot
  change between legs. A real legged entry can meet a different book at each leg; this model cannot show that.

---

## E4d. A book's entries at one snapshot share its displayed size: the later one is refused, never over-filled

**Repository:** trading · **Lane:** 1 (fills and entries). **Quality rule 9 applies** (ChatGPT after the judge's PASS).

**Description:** As the risk manager, I want a book's entries at one execution snapshot to be checked against the
displayed size *together*, so that two trades on the same contract never both fill against size only one of them
could have taken.

**Context and why:** ChatGPT review 123 (Q2) and E4c's first Known limit; orchestrator, 15 Oct 2026 (after response
192): "it gets fixed, not just listed".
- `entry_problems` (E4c) checks one entry's legs on their own. `DeskSteps.fill` loops over a book's orders at one
  snapshot, so two entries needing 65 units each of one contract both pass against a displayed size of 100, and both
  fill: 130 units at a touch that shows 100.
- **This is a real path (code read, strong evidence):** Book 1's orders are every traded opportunity of the day
  (`fno/books/book1_orders.py`). Two approved strategies near ATM (for example SF and BF on the monthly expiry) share
  their short strikes.
- Paper only: an over-fill inflates the book's results by fills that could not have happened at that quote.

**Scope.** In:
- **The units a book has already taken at this snapshot** come from its own desk records: every fill row with this
  `snapshot_id` and this snapshot's SHA-256 (so a same-named snapshot of another day never counts), whatever its action
  (an unwind's closing fills on the guard path included), summed per (contract, touch side): a buy takes ask size, a
  sell takes bid size (judge 201). For each protective leg still held from an entry at this snapshot, its sell-back need
  (the units bought less any already sold back there) is counted on the bid side too, the same capacity E4c checks. This
  is a conservative reservation, not consumed liquidity: the sell-back is not an order, so it can refuse a short sale a
  real book could have filled (review 126 Q2). This needs no new state: the records are kept in Drive after each entry
  (E2c) and are what the next entry reads, and a rerun counts the same units (E1's fills are idempotent by fill ID). The
  entry being checked never counts its own trade's rows, so a rerun after a crash between its fills and its event does
  not refuse itself.
- **The check:** `entry_problems` takes those units as an optional argument (empty by default, so E8 and E4c's tests
  are unchanged). Each leg's side passes only if the displayed size covers this entry's units plus the units already
  taken on that contract and side. The same `price_leg` is used with the summed units, so there is no second pricing
  rule.
- **The refusal:** the later entry is `not_opened` with a new code, `size_shared_in_book`, and
  "(<contract>, <units> units, <taken> already taken in this book at this snapshot)". These are the book's own units,
  never a quote figure. The information alert is the same as E4c's (`refused_by_check`).
- **Order:** entries are checked in the order the book's orders come (the decision's order). The first that fits
  fills; a later one that no longer fits is refused. E4c's own codes keep priority: a leg that fails on its own records
  its E4c code. `size_shared_in_book` is recorded only when the leg would have passed alone.
  This is a fixed, deterministic priority: Book 1's order list decides, the earlier strategy wins, and the order is
  never changed after outcomes are seen (review 126, response 209). It is a paper execution policy, not a fair split
  between strategies: a later strategy can lose capacity to an earlier one, and E6 and scoreboard B report such misses
  (review 126 Q4, routed to their owners).
- **Never pooled across books:** each book (and each shadow account) counts only its own records, as E1's firewall
  says.

Out:
- **Exits at the same snapshot** (they run after the fills; a close that meets thin size already stays a pending exit,
  E4 criterion 3).
- **Across books.** Different paper accounts are independent hypothetical books.
- **A short leg's buy-back depth.** E4c open question 2 is unchanged.

**Acceptance criteria:**
1. Two entries of one book each need 65 units of one contract on one side, against a displayed size of 100: the first
   opens, the second is `not_opened` with `size_shared_in_book`, and no fill row or ledger row is written for it. At
   size 130 both open; at 129 the second is refused (boundary).
2. The same two entries in two different books both open (never pooled).
3. A leg that would fail alone records its E4c code, not `size_shared_in_book`.
4. A rerun of the fills step returns the recorded outcomes. The first entry's units are counted from its committed
   fill rows, and nothing fills twice.
5. A protective leg already opened counts its sell-back need on the bid side. A later entry that sells the same
   contract short at the bid fits only if the bid size covers both.
6. The reason and the alert hold no quote figure.
7. `entry_problems` with no units taken behaves exactly as in E4c: every E4c test passes unchanged.
8. Engineering: the code in `entry_check.py` or one small new class behind it; constants in `fno/constants.py`; no
   file over 350 lines; ruff, imports and the full suite (`-n auto`) pass.

**Test plan:** unit tests with the fly fixture (65 units) and an SF plus BF pair sharing the 25000 strikes: sizes 100,
129, 130 and 131; two books; the rerun; a planted break per criterion. No network, no Slack.

**Judge verifies:** plants the units taken as zero (criterion 1 fails), pooling across books (criterion 2), and the
shared code taking priority over an E4c code (criterion 3).

**Known limits:**
- The snapshot's displayed size is all the depth the model knows. A real book could refill between two orders.
- The units taken are those already filled at this snapshot. An entry refused for another reason takes nothing.
- Every action other than `open` on a bought leg counts as reducing the protection still held. This is true for
  `unwind`, `close` and `settle`, the only such actions today; revisit it with any new action (review 126 Q5a).
- Two legs of one new entry on the same contract and side are not summed against each other. No STR1 structure has
  such legs; add a focused test before any structure that does is activated (review 126 Q5b).

**Depends:** E4c (merged first) · **Size:** S · **Status:** code PASS judge 205 (e33ba70d);
ChatGPT review 126 PARTIAL, acceptable for merge (text only, response 209)

---

## E5. Book 1: pure rules

**Repository:** trading

**Description:** As the owner, I want Book 1 to decide every day by code alone from its approved playbook strategies,
so that the first scoreboard question, "do tested rules alone make net money forward?", is answered cleanly.

**Context and why:** Design 12.1 and 12.9: Book 1 has no AI authority; any AI view is a shadow record only. Book 1
trades once a strategy has passed the historical test (12.11) and is `paper` in the playbook. Its decision is D2's
evaluation on the common and private packs.

**Scope.** In: Book 1's decider, its decision records, its forecasts' source (G3 frozen method). Out: AI (none).

**Expected design:** `fno/books/book1.py`: reads the two packs, runs D2 with C2 (Book 1's account) and C4 (playbook
mode), writes the D3 record with `chosen_action = rule action`, commits before the deadline. With no `paper` strategy,
it records "no approved strategy" each day (that is a result, not an error).

**Acceptance criteria:**
1. Book 1's decision equals D2's result on the same inputs (replay test on fixture days).
2. No AI call is reachable from Book 1's code path (test with an AI fake that fails on any call).
3. Without any `paper` strategy, each session day has a committed "no approved strategy" record.
4. Book 1's records are committed before the deadline on every fixture day.
5. End-to-end negative test: a Book-1 decision failing C4 never becomes a fill.

**Test plan:** replay tests; the AI-fake test.

**Judge verifies:** replays three Book-1 records.

**Depends:** C4, D2, D3, E2, E3 · **Size:** S · **Status:** done: judge 84 PASS (e3e0346), merged 58f5781; not live (no routine yet) (claims: reviews/claude/response_85_e5-book1.md)

---

## E5b. Book 1's decision command: one decision a day, and a failed commit alerts once and is recovered

**Repository:** trading

**Description:** As the owner, I want Book 1 to hold at most one decision a day, and `fno desk book1` to handle a
failed commit the way E3's daily run now does (story E2b, decisions 44 and 47): one alert, a clear line, exit code 1,
no traceback, and a rerun that commits the recorded decision as it was made. That way a later run can never re-decide
the day with later data (a look-ahead hole in the book's record), and a refused or rejected commit is never silent.

**Context and why:** Orchestrator decisions 46, 57 and 59 (judge 118 addenda 3 and 7; judge 123). Today `Book1.decide`
(`fno/books/book1.py:74`) calls `GitCommitter.commit`, which raises `CommitFailed` on any refusal or git failure (a
raw quote file in the index, a failed pull, a push rejected three times, an unpushed commit it did not make). Nothing
catches it, so the command ends in a traceback and nothing reaches #fno-desk. A rerun with byte-identical inputs then
returns "already decided" (`DuplicateRun`, `fno/playbook/decision_store.py:72-75`) without committing, so the first
decision stays uncommitted (or committed but unpushed) for good; with any changed input it decides again as a second
run beside the first, so the day holds two decisions, and E3's collector takes the latest one committed before the
deadline (`fno/desk/committed_decisions.py:36-41`). A rerun at 15:08 with fresher data would then replace the 15:00
decision: a look-ahead hole (decision 57). The judge's note (addendum 7): a Book 1 decision commit left unpushed in a checkout
also stops E3's daily run in that same checkout at its first commit (an unpushed commit the run did not make, decision
51), so its exits are not reviewed until the decision is resolved.

**Scope.** In:
- **One Book 1 decision a day: the prevention (decision 59 a).** Before deciding, `Book1.decide` fetches origin and
  looks for a Book 1 run of the day in three places: `origin/<branch>`'s decision folder, this checkout's `HEAD`, and
  this checkout's day folder on disk. A run found anywhere means it never decides again, whatever the inputs. Then:
  - **on origin, or committed here:** it reports "already decided" (after pushing a commit left unpushed, below);
  - **recorded by the pending marker:** it recovers the pending commit (below);
  - **on disk only, neither committed nor in the marker** (a stop between the decision and the marker write; judge
    123 should-fix 2): one alert naming the run and the hand fix. The fix is to inspect it, then commit it as recorded
    with `fno desk book1 --commit-run <run_id>`, or remove it before the deadline. Never a quiet "already decided",
    never a new decision. `--commit-run` refuses a run whose files D3's own check finds edited
    (`DecisionStore.edited`, the run's `records.sha256`), and it never runs D2.
  A second check sits just before the commit. Book 1's committer is given a check of the pulled tree (one new
  optional argument on the `Committer` port, run by `GitCommitter` after its pull and before it commits). That check
  refuses to commit a new Book 1 run when the pulled tree already holds another for the day, through `CommitFailed`,
  so it gets one alert. This covers two checkouts deciding at the same time (a scheduled session fired twice, or a
  retry in a fresh container).
- **Changed inputs on a decided day.** The day's inputs are recomputed and serialized as `DecisionRun` writes them,
  then compared byte for byte with each input file the run records (today `inputs.json`). When they differ, one alert
  states the fact and names each differing file and the top-level fields that differ ("inputs changed after
  decision <run_id> ...; not re-decided"). Nothing is acted on.
- **The guarantee is in D3b, not here (decision 59 b).** E3's collector will take the *first* non-correction run
  committed before the deadline, for every book. Then a second run that slips past this story's checks still never
  becomes the day's decision. This story is the prevention, and D3b carries the guarantee. Both are needed: the
  prevention alone depends on every writer checking, and the guarantee alone would still let a second run be written
  and published.
- `cmd_book1` (`fno/books/book1_cli.py`) catches `CommitFailed`: one alert to #fno-desk through the same alert
  sender as the daily run, the same text printed as one line, exit code 1, no traceback. The text names the cause and
  what it blocks: the decision is not public yet, so it is not on time unless it is pushed before E3's deadline, and
  a daily run in this checkout stops at its first commit until it is resolved. The hand fix: remove the cause, then
  rerun `fno desk book1`.
- Book 1's commit goes through E2b's `PendingCommitter` (a second use of the same class, with its own marker
  `journal/runs/.pending_book1.json`, git-ignored), so the rerun's first act commits the recorded decision files
  exactly as they are on disk, pushes a commit left unpushed, and never runs D2 again. A changed or missing file
  stops the rerun with the alert naming it. Nothing is regenerated.
- Its own marker, not the daily run's: the two commands may run in one checkout at overlapping times, and one shared
  marker could be overwritten.
Out:
- D3's shared store rule (`DecisionStore`: same inputs refused, new inputs make a new run;
  `tests/decisions/test_records.py::test_the_same_inputs_twice_are_refused_new_inputs_make_a_new_run`) stays as it is.
  It serves every book and D3's corrections (a new run linked by `corrects`, `test_a_correction_is_a_new_run_linked_to_
  the_record_it_corrects`). The one-a-day rule is Book 1's, in `Book1.decide`; books 2 and 3 take it when they are
  built (F5, F6). No existing test expects Book 1 itself to decide twice (checked: `tests/book1/`);
- E3's collector and D3 corrections: decided by decision 59 (b) and carried by story D3b (decision 58). The collector
  takes the first non-correction run before the deadline, and corrections are recorded and shown but never become a
  book's timely decision;
- any change to on-time rules: E3's collector decides from what origin shows at the deadline (`committed_at` before
  the deadline and visible then), so a decision pushed by a rerun after the deadline is late, as today;
- automatic retries or schedules (no routine runs `fno desk book1` yet);
- the daily run itself (E2b).

**Decided (orchestrator decision 57):** option A, recovery with Book 1's own marker (one new constructor argument on
E2b's class, the marker name), plus the one-decision-a-day rule. Option B (alert only, with a hand fix) was not taken.

**Acceptance criteria:**
0. Decide, change an input, rerun: one decision run for the day; one alert naming each input file that differs byte
   for byte from the run's recorded copy, and the fields; the decision files byte-identical. The same holds in each of
   three states: the decision committed, recorded only by the marker, or on disk only (then the alert gives the hand
   fix, and `--commit-run` commits it unchanged or refuses an edited run). A rerun with unchanged inputs on a committed
   decision reports "already decided" with no alert. Two checkouts of one bare origin each run `fno desk book1` for the
   same day, one after the other and also with the second pulling only after the first decided: origin ends with
   exactly one Book 1 run, and the second gets "already decided" or a refused commit, with an alert (tests).
1. With the real `GitCommitter` and a bare origin, a staged raw quote file, an unreachable origin and a push rejected
   three times each give exactly one alert naming the cause, one printed line, exit code 1 and no traceback (tests).
2. After the cause is removed, a rerun commits the decision files byte-identical to the first run's, with D2 run once
   in total, and origin then holds the decision; a push left unpushed is pushed by the rerun (tests).
3. A decision file changed after the failure stops the rerun with an alert naming it; nothing is committed and D2 is
   not run again (test).
4. Book 1's marker and the daily run's marker are separate files; a pending Book 1 commit does not change what the
   daily run's recovery commits (test).
5. A successful decision prints the same line as today, and exit code 0 (test).

**Test plan:** CLI and unit tests with real git against a bare origin, a fake alert sender (nothing posted), broken-code
proofs per criterion.

**Judge verifies:** reruns criteria 0 and 2 by hand; plants a second decision on changed inputs, a skipped origin
check, a skipped pre-commit check, a quiet "already decided" for an on-disk-only run, a missing catch, a shared
marker and a skipped hash check.

**Depends:** E2b (merged first: `CommitFailed`, `PendingCommitter`); D3b carries the collector's guarantee
(decision 59 b) and can merge in either order · **Size:** S · **Status:** story text on
`story/e5b-book1-commit-failure`, for the judge's story check (response 123)

---

## E6. Strategy paper scorecard and pause rules

**Repository:** trading

**Description:** As the portfolio manager, I want each paper strategy measured against its own evaluation plan, with
hard-loss pauses at once and statistical reviews only on scheduled dates, so that keeping, pausing or retiring a
strategy follows rules fixed in advance, not mood.

**Context and why:** Design 6 (paper gate at least 3 months and 20 positions, a minimum, not proof; plan fixed before
paper), 12.8 (no switch-off for statistical reasons before a scheduled review, except the brake, a strategy-level
catastrophic loss rule and any data, integrity or safety failure). Execution costs must be measured from the record
against the research pad.

**Scope.** In: per-strategy scorecard per book, pause rules, measured execution costs. Out: the book-level scoreboards
(S2, S3), changing a strategy (a new version).

**Expected design:** command `python -m fno desk scorecard [--book] [--strategy]` reading decision records, fills and
the playbook's evaluation plan; shows results against the expected range, the three ledgers (C1), the average
half-spread paid, legging costs, the share of attempted trades that did not fill and pending-exit delays, against the
Rs 1 pad used in research. Pause rules fire automatically and are recorded as a playbook status change (D1 registry).

**Acceptance criteria:**
1. Given a strategy's catastrophic-loss rule hit, its status becomes `paused` at once (no new trades in any book) and
   the owner is alerted.
2. Gate to any real-money discussion: at least 3 months and at least 20 completed positions, judged only on
   predetermined review dates; open positions are reported at their marks and not counted; an inconclusive result is
   never promoted.
3. Execution costs measured from the record match a hand computation on fixture fills.
4. On a review date, the scorecard states keep, pause or retire per the plan's own rules.

**Built (14 Oct 2026; the orchestrator's defaults, `reviews/claude/response_75_e6-scorecard.md`):** desk records carry the
version (`strategy`, `<name>-v<n>`) and the touch each fill met; a gate refusal is its own outcome (`refused`), apart
from fills that failed. Each shadow version has its own account `journal/shadow/<name>-v<n>/account/`, scored in a
separate section, and is D2's `ShadowBooks` (`fno/desk/shadow_books.py`). The machine-checked pause rule is the plan's
`catastrophic_loss_rs`, never above C2's per-trade maximum loss. The review thresholds are provisional until S1 and live
only in config.yaml `scorecard_review`. The review rule: only on a review date
and past the gate; mean C1 net per completed position with a seeded bootstrap 95% interval; retire when the interval's
upper end is below the expected low, pause when the mean is, else keep; promotable only when the interval's lower end
and the whole net are above zero. A review's decision is stated, never applied: only the owner pauses for statistics
or retires (D1). Judge 67: a paper version whose live feature drifts drops out of `approved()` and is paused by
`hard_loss_rule`; the rest keeps loading.

**Test plan:** tests with simulated paper histories.

**Judge verifies:** recomputes one scorecard number from the records.

**Depends:** C1, D1, E4 · **Size:** M · **Status:** done: judge 73 PASS (round 3 be69a08), merged 374ad67 (claims
`reviews/claude/response_75_e6-scorecard.md`)

---

## E6b. Missed executions in the scorecards: every refused or missed entry stays in the strategy's opportunities

**Repository:** trading · **Lane:** 1 (scoring and evaluation records; S2's scoring code joins S1's freeze). **Quality
rule 9 applies** (ChatGPT after the judge's PASS).

**Description:** As the portfolio manager, I want each strategy's and each book's record to count every entry it
could not execute, by reason, beside the trades it did fill, so that a strategy that loses entries to thin size, a
shared touch or the owner's timing is seen as capacity-constrained, not as inactive or better than it is.

**Context and why:**
- S1 pending edit (10) (`docs/WORK_REGISTER.md`, S1 text row). It collects ChatGPT reviews 122, 123 and 126 (responses
  190, 192, 209): net P&L per executed fill and per eligible opportunity, a missed entry being 0 in the denominator,
  with the fill rate and miss reasons on the whole original set. Refused entries (E4c's `not_opened`, E4d's
  `size_shared_in_book`, E8's misses) are missed executions of the strategy and its book, never a skip or a losing
  trade. "Code follow-up for E6 and S2 raised when E8 merges."
- **Today (code read, strong evidence):**
  - E6's `execution_costs` counts `not_filled` (all `not_opened` plus partial fills) as one number, with no reason
    split.
  - S2's board counts filled trades only. A strategy's misses do not appear on it at all.
  - E8's `TimingReport` (story text) is to report orders, fills, misses by reason and both nets per view. That would
    be a third counter of the same thing.
- **Why it matters (reasoning only):** filled-only results are conditional on filling. E8a measured that with the
  owner's price cap, bought options fill mostly on mornings that went against them (some evidence), and E4d's fixed
  entry priority makes a later strategy lose capacity to an earlier one. Without the misses beside them, a
  miss-skewed record reads as "the strategy is bad", or a starved one as "the strategy is quiet".

**Scope.** In:
- **One counter, used three times.** A new class `ExecutionOpportunities` (new module, `fno/desk/execution_outcomes.py`)
  is a pure function over one account's desk event rows and C1 trade lines (no file, Drive or desk I/O inside, so
  hashing it at S1's freeze pulls in no desk behaviour; S1's owner, 15 Oct). It gives, per strategy version and for the
  whole account:
  - **opportunities:** every trade with an entry outcome that reached the fill step: `opened`, a partial fill
    (unwound at once) or `not_opened` for any reason, E8's misses included (E8 writes each miss as a `not_opened`
    event with its fixed reason; agreed with E8's builder, 15 Oct). Gate refusals (`refused`: C2, C3, timing, a
    blocked book, E8's blocked book too) are risk or data decisions, not execution opportunities: counted apart, as
    E6 does today. E8's `entry_pending` (handed over, not yet due) is counted as "awaiting fill", outside the
    denominator until its fill or miss lands;
  - **filled** and the **fill rate** (filled over opportunities);
  - **misses by reason**, from one fixed table: `protection_not_buyable`, `protection_not_sellable`,
    `short_leg_not_sellable`, `size_shared_in_book`, `entry_worse_than_approved`, "partial fill, unwound", E4's guard
    ("a leg did not fill after the check"), and E8's eight (`MISSED_NO_CARD`, `MISSED_OWNER_AWAY`, `MISSED_NO_QUOTE`,
    `MISSED_PRICE_MOVED`, `MISSED_EXPIRED`, `MISSED_FUNDS`, `MISSED_RISK_CAP`, `DECIDED_AFTER_CARD`, imported from E8's
    modules, never copied). A reason the table does not know is counted as "other" with its count, never dropped;
  - **filled-only net:** C1 net per closed completed position (E6's review sample, unchanged);
  - **net per opportunity:** C1 net of every closed trade among the opportunities over the opportunities that are no
    longer open. An unwound partial fill enters with its actual C1 net (legging and unwind costs), never as 0: only a
    true no-fill counts 0 (S1's owner, correction a). A trade still open is neither 0 nor a miss: it is counted apart
    as "open" (a part of filled) and is in neither net, as S3's `after_cut` does (correction b).
- **The chain, per strategy and book** (ChatGPT review 131, response 221): chosen decisions (every desk entry
  event of the strategy: gate refusals plus fill-step opportunities; orders stopped before the desk are S6's
  `missed_runs`) → gate refused → reached the fill → opened / missed / awaiting fill → closed / still open. It keeps
  decision feasibility apart from execution feasibility:
  - **gate refusals by reason**, beside the execution figures, from one named table of the desk's refusal prefixes
    (C2's "risk manager refused", with C2's first verdict named; C3's data checks; the risk decision not matching;
    decided too late; snapshot incomplete; a blocked book), unknown ones as "other";
  - **both counts in words**, never one as the other: for 100 decisions, 80 refused by C2, 20 reaching the fill and
    20 opened, "fills 20 of 20" and "opened 20 of 100 decisions"; never "100% of signals traded";
  - **an unwound partial fill** is an execution miss and its real net (spreads, C1 charges, legging loss) enters net
    per opportunity: nine closes at +Rs 900 and one unwind at -Rs 250 give a filled-only average of Rs 900 and a net
    per opportunity of (9 x 900 - 250) / 10 = Rs 785;
  - **open trades:** `open_count` and the oldest open trade's age in sessions; both averages labelled "closed only,
    provisional while trades are open". When they close, the figures are recomputed from the same immutable events,
    never backdated. The denominator of net per opportunity is printed: opportunities minus open (awaiting fill is
    in neither);
  - **cohort label:** the block covers all dates and versions of the account and says so, "all dates, not the claim
    cohort". Before any figure is used for a version or promotion comparison, the block for that claim is computed
    on the claim's own eligible dates and version, by a date and version filter in the same counter (no second
    engine). Example: pilot 20 of 20 filled and the new version 2 of 10 give 22 of 30 (73.3%) overall, which hides
    the new version's 20%. E6b still changes no S1 verdict;
  - E4d's fixed priority and `size_shared_in_book` per strategy, and E8's owner away, price moved and no quote apart
    (they have different remedies).
- **E6's scorecard** shows the block for every card. Its present entry line (`attempts`, `opened`, `not filled`,
  `refused`) is replaced by the block, so there is one count of entries, not two (DRY). The changed report line is
  stated in the claims, not loosened.
- **S2's board** shows the block in each book's overall section and in each strategy entry (`strategies`), with the
  gate refusals beside it so nothing vanishes. The block's logic is in the new module; `book_board.py` gains one call
  for the overall section and one per strategy entry, and `sections.py` (S6's) is not changed. The book's block also
  states the entry priority: "fixed, the decision's order (Book 1's order list), never reordered after outcomes"
  (E4d).
- **E8's `TimingReport`** calls the same class once per view account (agreed with E8's builder, 15 Oct: the class
  takes one account, with no view logic inside). E6 and S2 read the verdict account only (E8 rule 10).
- **Reported only.** No verdict, review, pause, brake, uncertainty test, do-nothing comparison or random control
  changes. Those keep reading what they read now.

Out:
- run-level misses (a session with no collected decision): S6's `missed_runs` already reports them;
- scoreboard A (matched decisions);
- any change to how an entry fills or is refused (E4, E4c, E4d, E8);
- per-section blocks on the board's pilot, head-to-head and segment sections (one line to add later if S1 asks).

**Expected design:** `ExecutionOpportunities(event_rows, trade_lines)` (callers read the account) with
`by_strategy() -> dict[str, ExecutionCounts]` and `whole() -> ExecutionCounts`. `ExecutionCounts` is a frozen
dataclass (opportunities, awaiting fill, filled, misses by reason, open, gate refusals, filled-only net, net per
opportunity). The reason table and the labels are constants in `fno/constants.py`; E8's reasons are imported from E8's
modules. E6's `execution_costs` keeps the half-spread, legging and pending-exit figures and
takes its entry counts from the class. S2's `book_board` adds the block. No new file over 350 lines.

**Acceptance criteria:**
1. A fixture account with one strategy and seven entries (3 opened and closed, 1 `size_shared_in_book`, 1
   `protection_not_sellable`, 1 partial fill unwound with legging cost Rs 120, 1 gate refusal) gives: 6 opportunities,
   3 filled, fill rate 50%, misses {size_shared_in_book: 1, protection_not_sellable: 1, partial fill, unwound: 1}, 1
   gate refusal apart. The nets match a hand computation: filled-only = sum of the 3 nets / 3; per opportunity =
   (sum of the 3 nets - 120) / 6.
2. An E8 miss (`not_opened`, reason `MISSED_PRICE_MOVED`) counts as one opportunity, with its reason, and 0 net; an
   E8 `entry_pending` counts as awaiting fill and is in no denominator; E8's blocked-book `refused` is a gate refusal.
3. An unknown `not_opened` reason is counted under "other", and the totals still add up: filled + misses =
   opportunities, with open a part of filled. "Other" is a visible catch, never a silent bucket: a test lists every
   known reason code (E4, E4c, E4d and each of E8's constants by name), so a reason added in E8 without a table entry
   fails that test.
4. A trade still open is in neither net and is counted as open.
5. Two strategies in one book: each strategy's block counts its own entries only, and the book's block is their sum.
   Two books are never pooled.
6. E6's card and S2's strategy entry give the same block for the same account and version (one class).
7. No verdict changes: E6's review, S2's head-to-head figures, uncertainty, do-nothing and random control are
   unchanged on the existing fixtures (their tests pass unchanged).
8. The block holds no quote figure: reasons are codes and E8's fixed wording only (E2b).
9. The chain (review 131): a strategy with 100 decisions, 80 C2 refusals (reason counted), 20 reaching the fill and
   20 opened shows "fills 20 of 20" and "opened 20 of 100 decisions". Nine closes at +Rs 900 and one unwind at -Rs 250
   give Rs 900 filled-only and Rs 785 per opportunity. An open trade shows `open_count` 1, its age in sessions and the
   "closed only, provisional" label. The whole-account block says "all dates, not the claim cohort", and the filter
   on one version's dates gives that version's own counts (pilot 20 of 20 and version 2 of 10 give 2 of 10, not 22 of
   30). An unknown refusal or miss reason is "other".
10. Engineering: constants in `fno/constants.py`; no file over 350 lines; ruff, imports and the full suite (`-n auto`)
   pass.

**Test plan:** unit tests on fixture desk records (no network, no Slack): criterion 1's account, an E8 miss, an
unknown reason, an open trade, two strategies, two books; E6 and S2 rendering tests; a planted break per criterion.

**Judge verifies:** plants a miss dropped from the denominator (criterion 1 fails), a gate refusal counted as an
opportunity (criterion 1), an unknown reason dropped (criterion 3), an unwound partial fill counted as 0 (criterion
1), an open trade counted as 0 (criterion 4), pooling across books (criterion 5), and E6 and S2 counting differently
(criterion 6).

**Agreements before code (both closed, 15 Oct):**
1. **E8's miss record: closed** (E8's builder, session 01H1CmuW, 15 Oct): `not_opened` with E8's fixed reason, no new
   outcome; `TimingReport` calls this class per view account.
2. **S1's text: agreed** (its owner, session 0185gR5D, 15 Oct): its own item `execution_opportunities` (added to
   `REQUIRED_ITEMS`; status "proposal, owner decides" until the owner decides), worded and landed by S1's owner, with
   `fno/desk/execution_outcomes.py` named explicitly in `frozen_files` (the freezer reads explicit paths only). The
   item, its `REQUIRED_ITEMS` entry and the path land as one S1 edit together with this story's code, never before
   (a listed file that does not exist makes the freeze refuse); the reasons are named by code, not by a count. The
   board change touches `book_board.py` only and is built after S6's follow-ups merge (`story/s6-followups`), or on
   main merged first.

**Code-round notes (judge 212):** a reason's code is matched on the text before " (" (E4c's and E4d's format);
"partial fill, unwound" is the outcome `not_opened_partial_fill`; E4's guard with nothing filled is `not_opened` with
free text ("<contract> did not fill: ...", `entries.py`), mapped by one named pattern constant (no change to E4's
records), and it is in criterion 3's named test.

**Depends:** E6, S2, E4c, E4d (all merged); E8 and S6's follow-ups (code only) · **Size:** S · **Status:** story
text PASS judge 212 (0d644e83); code waits for E8 and S6's follow-ups (response 215)

---

## E7. Expiry settlement

**Repository:** trading

**Description:** As the risk manager, I want a paper position still open at expiry closed at NSE's cash settlement,
with its real charges, so that no book's result carries a dead contract at a stale price and no book keeps trading
while one is unsettled.

**Context and why:** Judge 68 on E4: a leg still open after expiry was never priced, E1 kept marking it at its last
pre-expiry mid (an in-the-money short showed its old value), and the book could keep opening trades. NIFTY options
are cash-settled: each contract closes at its intrinsic value against the index's final settlement price. Orchestrator
and owner condition (14 Oct 2026): no strategy version is approved to paper until E7 passes.

**Scope.** In: the final settlement price (point in time), the settlement close of each expired leg, exercise STT in
C1, blocking new risk while a settlement price is missing. Out: physical settlement (stock options; NIFTY is cash
settled), choosing exits (E4's rules and the playbook).

**Expected design:**
- `fno/desk/settlement.py`: interface `SettlementPrices.final_settlement(underlying, expiry)`; `NseFinalSettlement`
  reads **only the expiry day's** UDiFF F&O file through A2's library (`build_nse_fo_library`). In that file every row
  of the expiring contracts (future and options) carries the index's final settlement price in `SttlmPric` (an option
  row's `SttlmPric` is not the option's value; its `ClsPric` is not its settlement value: NSE 25 Jan 2024, 21300 CE
  closed at 19.70 and settled at 52.60). The price is used only when every expiring row agrees; otherwise refused.
  Not yet published: no price.
- The exit review (E4) settles every expired leg at `max(settlement - strike, 0)` (call) or `max(strike -
  settlement, 0)` (put), short legs bought back and long legs sold at that value, recorded as `settlement` rows in E1's
  ledger and `settle` rows in the desk fills (the file's SHA-256 in place of a snapshot hash), dated the expiry day at
  15:30 IST.
- C1 (`fno/costs.py`): `settlement_charges_breakdown`: an in-the-money long pays STT at `charges.stt_exercise_pct`
  (0.15% of intrinsic value from 1 Apr 2026, Budget 2026; it was 0.125%) on its intrinsic value; brokerage plus GST on
  every in-the-money leg (conservative); no exchange, SEBI, IPFT or stamp charge (no premium traded); nothing on a leg
  that expires worthless. One dispatch, `Order.charges(table)`, serves E1's fills and C1's three ledgers.
- While the expiry day's file is not published (or gives no clear price), the trade is `settlement_needed`: one
  alert to #fno-desk per day, and it blocks the book's new risk exactly like `protection_unverified`.

**Acceptance criteria:**
1. An in-the-money short at expiry closes at its intrinsic value against the final settlement price, never the stale
   pre-expiry mid or the option's close (hand computation).
2. An out-of-the-money leg settles at 0 with no charges.
3. An in-the-money long pays exercise STT on its intrinsic value; a short does not.
4. Only the expiry day's file is read; a file whose expiring rows disagree on the price is refused, never guessed.
5. A missing settlement file gives `settlement_needed`, an alert, and no new risk for that book until it is settled.
6. After settlement C2 no longer sees the position (no marks or terms needed), and C1's trade ledger equals the
   account's net to the paisa.

**Test plan:** unit tests with a cut of NSE's real 25 Jan 2024 file and fixture positions; mutations of each rule.

**Judge verifies:** recomputes one settlement by hand from an expiry day's NSE file.

**Depends:** A2, C1, C2, E1, E4 · **Size:** S · **Status:** done (judge 71 PASS; merged f655612; claims `reviews/claude/response_73_e7-expiry-settlement.md`)

---


## E8. Owner-timing fills

Story text in its own file: `docs/stories/E8-owner-timing-fills.md` (issue #109).

---

## E8a. Fill-timing study: what E8's reaction-time fills do to an entry (history)

**Repository:** trading

**Description:** As the F&O trader and the risk manager, I want to know how far each structure family's entry price
moves between the decision and E8's fills (R = 5, 30 and 60 minutes), for a 15:00 decision and for a 14:00 decision,
and how often a trade that wins when filled at the decision price would lose when filled at E8's price, so that the
owner can choose the decision time from numbers before any strategy is paper traded on E8's fills.

**Context and why:** owner decision of 15 Oct 2026 "Fill-timing study: history now, then live"
(`docs/DESK_DECISIONS.md:179`). E8's design (`docs/design_v2/03_layers_factory_desk.md:88-102`): a card at time T
fills at the first quote snapshot at or after T + R; after 15:25 the fill moves to the next session's 09:15 + R; the
remedy for a costly delay is an earlier decision time (an S1 `timetable` change, for example 14:00), never a shorter
R. Response 144 plan item 3. Facts already measured:
- NIFTY's close-to-open move, 680 sessions of 2024-26 (`research/data/intraday/rv-candle`, `rv_overnight`): median
  0.22%, at least 0.5% on 17% of sessions, at least 1% on 5% (some evidence; recomputed by judge 153).
- Groww serves 15-minute candles of **expired** NIFTY options (read-only probe, 15 Oct 2026, nothing stored): Jan and
  Jun 2024 and Mar 2025 contracts answered 51-53 candles with volume and open interest. The prices are **real last
  trades**, not bid and ask and not model estimates. A Sep 2025 symbol returned nothing (probably a wrong expiry date
  after NSE's move to Tuesday expiries), so coverage is probed before the freeze (below).
- The daily card has no trade fields yet (`fno/cards/card.py:76-78`) and E8 is not built, so no entry range exists.

**What the numbers can and cannot mean (judge 153 B1).** For one structure entered later with the same exit, the P&L
changes by exactly the entry move `C`. The families mirror each other (STR1: SF = CCS + PCS, BF = CDS + PDS, BF is SF
with every leg reversed), so the **mean** of `C` for a seller is minus the buyer's: it is mostly price drift, chiefly
the overnight time decay (theta), which a later seller also stops paying for. So the mean is never read as "the cost of
waiting". The study leads with the **size** of the move (the spread of `C` and of `|C|`, the bad-side tail) and with
the **flip share** (below), splits 1-night from 3-night (weekend and holiday) gaps, and shows the time part
separately. It cannot measure what waiting costs in the decision itself (an older signal): that is out of scope and
said on the report.

**Scope.** In:
- a frozen, registered history study, 2 Jan 2024 to 30 Sep 2026, of NIFTY monthly options, for the families SF, SC,
  BF and the STR1 codes (LC, LP, CDS, CCS, PDS, PCS);
- the two decision times with all three E8 reaction times;
- E4's 15:15 execution snapshot (it is at the same time as the 15:00 decision's R = 5 fill and the 14:00 decision's
  R = 60 fill, so it is labelled on those rows, not computed apart);
- the flip share;
- the raw candles archived;
- one results file.

Out, each with its reason (gap list, judge 153 B3):
- The live comparison with A16's bid and ask. It needs 20 sessions of A16 data, so it is a follow-up story; this story
  only fixes its rule.
- E8's fill code and its entry range. The card has no trade fields yet.
- "Missed, price moved". It needs an entry range; the 5/10/20% thresholds below stand in for it.
- The decay of the decision signal. It cannot be measured from prices alone.
- Weekly options. The decisions are monthly.
- Any edge or verdict on a strategy.
- A timetable change. The owner decides from the results.

**Expected design:**
- **Registration:** study folder `research/2026-10-16-fill-timing/` (`PROTOCOL.md`, `FREEZE.md`, `README.md`,
  `results.md`, `results.json`, a small `ft1study/` package) and idea card `research/ideas/FT1.md`. Ledger trial 54
  takes kind `prospective`, hypothesis `no`, as R2 did (`fno/research_engine/ledger.py:26`). Protocol and code hash
  are frozen before the full fetch (`research/FACTORY_RULES.md` G4).
- **Coverage probe before the freeze:** one read-only call per month of the window (nearest-ATM call of that month's
  monthly expiry, symbol built from the panel's listed expiry date) records only whether Groww answers and its candle
  count, never a price. A month that does not answer is first investigated (symbol format, the Tuesday-expiry dates
  from Sep 2025, a second strike) and its cause written in the protocol; only a month still unanswered is left out and
  listed. The probe's counts and causes go into the protocol before the freeze.
- **Sessions:** every regular session (A7) whose next session exists. Special and muhurat sessions are left out and
  counted.
- **Expiry:** the nearest monthly expiry more than 7 sessions away. Figures are split by sessions to expiry (8-15,
  16-25, 26 and more), so contracts of different ages are never pooled without a split.
- **Strikes:** built by `fno/research_engine/structures.py` at NIFTY's 15-minute close at the decision time, at width
  200 points (experiment 1's middle width; 100 and 300 as sensitivity), from the expiry's strikes in the daily panel.
- **Prices and times:** each leg's close of the 15-minute candle ending at the time named. All legs of a structure
  are taken at the same time.
  - The decision price is the 15:00 close (candle 14:45) or the 14:00 close (candle 13:45).
  - A 15:00 decision (card about 15:08) fills at 15:15 (R = 5), next session 09:45 (R = 30) and next session 10:15
    (R = 60).
  - A 14:00 decision (card about 14:08) fills at 14:15, 14:45 and 15:15.
- **Measure:** `C = signed(price_fill - price_decision)` in index points per unit, positive when worse for the trader
  (a seller gets less credit, a buyer pays more); **bad side** means `C > 0`. It is shown also as a share of the
  structure's risk scale: the width for SF, SC, BF and the four spreads, the decision debit for LC and LP (their
  "width" is a distance out of the money, not a risk), never a share of a small credit; and in rupees at today's NIFTY
  lot size (stated once; points carry the result).
- **Per family, decision time and R:**
  - n; the 10th, 50th and 90th percentiles of `C`; the mean of `|C|` and its 95% block-bootstrap interval;
  - the share of days with bad-side `C` above 5%, 10% and 20% of the risk scale (entry-range stand-ins, reasoning
    only);
  - the time part: the Black-76 value change from the decision time to the fill time with only time moving (forward
    and IV held at the decision; forward = the same-expiry NIFTY future's 15-minute close at the decision time,
    fetched read-only with the legs; IV per leg from that forward and the leg's decision price,
    `fno/research_engine/implied_vol.py`; time in calendar minutes / (365 x 1440)), shown beside the mean of `C`; a
    leg whose IV cannot be solved makes that structure's time part "not computed", counted, never filled in;
  - splits: 1-night vs 3-or-more-night gaps; gap band from the same 15:00-to-fill window (below 0.5%, 0.5-1%, 1% and
    more); India VIX at the decision day's open (known at decision time; below 13, 13-18, above 18). A cell with fewer
    than 30 days prints "too few days", never a number.
- **The owner's choice, paired:** per session and family, the difference between the 15:00 decision's R = 60 bad-side
  `|C|` and the 14:00 decision's R = 60 bad-side `|C|`, with its block-bootstrap interval. What the 14:00 path gives up
  (the last hour's information) is stated as not measured.
- **Flip share ("win at both", owner row):** for each structure, held to expiry (settled at intrinsic value against
  NSE's final settlement price, E7), net of C1 charges, each fill charged at its own price (STT and exchange charges are shares of premium), with a P&L of exactly zero counted as
  not a win. Printed per family and decision time at R = 60: **bad flips** (wins at the decision price that lose at
  E8's price) as a share of those wins, and **good flips** (losses that become wins) as a share of those losses. The
  report prints only these two shares, never a win rate or a mean P&L, so no strategy result leaks out. All entries
  into one expiry share one settlement price, so the independent unit is the **expiry** (about 33): the interval
  resamples whole expiries (B = 10,000, the protocol's seed). Exploratory: it reads option P&L of spent data.
- **Bootstrap:** stationary blocks of 5 sessions (10 and 20 as checks), B = 10,000, one fixed seed in the protocol.
- **Stale and missing legs:** a leg whose candle has zero volume is stale. The structure is left out of that time's
  figures and counted; no other price stands in. Per family and path, more than 10% of sessions stale or missing makes
  that cell "insufficient data", and the report shows it as such, never as a number.
- **Spread caveat:** candle closes carry no spread. A4 has only a few sessions of 15:00 bid and ask and nothing at
  09:45, 10:15 or 14:00-14:45, so the spread at the fill times is **not measured** here. The report says so and gives
  A4's 15:00 median half-spread per family only as an order of size; the live follow-up measures it.
- **Raw answers** go to Drive through `RawFileStore` (`raw/groww/options/candles-15m/<yyyy>/...`) with a manifest and
  SHA-256 in `research/data/manifests/`, in A16b's pattern. Nothing raw goes in the repository. Groww is reached only
  through A16's `ReadOnlyGroww` behind a paced candle-source interface, at most 2 calls a second, outside market hours.
  Estimate: about 2,000-3,000 calls, 20-40 minutes (reasoning only; the dry run measures it).
- **Data spend:** Groww's historical 2024-26 option and future candles become `registered` with the ledger row and
  `spent` after the run, for the 14:00-to-next-10:15 windows of the sampled contracts, because `C` is the P&L of
  "sell at the decision, buy back at the fill". Their 2019-23 candles stay `fresh`. The flip share reads NSE's final
  settlement prices of 2024-26 expiries (already seen through the spent monthly data). The rows are written in
  `research/DATA_SPEND.md` with the ledger row.
- **Live rule, for the follow-up:** after 20 sessions of A16 snapshots, `C` from mid-quotes and from bid/ask (sells at
  bid, buys at ask) is compared, paired by session and family, with the candle-close `C` of the same sessions. The
  report gives the paired difference and its interval, and says the history figures are "not confirmed" when that
  interval excludes zero or its median passes 2% of the risk scale.

**Acceptance criteria:**
1. The coverage probe, protocol, idea card, ledger row 54 (prospective, hypothesis no), the DATA_SPEND rows and the
   code hash are committed and frozen before the full fetch; the probe records no price.
2. One 15:00-decision day and one 14:00-decision day are recomputed by hand from the archived raw answers: strikes,
   leg prices at the decision and at each fill, `C`, and the flip of one SF and one LC structure. Each equals the
   output.
3. Signs and mirrors: fixture candles where a seller's credit falls give positive `C` for SF and negative for BF on the
   same legs (`C(BF) = -C(SF)`, and likewise CDS/CCS and PDS/PCS), tested exactly.
4. E8's timing: a 15:00 decision maps to 15:15, next 09:45 and next 10:15, and a 14:00 decision to 14:15, 14:45 and
   15:15. A Friday decision's next-session fills fall on Monday (or the next A7 session) and are counted as 3 or more
   nights.
5. Exclusions: a stale leg removes that structure at that time and is counted; an entry 7 or fewer sessions before
   expiry, a special or muhurat session, and a month the probe did not answer are excluded and counted. A cell over
   10% stale or missing prints "insufficient data".
6. The bootstrap uses the protocol's seed, B and block lengths; the flip-share interval resamples whole expiries. The
   same run twice gives the same intervals.
7. The report prints, per family, decision time and R, every figure listed in the design, the paired 14:00-vs-15:00
   difference, the flip share, the time part, the splits, the exclusion counts, the spread caveat and the window,
   each labelled exploratory measurement, and the "not measured" lines (signal decay, fill-time spread).
8. The time part equals a hand Black-76 value for one fixture leg (forward, strike, IV, minutes to fill given); the
   gap, VIX, nights and sessions-to-expiry splits put fixture days in the right cells; a cell under 30 days prints
   "too few days".
9. The report prints only the two flip shares from option P&L, never a win rate or mean P&L (a test reads the
   report's fields).
10. Read-only: the study's import closure reaches no order, position, margin or funds call (A16b's test pattern). No
   credential and no raw candle appears in the repository or the output.

**Test plan:**
- Unit tests with fixture candles: the strike choice, the E8 time mapping, the sign and mirror rule, the stale and
  exclusion rules, the bootstrap seed, the flip share, and the report.
- The read-only closure test.
- A dry run on 5 sessions with real answers before the full run, giving the call count and duration.

**Judge verifies:**
- Recomputes the two hand days from the archived raw answers.
- Plants a sign error, a stale-leg substitution, an expiry-week entry and a wrong R mapping, and sees each test fail.
- Checks that the probe and the freeze precede the full fetch and that the probe holds no price.

**Depends:** A7, A15, A16 (`ReadOnlyGroww`), A16b (candle pattern), B2 and STR1 (structures), C1, E7 (settlement for
the flip share) · **Size:** M · **Status:** proposed (story text revision 3, answering judges 153 and 154)

**Evidence labels:**
- The overnight-gap figures are some evidence.
- The 5/10/20% thresholds, the 7-session rule, the 10% insufficient-data cut and the 2% live tolerance are reasoning
  only.
- The study is exploratory measurement with no edge claim. Only the live comparison can make its figures evidence of
  what the owner would really get.

---

## E2c. Per-contract paper fills, marks and equity history in Drive; per-book daily totals in public

**Repository:** trading

**Description:** As the owner, I want every paper record that names a contract's price, and every mark, kept in Drive,
with only per-book daily totals in the public repository. Then no one can rebuild a Groww quote from the public record
(owner "6 A" and "8 A").

**Context and why:** Owner decision, 15 Oct 2026 (`docs/DESK_DECISIONS.md`): "Per-contract paper fills, marks and
equity history move to Drive before the first counted paper fill (story E2c)" ("A: move to Drive"). ChatGPT review
105, point 1 (strong evidence: algebra) found the leak that E2b left open. A public fill at the ask `a`, together with a
public mark `m` of the same contract at the same snapshot, gives the bid: `b = 2m - a`. For a book with one open
contract, `m` is `(marked_equity - cash) / units` (`equity_history.csv`, scoreboard B's `raw_account_net_rs`). STR1's
single-leg structures (LC, LP) make this a real path, not an imagined one. Response 131 records the rule (the public
record keeps per-book daily totals only) and review 105's point 3 (a run with an unrecovered stop opens nothing). No
paper fill has happened yet (no strategy approved), so the move costs no history.

**What is public today and where each part goes (checked in code on `main`):**

| File (committed today) | What it holds | Goes to |
|---|---|---|
| `journal/<book>/account/cash_ledger.csv` (E1) | every fill: contract, quoted and fill price, charges | Drive |
| `journal/<book>/account/desk_fills.csv`, `desk_events.csv` (E4) | every leg's fill; events with reasons and legging cost | Drive |
| `journal/<book>/account/positions.json` (E1) | open and closed trades with their money | Drive |
| `journal/<book>/account/equity_history.csv` (E1) | daily cash, closed and **marked** equity | Drive |
| `research/scoreboards/B/<date>.json` (S2) | per-trade lines and marked results | Drive |
| `journal/<book>/packs/<date>/private.json` (E2, committed by E3's pack step: `daily_steps.py:85`, `pack_store.py:28`) | the full text of the book's own files, its account folder included (`private_pack.py`) | Drive; its `private.json.sha256` stays public (D3 records the pack's hash as evidence) |
| new: `journal/<book>/daily_totals.csv` | per book, one row per date with a ledger row (closed equity cannot change without one): `date`, `closed_equity_rs`, `open_trades`, `closed_trades`, `fills` (a count) | public |

`closed_equity_rs` is the opening cash plus the net of closed trades only. It holds no cash for open positions and no
mark. A closed trade's net is the sum of its fills at different snapshots, so it gives no bid-ask pair (reasoning).
The run log keeps what it holds after E2b (outcomes, run IDs, snapshot IDs, no prices). The daily card is already
Drive-only (T1).

**Scope.** In:
- **Where the files live.** A book's account folder becomes local and git-ignored. Its files are kept in Drive through
  A4b's Drive store, under their repository paths in the `paper` area (`paper/journal/<book>/account/`; judge 159
  accepted the whole path, so one rule covers accounts, packs and scoreboard B), with the same names and formats (E1,
  E4). Shadow accounts go the same way (`paper/journal/shadow/<name>/account/`).
- **The writer.** Every account write (fills, exits, settlement) runs as one `DriveAccountSync`, behind E3's existing
  `AccountSync` port and replacing `GitAccountSync` in `fno/desk/daily_wiring.py`:
  - download the book's files from Drive;
  - apply under E1's lock;
  - upload the changed files, the desk fills first and the desk events last (judge 159: a push that stops part way
    leaves a state the rerun completes; an entry's event is its "done" marker, and a ledger fill never reaches Drive
    without its desk row);
  - then write and commit `daily_totals.csv`.

  The daily run is the only writer of accounts (E3), so the git reset-and-reapply logic for competing writers goes:
  one writer, no merge.
- **The private packs.** E2's pack builder writes each book's `private.json` to Drive beside the account. Only its
  `private.json.sha256` is committed, and D3 records the pack's hash, as today. Book 1's decision hashes its pack for
  D3's record (`fno/books/book1_inputs.py:42`), so it needs the downloaded copy.
- **The readers: one shared download at the start of each run or command that reads accounts or private packs.**
  The function fetches every book's account and private packs from Drive into the git-ignored local folders. It runs
  once, before anything reads them. The readers are:
  - E3's daily run (fills, exits, settlement, the C3 and C4 checks);
  - Book 1's decision (C2's view of the book, trade counts, opening runs, its private pack: `fno/books/book1_wiring.py`);
  - C4's `LedgerAccounts` (`fno/checks/validity_account.py`, wired in `fno/checks/wiring.py:91`). Its replay stays
    valid on the Drive copy, because C4 counts only the ledger rows filled by the decision cutoff, and the ledger is
    append-only;
  - T1's card (`fno/cards/status.py:29`, `:83-100`). It reads `positions.json` from the downloaded folder, no longer
    from the committed record;
  - E6's scorecards (`fno/scorecard/wiring.py`);
  - scoreboard B (`fno/scoreboard/wiring.py`), which writes its board to Drive, not to `research/scoreboards/B/`;
  - Home's read model (`fno/market_read_models/home_inputs.py`), which publishes to the dashboard's Azure store as
    today;
  - E1's account command (`fno/composition.py`), and the shadow books (`fno/desk/shadow_books.py`), whose accounts
    are downloaded with the books'.
- **The move itself.** Today's committed account files hold only the opening rows. They are uploaded to Drive once,
  then removed from the repository (`git rm`, the history keeps the opening rows only), and the folder is ignored.
- **A stop before the exits blocks new entries** (review 105 point 3; response 131). E3's rerun recovers a stop in the
  same checkout (E2b). But the daily routine starts in a fresh container each day, so the stop can only be seen in the
  committed run log. Before today's fills, the desk reads the last session's run log. If that log has no `exits` step
  (the run stopped before its exits), today opens no new entry, with one alert naming the day. A stop before any
  step (the recovery or the download) leaves no log, so a missing log blocks too once an earlier log exists (judge
  159). A completed exits step can still hold a book whose review failed (an `error`, such as a Drive 503) or whose
  due exits were held up for lack of a snapshot (a non-empty `waiting`): that book alone opens nothing new (ChatGPT
  review 115). A day without a snapshot and nothing due blocks nothing. Today's exits still run, and once they are
  done the next session opens normally.
Out:
- the raw quote files (A4b);
- D3's decision records and C4's records (they hold no fill or mark; E2b's kept mids stay, as decided);
- any change to how fills are priced (E4, E4c).

**Acceptance criteria:**
1. After a day with fills and exits, no committed file holds a contract's fill price, a mark, cash or marked equity:
   a test runs a fixture day end to end (the pack step included) and scans every committed file, the private packs'
   folders included, for the day's prices and marks.
2. `daily_totals.csv` holds, per book and date with a ledger row, exactly the five columns above, matching the Drive account by
   hand on a fixture day (one entry and one closed trade).
3. After the shared download, the daily run, Book 1's decision (with its private pack), C4, T1's card, E6, scoreboard B
   and Home read the same values as they read from the local folder before (one test each, on a fake Drive store).
4. A Drive write that fails stops the account write with E3's alert. Nothing is committed for that step, and the rerun
   repeats the write (E1's fills are idempotent by fill ID).
5. With the last session's run log holding no `exits` step, today's fills step opens nothing and sends one alert, and
   today's exits still run. With the step present, entries open as usual.

**Test plan:** a fake Drive store (A4b's), a fixture day end to end, the committed-file scan (packs included), and one
reader test each.
No network, no Slack.

**Judge verifies:** runs the fixture day and greps the committed tree for the day's prices; recomputes one
`daily_totals.csv` row by hand; checks the stop-blocks-entries test.

**Known limits:**
- The read models go only to the dashboard's Azure store behind sign-in (judge 148). P2 or any later job must never
  commit a page holding these fields to a public repository.
- Two daily runs on one book at the same time would race on Drive (no lock across containers). Only one routine runs
  the desk.
- A closed single-leg trade's net, kept owner-only here, is not a bid-ask pair (its fills are at different snapshots).
- Every command that reads the accounts needs Drive's four `FNO_GDRIVE_*` settings, `market publish --local`
  included; without them it stops with one line rather than read a stale copy.

**Depends:** A4b (the Drive store), E2b, E3, E4 · **Size:** M · **Status:** done: merged df136912 (response 150, first
numbered 148; story text PASS judge 148 add. 1; code PASS judge 159 add. 2; ChatGPT review 115); accounts moved to
Drive at the merge (3f5a4473, d9f67c4)

## E2d. Per-trade daily marks: every open paper trade marked once a session, in Drive

**Description:** As the owner, I want each open paper trade valued once every session and the value kept with its
account, so that the paper-books page, Home's F&O figures and every later reader see what an open trade is worth
today, never a number that nothing recorded.

**Why now (checked on `main`, 16 Oct 2026, found by the P2 builder and the screens lead, routed by R2/G7):**
`AccountWriter.record_equity` (`fno/books/account.py:203`) has no caller outside `tests/books/test_paper_account.py`.
The desk's marks live only in memory during the exit review, and `journal/<book>/daily_totals.csv` holds closed
equity only. So from the first open paper trade nothing records an open trade's value, and the P2 page
`paper_trades` cannot publish `open[].mark_value` or `unrealised`, or `accounts[].value`. E2c moved
`equity_history.csv` to Drive but left the daily call to no one; this closes that gap in E2c's own function (owner
session 0134MoC6). Scoreboard B is not blocked: it re-marks from the execution snapshots at score time
(`fno/scoreboard/daily_values.py`), and nothing here changes it.

**Design (judge 250 and its addendum 1: one rule, one history, no second implementation):**
1. **The rule is S2's, imported unchanged.** S2's `fno/scoreboard/daily_values.py` already values an open trade per
   session exactly as needed: cash flow so far plus each held leg at the mid of that session's valid 15:15
   execution snapshot; a leg without a valid mid keeps its last valid mark, flagged stale; a leg never marked leaves
   the day unvalued. E2d imports `trade_days`, `key_of` and `DayMarks` from it, and S2's `SnapshotMarks`
   (`fno/scoreboard/sources.py`: each session's mids from the snapshot the run log recorded as valid). It edits none
   of them; `daily_values.py` is hashed by S1 (PROTOCOL.md) and stays as it is. So the fallback comes from **the
   trade's earlier execution snapshots**, the same history scoreboard B reads, never from a file E2d wrote: a lost
   marking day cannot make the two disagree.
2. **When.** In the daily run, right after the exit review (`DeskSteps.review_exits`; the run order is snapshot,
   fill, exits, so a trade opened today is valued today), for each book and each shadow account with an open trade,
   in the account's journal under its single-writer lock, pulled from Drive and pushed back (what `sync.write`
   opens), committing nothing: marking changes no ledger row (response 246 addendum 3). For each open trade E2d calls
   `trade_days` over the trade's sessions (entry day to today) with `SnapshotMarks`; today's `TradeDay` is the value
   written. A rerun of a session reads that session's recorded snapshot, so it is never re-dated and never uses a
   later quote.
3. **Per trade, not per contract.** What the page needs is per trade (the contract's `mark_value` and
   `unrealised`), and a per-contract mark would need a second walk of the history. So E2d stores, per open trade:
   `value` (S2's `TradeDay.value`, cash flow plus the legs at their marks), `mark_value` (`value` minus the trade's
   cash flow so far, from its fills), the stale contracts (S2's `TradeDay.stale`), and a status:
   - `valued`;
   - `unmarked` (a held leg never had a valid mid: `TradeDay.value` is None);
   - `awaiting_settlement` (a stale contract whose expiry is before today: no quote exists until the final settlement
     price is published; E7 settles it at the next daily run after publication). This is a label on S2's stale value,
     not a different value, as S3's standard unit treats `past_expiry`.
4. **An unmarked trade.** It never gets a price. Its row says `unmarked` with the contracts S2 could not value, that
   book's equity row is not written that session, and #fno-desk gets one alert naming the book, the trade and the
   contracts (`FNO_SLACK_BOT_TOKEN`). The page shows "not valued on <date>". The gap moves nothing that decides a
   trade: the drawdown brake reads closed equity (`fno/risk/book_view.py`), and S2 carries an unvalued day's change
   to the next valued day without interpolating.
5. **What is written (Drive only, private).**
   - `journal/<book>/account/trade_marks.csv`: one row per open trade and session (date, trade id, status, value,
     mark value, stale contracts). It is new in `ACCOUNT_FILES`, so `PrivateFiles` pulls and pushes it like the other
     account files. It is an output only: nothing reads it back to value a trade.
   - The session's `equity_history.csv` row, from the same values: marked equity = closed equity + the sum of the
     open trades' `value` (the identity `fno/books/equity.py` defines). It is written by a new
     `AccountWriter.record_marked_equity(day, open_value, stale)`. The unused `record_equity(day, marks)` and its
     per-contract `marks` path are removed with their tests, so the account has one valuation path, not two.
   - A rerun replaces that session's rows (idempotent by date and trade), as `_replace_equity_row` already does; a
     same-day row written by a top-up is replaced the same way (test).
6. **Account files refused by path.** Today only `.gitignore` (`journal/*/account/`, `journal/shadow/*/account/`)
   keeps account files out of git, and `git add -f` would get past it: `fno/record_scan/forbidden_files.py` refuses
   raw Groww quotes by one fixed prefix, and no account file. E2d adds a matcher for the two wildcard folders (a new
   class beside `ForbiddenFiles`, which matches one fixed prefix only), so a forced add of any account file is refused
   by the public-record scan (O5).
7. **What stays public.** `daily_totals.csv` is unchanged: closed equity and counts only, no contract, price or mark
   (owner, 15 Oct 2026, "A: move to Drive").
8. **Readers.** The P2 builder's `paper_trades` page reads `value` as `unrealised`, `mark_value`, the status, and the
   book's marked value from the equity row, through `PrivateFiles`. A book whose last equity row is older than the
   session says so (the page's freshness).
9. **Shadow accounts.** The same step runs for each registered shadow account (R3's `journal/shadow/<account>`), in
   its own files.
10. **No age limit on a stale mark.** S2 has none, and a limit in one place only would split the two again. If the
    owner wants one, it belongs in S2's rule, through S1 (judge 250 addendum 1, reasoning only).

**Acceptance criteria:**
1. **Same as S2, every session.** On a multi-session fixture, E2d's `value` equals S2's `trade_days` for every
   session, and `mark_value` equals it minus the cash flow. The fixture has:
   - an entry day;
   - a session with a missing quote (stale, the earlier snapshot's mid);
   - a **lost marking day** (day 2's marking step fails after its valid snapshot was recorded, then day 3 has no
     quote): day 3 is valued at day 2's mid from the snapshot history, as S2 values it, never at day 1's value from
     `trade_marks.csv`.
2. The equity row's marked equity equals closed equity plus the open trades' values, with the stale contracts listed.
3. A trade with a leg never validly quoted is `unmarked`: no equity row for that book that session, and exactly one
   alert naming book, trade and contracts (fake sender in tests; nothing is posted while building).
4. The values come only from recorded valid execution snapshots: a planted later quote in the store is not used.
5. A rerun of the same session gives the same bytes (idempotent), and a same-day top-up row is replaced, not doubled.
6. The record scan refuses a staged file under `journal/<book>/account/` or `journal/shadow/<account>/account/` by
   path, even after `git add -f` (planted-file test for `trade_marks.csv` and `equity_history.csv`).
7. `daily_totals.csv` bytes are unchanged by marking (before and after a marked run).
8. A book with no open trade writes no trade rows and still gets its equity row (closed equity equals marked equity).
9. One book's marking failure is alerted and never stops another book's marking or exits (the exit review's
   per-book rule).
10. Shadow accounts are valued in their own files.
11. A stale contract past its expiry is labelled `awaiting_settlement`, with the same value S2 gives; after E7's
    settlement the trade is closed and no longer listed (fixture before and after the settlement file).
12. `daily_values.py`, `sources.py` and every S1-hashed file are byte-for-byte unchanged (a diff check in the claims).

**Not in scope:** intraday marks (LM1 reads quotes for alerts only; the paper record changes only at the daily run's
snapshot); the risk manager's own valuation with live marks (C2, unchanged); the P2 page itself (P2c's builder).

**Depends:** E1 (the account writer), E2c (Drive store, `PrivateFiles`), E3 (the daily run and its run logs), E4
(execution snapshot), C3 (quote validity), S2 (`trade_days`, `SnapshotMarks`, imported unchanged), E7 (settlement), R3
(shadow accounts), O5 (the record scan) · **Size:** S-M · **Owner:** 0134MoC6 (E2c's owner) ·
**Status:** done: text (judge 250 addendum 2) and code (judge 262) PASS, merged; the desk's `live_from` is on or after
this merge (O8's owner, judge 262).

## E2e. A book's sheet in its private pack, and the pack's own snapshot for every reader

**Description:** As the owner, I want each book that needs its own view of the day (Book 2's rule default, Book 3's
candidates) to get it inside its private pack through one hook, and every reader of the cutoff market to read exactly
the snapshot the common pack froze, so that no book's evaluation is public and none can price on a later quote.

**Design:**
- `BookSheet.sheet(book, day, common) -> Mapping`. `WrittenPacks` runs it after the common pack, and its result
  goes into the book's private pack under `"evaluation"`. Private packs are Drive-only, and git keeps only the
  `.sha256` (E2c).
- `canonical_snapshot(day, common, quotes)`:
  - reads the snapshot ID the common pack recorded, from its recorded dataset;
  - checks the quote file and the sidecar against the recorded SHA-256s;
  - parses those verified bytes;
  - never follows the day's `.canonical` marker (judge 309).

  Book 1's inputs use it, and so do F5's and F6's sheets and deciders.

**Acceptance criteria:**
1. A book's sheet is in its private pack under "evaluation", built from the day's common pack.
2. A book without a sheet: its private pack is byte-identical (same SHA-256).
3. A sheet that raises: that book's pack is not written (no partial pack) and one alert names the book. Every other
   book's pack is written and kept. Without an alert sender the line is printed.
4. `canonical_snapshot` returns the pack's own capture, even when the marker names a later capture with other
   quotes. It refuses a quote file or sidecar that differs from the recorded hash, a missing file, and a pack that
   names no snapshot.
5. The daily run keeps its one reported alert sender.

**Depends:** E2 and E2c (packs, Drive), A4 (the snapshot store) · **Size:** S · **Owner:** 0134MoC6 ·
**Status:** done: merged (judge 309 and addendum 1 PASS); F5 and F6 add their sheets.
