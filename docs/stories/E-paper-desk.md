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
  under the book's lock, dated, with its amount and the cash after it; never edits or removes an earlier row;
- the account's **capital**: the opening row plus every top-up dated on or before a day; the account's cash, closed
  equity and marked equity include it;
- every reader of the opening cash moved to capital:
  - E1's state and `positions.json`;
  - C2's risk view (closed-equity series, paper-account rule);
  - C4's own ledger read (its capital, cash, closed-equity series and paper-account check);
  - P10's Home figures (profit and loss against capital as of each day);
  - S2's reconciliation (cash change against capital);
- a command `python -m fno account top-up [--book ...]` that tops each book up to its profile's `paper_account_rs`.
  The amount is computed, never typed. It is refused when the book is already at size, above it, or not started, or
  when the book has open positions (its marked equity would need marks). The equity history gets that day's row.
- run once per book after the judge's PASS and the merge, by the orchestrator or the owner, and the data committed
  (lane 1: `journal/`). Never run by the builder on the real journal.

Out:
- withdrawals and any capital decrease;
- top-ups of the Manual account (none exists; MA1);
- S2's benchmark returns per rupee of capital (S2 change; noted: a capital flow must not count as return);
- any change to a frozen file.

**Design:**
- `fno/books/fills.py`: `top_up_row(entry_id, day, amount, cash_before)`; `CAPITAL_KINDS = (opening, top-up)`; fills
  stay `FILL_KINDS` only, so no position or trade ever includes a top-up.
- `fno/books/account.py`:
  - `PaperAccount.capital(on: date | None = None)`: the opening plus top-ups dated on or before `on` (all when None).
    It replaces `starting_cash()`.
  - `AccountWriter.top_up(day, target)`: appends `top_up_<day>` for `target − capital`, refused as in Scope. Idempotent:
    the same day's entry already recorded returns False. Writes the day's equity row from the unmarked state (exact,
    as the book is flat).
- `fno/books/equity.py`: `account_state(capital, ...)`; the state's field renamed from `starting_cash` to `capital`,
  every reader updated.
- C2 `fno/risk/book_view.py`: the closed-equity series is the account's capital (as of the decision day) plus the
  cumulative closed profit and loss. The capital is constant across the series, so a top-up shifts the whole series
  and never creates a new high; the brake measures drawdown of profit and loss only. `PaperAccountSize` compares
  capital.
- C4 `fno/checks/validity_account.py` (its own read, no E1 code): capital rows are the opening and top-up rows filled
  by the cutoff. They count in cash and capital, never in trades. The closed-equity series uses the capital as of the
  cutoff throughout, and the paper-account check compares that capital.
- P10 `fno/market_read_models/home_inputs.py`: `pnl = marked equity − capital(day)`.
- S2 `fno/scoreboard/reconcile.py`: the cash change is measured against capital.
- Wiring: the command in `fno/books/cli.py`, the target from `fno/composition.py` (`paper_account_rs`).

**Acceptance criteria:**
1. A top-up appends exactly one `capital_top_up` row to a started, flat book whose capital is below the books' size:
   amount = Rs 20,00,000 − capital (Rs 15,00,000 for a Rs 5 lakh book), `cash_after` = cash before + amount; every
   earlier row is byte-for-byte unchanged (test reads the file before and after).
2. Refusals, each with a named reason and nothing written: a book already at Rs 20 lakh (a second run: "already at
   size", idempotent), a book above it, a book not started, a book with an open position, a write without the book's
   lock.
3. Capital is the opening plus top-ups dated on or before a day: for the 13 Oct book topped up on day T, capital is
   Rs 5,00,000 on T − 1 and Rs 20,00,000 on T. Cash and closed equity include it; no trade, fill, position or C1
   ledger line contains it (tests on E1's state, `positions.json`, `trade_positions` and C1's three ledgers).
4. C2 after the top-up: `paper_account` passes for a topped-up book and still refuses a Rs 5 lakh book; the drawdown
   brake is unchanged by a top-up:
   - a book Rs 1,30,000 below its high stays braked after a Rs 15 lakh top-up;
   - a book at its high does not get a higher high-water mark from it;
   - closed equity minus the high-water mark is identical before and after the top-up (tests at, under and over the
     Rs 1,20,000 brake).
5. C4 reads the same ledger independently and agrees with C2 on capital, cash, the brake and the paper-account check
   (test on one ledger; C4's independence test still passes).
6. P10 Home: on days before the top-up the book's `pnl` is 0 against Rs 5 lakh; on and after it, 0 against Rs 20 lakh;
   never −Rs 15 lakh (test over a date range).
7. S2's reconciliation still holds to the rupee with a top-up in the ledger (test).
8. The command tops up all three books (or `--book`), prints one line per book (topped up by Rs X / already at size /
   refused: reason), and exits non-zero if any book was refused.
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
| Point in time (C4 reads rows by its cutoff) | 3, 5 |
| Capital flows are not returns (S2 benchmarks, design 03 change 4) | out: S2's change; recorded here so S2 inherits it |
| Withdrawals | out: no owner decision |

**Test plan:** `tests/books/test_top_up.py` (criteria 1-3, 8, 9); C2's `tests/risk/test_top_up_brake.py` (4); C4's
`tests/checks/test_validity_top_up.py` (5); P10 and S2 tests extended (6, 7). Every criterion broken on purpose once
(`PYTHONDONTWRITEBYTECODE=1`).

**Judge verifies:** tops up a copy of the three committed books and diffs the ledgers; plants a brake case (a book
Rs 1.3 lakh down) and checks that the top-up leaves it braked in C2 and C4; runs Home over the top-up day.

**Depends:** E1, C1, C2, C4, C5 (the `paper_account` rule and the books profile), P10, S2 · **Size:** S · **Status:**
story text for the judge's check before code (claims: `reviews/claude/response_110_e1-topup.md`)

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
