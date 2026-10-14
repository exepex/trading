# Response 88: story S2, scoreboard B: design proposal before building

Builder: Claude, 14 Oct 2026, for the orchestrator and the judge. This is not the claims file; S2's claims follow as
addenda here once it is built. I wrote it first because several of S2's sources do not exist yet, and the way around
each one is a design choice the judge should see before it is code.

## 1. What S2 reads, and what exists today

| Source the story names | State on main today | What S2 does |
|---|---|---|
| E1 accounts (`cash_ledger.csv`) | built | the money: every fill, every charge |
| E1 `equity_history.csv` | **never written after the opening row**: no code calls `record_equity` | not used. Each day's value is rebuilt from the stored snapshots instead (2 below). The equity history may be checked against that later. |
| E4 desk records (`desk_fills.csv`, `desk_events.csv`) | built | which trade is which version (`strategy`), its decision ID, and how each attempt ended |
| C1 three ledgers | built (`Ledgers`) | trade lines (gross, pads, charges, net), by month, tax scenario; S2 criterion 2 reconciles to them |
| C1 operating costs per book | **no file exists for any book** | read `journal/<book>/operating_costs.csv` in C1's own columns (`month,item,category,amount_rs,source`) through a port. A missing file means none recorded, and the report says "no operating costs recorded", not zero spend. |
| F8 allocated AI cost | **not built** | a port, `AllocatedAiCost`. Until F8, the report shows "not available: F8 not built" and never a number. Book 1 has no AI, so its figure is a true Rs 0. |
| D6 versions and segments | built (`segments`, `journal/versions.csv`) | each trade belongs to the segment of the decision that opened it |
| D3 decision records | built | the maximum loss at entry, the stressed margin and the stress loss of each opened trade (its chosen record's `risk` and `validity`), and `owner_override` |
| F4 overridden trades | **not built**; D3's header already has `owner_override` (always empty today) | a trade whose opening record has a non-empty `owner_override` is "overridden", scored apart. This is ready for F4 and is a no-op until then. |
| S1 protocol | passed (judge 85 add. 1), **not merged; a draft, not frozen** | S2 applies its rules (common start, pilot, ratio of means, block bootstrap). Every output says which protocol version and whether it is frozen. Until the freeze, every figure is labelled "protocol not frozen: provisional". |
| E3 run log (`journal/runs/<day>.json`) | built | the day's execution snapshot ID, to mark open trades on that day |

## 2. The daily series (the heart of S2)

Net per unit of risk (protocol `primary_metric`) is the period's mean daily net change divided by its mean daily risk
at stake. Both means run over the same days, so this equals **total net change / risk-days**. The bootstrap
(`uncertainty_criterion`) needs the daily pairs themselves.

Each trade is valued on each session day it is open. The value is its cash flow so far plus its legs at the mid of
that day's execution snapshot, the same marks E6 uses. That gives:
- **Daily net change** of a book or a segment: the sum of its trades' value changes that day, minus operating costs
  dated that day. C1 dates operating costs by month only, so they are booked on the month's last session (rule 3).
- **Daily risk at stake:** the sum of the maximum loss at entry (from D3) of every trade open that day.
- **A leg with no valid mid:** the last valid mark is used and flagged stale, as E1 does. A trade with no valid mark
  ever is shown as unvalued, and those days are listed. No price is invented.

All of this is rebuilt from committed records, so a rebuild gives the same bytes (criterion 4).

## 3. Rules I propose (reasoning only; the judge or owner may change them)

1. **The segment of a trade** is the D6 segment of the D3 decision that opened it. Its later value changes stay in
   that segment even after a new version is registered. A version is credited with its own trades to their end.
2. **Common start:** the S1 rule, read from the records: the first session on which every book has an on-time
   committed decision under a registered version. Books 2 and 3 are not built, so today **everything is pilot**. The
   output says "common start: not reached" and puts all of Book 1's figures in the pilot section.
3. **Operating costs** are booked on the last session of their month, so the daily series and C1's month table
   agree.
4. **Margin-days:** the stressed margin at entry (from D3's `margin_room` numbers) times the session days held. It
   is not re-margined daily: the daily stressed margin is not recorded anywhere. Labelled "at entry margin".
5. **Stress usage:** the stress loss at entry (D3's `stress_loss` numbers) as a share of the owner's stress limit.
   Reported, never the verdict.
6. **Uncertainty** is computed only where the protocol allows a claim. Its figures (block 20, 10,000 resamples,
   seed 20261014, nearest-rank 5th percentile) are named constants in the scoring module. A test checks that each
   one appears in the protocol's `uncertainty_criterion` text. The S1 freeze then hashes the module.
7. **Output:** `research/scoreboards/B/<date>.json`, canonical JSON (sorted keys, fixed rounding to the paisa),
   with:
   - per book: overall, head-to-head, pilot, unscored and overridden sections, each with the full detail list of
     design 12.5;
   - per segment;
   - the inputs it read, with their SHA-256 (so the judge can rebuild it).

## 4. Questions for the orchestrator (I proceed on the proposals above unless told otherwise)

1. Is reading D3's `owner_override` as the F4 hook acceptable, rather than waiting for F4's format?
2. Rule 2: should Book 1 also get a "since its own first decision" view, clearly labelled pilot, so the owner sees
   something before books 2 and 3 exist? I propose yes, since the pilot section is exactly that.
3. Should S2 also start writing `equity_history.csv` daily (an E3 change), or leave that file to a separate story?
   I propose a separate story: S2 should read records, not change the desk.

## Addendum 1: S2 built (builder's claims)

Built as proposed above. The orchestrator had not answered the three questions when I built, so I followed my
proposed answers. Package: `fno/scoreboard/`, 16 modules, the largest 81 lines. Composition root:
`fno/scoreboard/wiring.py`. Command: `python -m fno scoreboard b [--on YYYY-MM-DD]`, which writes
`research/scoreboards/B/<date>.json`.

### The modules

| Module | Job |
|---|---|
| `daily_values.py` | each trade's value per session: cash moved plus legs at mid; stale and unvalued days flagged, never invented |
| `committed_runs.py` | the runs E3 collected (run ID and commit), on time when committed before the snapshot started; each day's valid snapshot ID |
| `entry_facts.py`, `entry_decisions.py` | from the committed D3 record of each trade: max loss, stressed margin and stress usage at entry, `owner_override`, the D6 segment (computed once over all records); the common-start rule |
| `book_trades.py` | E1 fills and C1 trade lines, E4 version and decision, D3 entry facts, daily values; groups: segment, `unscored`, `overridden` |
| `series.py` | daily (net change, risk at stake) pairs; costs on their month's last session; net per unit of risk = total net / risk-days |
| `uncertainty.py` | S1's block bootstrap and sample rule, its figures as named constants |
| `sections.py` | every design 12.5 number for one group and period |
| `book_board.py` | overall, pilot, head-to-head (overall and per segment), unscored, overridden |
| `reconcile.py` | criterion 2 |
| `whole_system.py`, `sources.py`, `ports.py`, `protocol_status.py`, `cli.py` | assembly, adapters, interfaces, output |

### Evidence (`tests/scoreboard/`, 24 tests)

- **Fixture histories for three books** (E1 and E4 records written by the real account writer; D3 records and E3
  run logs in the desk's format). Book 1 has four trades:
  - p1, pilot;
  - h1, head-to-head;
  - o1, overridden;
  - u1, no committed record.

  Book 2 has one open trade and Rs 500 of October data costs. Book 3 is started with no trades.
- **Criterion 1:** every section of every book has every key of design 12.5's list. The risk block has max loss, risk-days,
  mean daily risk, net per unit of risk, margin-days and stress usage.
- **Criterion 2:** all three accounts reconcile. A charges table changed after the fills fails the trade-ledger check
  while the cash ledger still agrees, so reconciliation is a real check, not a formality.
- **Criterion 3:**
  - p1 appears only in the pilot section; o1 only in overridden; u1 only in unscored. Head-to-head holds h1 alone.
  - Without the common start, there is no head-to-head section and every trade is pilot.
  - The common-start rule: a late run does not start the comparison. An unscored run keeps its book paused until a
    new version is registered. A book with no registered version never starts it.
- **Criterion 4:** writing twice gives the same bytes, and the bytes equal the canonical JSON. The inputs' SHA-256
  values are listed in the file.
- **Known answers by hand:**
  - daily values;
  - the sum of a closed trade's daily changes equals C1's net;
  - h1's net per unit of risk equals net / (Rs 6,000 × sessions held). The 20 Oct 2026 holiday is correctly not a held
    session;
  - an open trade at its marks, minus operating costs;
  - costs in the common-start month count head-to-head, not pilot;
  - the bootstrap bound equals an oracle written separately in the test.
- **Mutations** (`python -B`, caches cleared): 23 of 23 caught. They cover stale marks, risk days, cost booking and
  sign, ratio of means, the pilot split, the overridden filter, the on-time and scored rules, late detection,
  reconciliation, the sample rule, the percentile, `owner_override`, AI cost, margin-days, closed-after-the-report-day
  and Book 1's zero AI cost. Two first-round survivors needed new tests (the percentile, net minus AI cost); two more
  needed new tests too (a trade closed after the report day, costs of the common-start month). One survivor was dead
  code (two months cannot share a last session), and I removed it.
- **Smoke run on the real repository records:** three started accounts, no trades. Common start not reached; every
  account reconciles.

### What the owner and judge should know (doubts, plainly)

1. **There are no real figures yet.** Book 1 has no approved strategy and books 2 and 3 are not built, so today's
   board is all zeros and "common start not reached". The code is tested only on fixtures.
2. **Margin-days use the margin at entry,** not a daily re-margin (that is not recorded anywhere). It is labelled in
   the output.
3. **Stress usage** is the book's worst stress loss with the new trade, as a share of the limit, at entry (C2's own
   number). It is not a per-trade stress figure, because C2 does not separate one.
4. **An entry unwound the same day adds its cost and no risk-days.** That is correct under "risk held at the day's
   close". It means a book that only ever unwinds shows a cost with no risk.
5. **Reconciliation recomputes C1 from today's charges table.** If the table changes after fills, the board fails
   reconciliation instead of hiding the drift. Whether C1 should instead price each trade at the table in force when it
   filled is a C1 question for later.
6. **The protocol is not frozen.** Every board says "not frozen: figures provisional" until S1's freeze record exists.
   Holm's correction across claims is a review step (S4), not S2.

## Addendum 2: the orchestrator's answers, applied

1. **F4 hook:** D3's `owner_override` is now read behind a port. `OwnerOverrides` is implemented by
   `RecordedOwnerOverride` and wired in `wiring.py`. F4 itself is not built.
2. **Pilot view:** the pilot section is labelled "pilot, not counted" in every board. Before the common start the
   label adds "common start not reached".
3. **Daily equity history:** it is its own story, **E3-equity-history** (E3 calls E1's `record_equity` each session).
   It is not built in S2. S2 rebuilds daily values from the recorded snapshots and does not depend on it.
4. **Uncertainty figures:** these are S1 proposals the owner has not decided. Each uncertainty block in the output
   says `"figures": "S1 proposal, provisional: not decided by the owner"`, and the module docstring says the same. The
   test against the protocol text only checks that the code and the draft agree; nothing claims they are frozen.

**Scope check against "fewest moving parts".** Ports: the three named (operating costs, F4 overrides, F8 AI cost)
plus `ProtocolStatus`. `ProtocolStatus` is a value read from S1's files, not a port to a missing service. The pieces
beyond the four acceptance criteria, and why each stays:
- **Stale and unvalued marks:** without these, an open trade on a day with no valid quote would need an invented
  price.
- **The SHA-256 of the inputs:** these let the judge rebuild the board from the same records (criterion 4).

## Follow-ups (written down, not built)

1. **E3-equity-history:** write `equity_history.csv` every session (orchestrator's story).
2. **C1 pricing:** price each trade at the charges table in force when it filled. Today reconciliation fails if the
   table changes later, which is shown, not hidden.
3. **Daily stressed margin:** for margin-days, record it each session. Today it is the margin at entry, labelled.
4. **Holm's correction across claims** belongs to the S4 review, not S2.
5. **Quote snapshots in the input hashes:** the board hashes the run logs that name the snapshots, not the snapshot
   files. Adding them would make the hash list self-contained.

## Addendum 3: judge 87's must-fix (the AI cost counted in every section), fixed

**Accepted.** I checked it against the code. `BookBoard._section` called `ai.allocated(book, first, last)` for every
section, and the pilot period (first to the run date) overlaps the head-to-head period (common start to the run
date). Segments, unscored and overridden sections each charged it again. With F8 built, an AI book's net would have
been wrong in every section; today it was hidden because F8 returns no figure.

**Fix** (`book_board.py`, minimal): the AI cost is charged only at book level, over periods that do not overlap:

| Section | AI cost charged |
|---|---|
| Overall | first to the run date |
| Pilot | first to the day before the common start |
| Head-to-head | common start to the run date |
| Segments, unscored, overridden | none; they say "charged at book level only", and their net is the raw net |

**Test:** a fake allocation of Rs 10 a day. Pilot (Rs 30) + head-to-head (Rs 80) = overall (Rs 110). Unscored,
overridden and a real segment carry no AI cost.

**Mutations:** 3 of 3 caught:
- the pilot charged to the run date;
- every section charged;
- each section charged over its own trade period.

**Follow-up (judge, not blocking; owner's call):** pro-rating operating costs. Today they are booked on their
month's last session, so the common-start month's costs go wholly to head-to-head.

## Addendum 4: merged; the judge's follow-ups (judge 87 addendum 1, not blocking, not built)

S2 passed at 771d508 and is merged into main as a9a3cd1, with 2,996 tests passing on the merged tree.

Follow-ups 6 and 7 below extend the list in addendum 2.

6. **An AI book with no allocation:** the segment, unscored and overridden sections should show `net_rs` as null,
   like the book-level net. Today they show the raw net, while the book-level net is null until F8.
7. **Once F8 exists:** test that an empty pilot period (common start = the first session) gives a pilot AI cost of
   0.
