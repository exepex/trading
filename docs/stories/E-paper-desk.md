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
- **two stated exceptions**, put to the owner together with the open question of whether paper fills should move to
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
   one spot per recorded chain. A chain whose rows carry no spot keeps its `spot:` item with no value, and a refused
   `spot:` item counts as missing; C3 names the chain and fails, so the 0.2% agreement is never skipped (test).
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
   committed (tests: refused, allowed, mixed list, empty list, `.CSV`, `../`, symlink, folder, earlier-staged file).
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
