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

**Depends:** A3, A4, A6, A7, D1, E1 (D4 and D5 for the private packs of books 2 and 3) · **Size:** M · **Status:** built on branch `story/e2-market-pack`; awaiting judge (claims: `reviews/claude/response_74_e2-market-pack.md`)

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
- **three stated exceptions**, put to the owner together with the open question of whether paper fills should move to
  Drive at all:
  1. *an unwound entry* (judge 118 SF1; orchestrator for the owner, response 113): when an entry fails after some legs
     filled (E4 criterion 2), each filled leg is traded back at the same snapshot (a protection bought at the ask and
     sold at the bid; a short already sold at the bid bought back at the ask), and `legging_cost_rs` in
     `desk_events.csv` is the spreads paid. Those rows publish both sides of each unwound contract. Rare: a failed
     entry only, after 15:15;
  2. *two accounts on opposite sides* (judge 118 addendum 1, confirmed by a test): E4 fills each account on its own,
     so when one account buys a contract and another sells it at the same execution snapshot (one closing while the
     other opens, or a book and a shadow), their rows together publish both sides of that contract;
  3. *protection unverified at the opening snapshot* (builder's review 2, confirmed by a test; orchestrator for the
     owner, response 113): when a protective leg's bid size cannot cover its units at the snapshot that opened the
     trade, E4 marks it `protection_unverified` and closes the trade at that same snapshot (`fno/desk/exits.py:90-106`),
     so its rows show both sides of each leg closed there. It is also a pointless loss (the spread paid in and out at
     once): a separate small E4 story will refuse such an entry (a protection-exit size check before opening), which
     removes this exception;
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
| E4 criterion 2 (a failed short leg unwinds the protection, legging cost recorded) | kept; the one stated exception (criterion 3) |
| E6's half-spread paid (criterion 3 of E6) | criterion 3 |
| C3's spot rules (2% from the previous close, 0.2% chain agreement) | criterion 2 |
| One spot per recorded chain (orchestrator's decision 4, review 2 finding 6) | criterion 2 |
| Other committed figures that could reveal a quote (review 2) | Scope "Out": exception 3, known channels, kept mids |

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
3. `desk_fills.csv` has no `quote_bid` or `quote_ask` column. Apart from the three stated exceptions (an unwound
   entry; two accounts on opposite sides of one contract at one snapshot; protection unverified at the opening
   snapshot), no committed desk fill row lets a filled leg's other quote side be worked out: tests build E4's outcomes
   (opened, closed at a later snapshot, pending exit, a time rule at the opening snapshot, partial fill) and find that
   within one account only the unwound legs give both sides, that unverified protection at the opening snapshot does
   (pinned until the E4 story removes it), and that two accounts on opposite sides do. E6's half-spread from the execution snapshot equals the old figure on the
   same fixtures; a fill whose snapshot is missing or whose hash differs counts as "touch unknown" (excluded from the
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

**Depends:** C4, D2, D3, E2, E3 · **Size:** S · **Status:** built on `story/e5-book1`, judge pending; not live (no routine; until C4 merges and writes `validity.c4`, no Book 1 order can fill) (claims: reviews/claude/response_85_e5-book1.md)

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

**Depends:** C1, D1, E4 · **Size:** M · **Status:** built; awaiting judge (branch `story/e6-scorecard`, claims
`reviews/claude/response_75_e6-scorecard.md`)

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
claims `reviews/claude/response_73_e7-expiry-settlement.md`)

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
| new: `journal/<book>/daily_totals.csv` | per book and session: `date`, `closed_equity_rs`, `open_trades`, `closed_trades`, `fills` (a count) | public |

`closed_equity_rs` is the opening cash plus the net of closed trades only. It holds no cash for open positions and no
mark. A closed trade's net is the sum of its fills at different snapshots, so it gives no bid-ask pair (reasoning).
The run log keeps what it holds after E2b (outcomes, run IDs, snapshot IDs, no prices). The daily card is already
Drive-only (T1).

**Scope.** In:
- **Where the files live.** A book's account folder becomes local and git-ignored. Its files are kept in Drive through
  A4b's Drive store, under `paper/<book>/account/`, with the same names and formats (E1, E4). Shadow accounts go the
  same way (`paper/shadow/<name>/account/`).
- **The writer.** Every account write (fills, exits, settlement) runs as one `DriveAccountSync`, behind E3's existing
  `AccountSync` port and replacing `GitAccountSync` in `fno/desk/daily_wiring.py`:
  - download the book's files from Drive;
  - apply under E1's lock;
  - upload the changed files;
  - then write and commit `daily_totals.csv`.

  The daily run is the only writer of accounts (E3), so the git reset-and-reapply logic for competing writers goes:
  one writer, no merge.
- **The private packs.** E2's pack builder writes each book's `private.json` to Drive beside the account. Only its
  `private.json.sha256` is committed, and D3 records the pack's hash, as today. The books' decisions read the pack
  from Drive (Book 1: `fno/books/book1_inputs.py`).
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
  (the run stopped before its exits), today opens no new entry, with one alert naming the day. Today's exits still
  run, and once they are done the next session opens normally.
Out:
- the raw quote files (A4b);
- D3's decision records and C4's records (they hold no fill or mark; E2b's kept mids stay, as decided);
- any change to how fills are priced (E4, E4c).

**Acceptance criteria:**
1. After a day with fills and exits, no committed file holds a contract's fill price, a mark, cash or marked equity:
   a test runs a fixture day end to end (the pack step included) and scans every committed file, the private packs'
   folders included, for the day's prices and marks.
2. `daily_totals.csv` holds, per book and session, exactly the five columns above, matching the Drive account by
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

**Depends:** A4b (the Drive store), E2b, E3, E4 · **Size:** M · **Status:** story text on `story/e2c-fills-to-drive`,
for the judge's story check (response 148)
