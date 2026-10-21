# E8. Owner-timing fills: every paper trade filled when the owner could really act

**Repository:** trading · **Lane:** 1 (new story; it decides the fill price of every counted paper trade) · **Branch:**
`story/e8-owner-timing-fills` · **Issue:** #109 · **Work register:** row E8 · **Quality rule 9:** it changes how
fills are priced, so a ChatGPT review follows the judge's PASS on the story text and again on the code.

**Description:** As the F&O trader, the risk manager and the owner, I want every paper entry and exit filled at the
first quote snapshot at or after the time the owner received the order plus the owner's reaction time R. The fill must
be at real bid or ask, inside the entry range, or recorded as missed. Every trade is filled at R = 5, 30 and 60 minutes
and E4's 15:15 snapshot, all four are reported, and the verdict uses R = 60. Then a strategy passes or fails on prices
the owner could really have got, and the cost of human delay is measured, not assumed.

**Context and why:**
- **The decisions this story carries out:**
  - owner, 15 Oct 2026, reaction time "5 minutes when available, 30 on average, at most 1 hour"
    (`docs/design_v2/REPLAN.md` section 5, decision 5);
  - "The 60-minute fill decides whether a strategy passes; the 15:15 snapshot is the common yardstick only"
    (`docs/DESK_DECISIONS.md:181`);
  - E8's code joins S1's `frozen_files` (REPLAN section 5, decision 12, option a);
  - the v4 timeline, which gives each decision a skill score at the common 15:15 snapshot and its money verdict at the
    60-minute fill (`docs/DESK_DECISIONS.md:184`, story G10).
- **Design:** `docs/design_v2/03_layers_factory_desk.md:88-102` and `REPLAN_new_stories.md:90-94`.
- **Still open, from the owner:** the availability calendar (REPLAN section 5, decision 5). This story gives its format
  and a default until the owner supplies it (rule 8).
- **What E8a measured** (`research/2026-10-16-fill-timing/results.md`, ledger trial 54, exploratory, candle last trades
  2024-26, not bid or ask). E8a assumed a card at 15:08 (or 14:08), which O1 does not give (see "Card time" below), so
  only its R = 60 cells at 15:00 (next session's 10:15) and at 14:00 (15:15, the same prices as the `e4_1515` view)
  describe E8's real fills. E8a has no 09:30 cell, so the R = 5 view has no historical figure. The entry moves C
  between the decision and the R = 60 fill:

  | Family | Mean \|C\| at 15:00, R = 60 (overnight) | Mean \|C\| at 14:00, R = 60 (= the 15:15 snapshot) | Days C is above 10% of the trade's risk (15:00, R = 60) |
  |---|---|---|---|
  | Long call and long put | about 52-55 points (about Rs 3,400-3,600 a lot) | about 21-25 points | 23-28% |
  | Vertical spreads | about 10-11 points | about 5 points | 4-8% |
  | Four-leg structures (SF, BF, SC) | about 3-4 points | about 2.5 points | 0% |

  Flip shares (wins that become losses when filled later) were small: long call 3.8% at 15:00 against 1.6% at 14:00,
  four-leg structures under 2%. So E8's delay matters a lot for bought options, a little for verticals and almost not
  for protected four-leg structures (some evidence). E8a cannot measure the spread at 09:45 or 10:15, nor what an
  older signal costs; only E8's live record can.
- **Code facts on `main`:**
  - E4 prices one leg at the ask for buys and the bid for sells of a valid A4 quote whose size covers the units. The pad
    is 0, because crossing the spread is the slippage (`fno/desk/pricing.py:1-6`).
  - E4 enforces C2's approved entry as a limit on the net at the touch (`fno/desk/entries.py:14-20`).
  - E4 fills only at E3's one execution snapshot (`fno/desk/timetable.py`, `config.yaml` `desk.timetable`).
  - A16 records NIFTY's index, near future, and weekly and monthly chains within 6% of spot every 15 minutes, with one
    `get_quote` per contract (bid, ask, depth, last trade time) and our own request and response times
    (`fno/intraday/document.py`, `docs/stories/A16-intraday-quote-recorder.md` step 0).
  - The card's delivery record holds Slack's `ts` and the clock checks (`fno/cards/deliveries.py`).
  - The card has no trade fields yet (`fno/cards/card.py:76-78`).

## Card time (judge 193 should-fix 1)

O1's daily run posts the card only after `quotes_done`, which comes after `exits`, so the card is "always after
`decisions` (final at 15:12) and `snapshot` (C3 final at 15:15), so a card never posts before what it shows is final"
(`docs/stories/O1-daily-run.md:88` on `story/o1-daily-run`). So T is 15:15 or later on a normal day, and E8's exit
alerts go out in the same run, after `exits`. Under rule 2, every owner-timing view then fills the next session:
- R = 5: T + 5 is 15:20 or later, so the first mark is 15:30, which is after 15:25. The fill moves to the next
  session's 09:15 + 5, the **09:30 mark**.
- R = 30: the next session's **09:45** mark. R = 60: the next session's **10:15** mark.

Only the `e4_1515` view fills the same day.

## What changes for the owner, said plainly

1. **The book's own account is filled at R = 60.** With today's 15:00 decision, almost every entry fills at about 10:15
   the next session, after the overnight gap. That is what the owner would really get.
2. **Three more views of the same decisions** are kept beside it: R = 5, R = 30 and E4's 15:15 fill. The gap between
   the verdict and the 15:15 view is the measured cost of human delay. The four views are four looks at one decision,
   highly correlated, never four independent trials.
3. **Until A16's routine runs, no owner-timing fill can happen.** R = 5, 30 and 60 need A16's 09:30, 09:45 and 10:15
   snapshots, and nothing else records them, so every such entry is "missed, no quote". Only `e4_1515` fills. A16's routine waits
   for the owner (`docs/stories/A16-owner-checklist.md`). E8's code can merge first, but its verdict starts only with
   A16.
4. **If the delay costs too much, the remedy is an earlier decision and an earlier card, never a shorter R.** An
   earlier decision alone moves nothing: the card still waits for the 15:15 snapshot, so R = 60 stays at 10:15 the next
   session. A 14:00 decision puts R = 60 at 15:15 only if its card goes out at about 14:08. That needs an O1 and T1
   change, with a cost: a card posted before that day's 15:15 data checks are final, or a second, earlier run with its
   own data checks. E8a's 14:00 figures show what it would buy (long call: mean |C| about 25 points against 55). It is an
   S1 `timetable` choice for the owner, from E8a now and E8's live report later.

## Rules

1. **Order time T.**
   - For an entry, T is when the order reached the owner: the Slack delivery time of the card that carries it (T1's
     delivery record, Slack `ts`). An entry whose card was not delivered is "missed, card not delivered".
   - For an exit (E4's exit rules at the daily run, and later LM1's monitor), T is the delivery time of E8's exit alert
     to #fno-desk (`AlertSender`, `FNO_SLACK_BOT_TOKEN`). The alert names the trade and the action, never a price (the
     card rule of 15 Oct 2026). An exit alert that was not delivered is sent again at the next run, and T is its first
     delivery.
2. **Due mark.** The fill mark is the first of A16's 15-minute marks (09:15, 09:30, ..., 15:30) at or after T + R.
   - If that mark is after 15:25, or the owner is away that session (rule 8), the fill moves to the next session's
     open plus R, then to the first mark at or after that.
   - "Next session" comes from A7's calendar: a normal or special session, never a muhurat-only day (it has no 09:15
     mark).
   - With O1's card at 15:15 or later: R = 5, 30 and 60 give the next session's 09:30, 09:45 and 10:15. Only if the card
     moved to 14:08 (point 4 above): 14:15, 14:45 and 15:15.
3. **Snapshot at the due mark.** The snapshot is A16's snapshot of that mark, the copy its ledger row names (hash
   checked).
   - A missing or failed A16 mark may be replaced only by a recorded A4 capture that started within the mark's 2-minute
     window (A16's on-time rule), for example E3's 15:15 execution capture. This is the "falls back to A4 snapshots"
     of `REPLAN_new_stories.md:94`.
   - A fill never uses a later or earlier mark. A mark that exists but is invalid for a leg (stale, one-sided, too
     little size) is treated like a missing one: an entry is missed (rule 7) and an exit waits for the next mark.
4. **Price.** E4's rule, unchanged: a valid quote by A4's rule (two-sided, not crossed, sizes on both sides, a trade
   in the contract that session), the ask for buys and the bid for sells, the size at the touch covering all units,
   pad 0, C1's charges. For an A16 quote, "a trade that session" is read from its `last_trade_time`.
5. **All legs or none.** Every leg is checked at the due mark before any fill (E4c's rule). If any leg fails, nothing
   fills.
6. **Entry rule: price cap only** (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md:220`: "Price cap only
   (Recommended)"). An entry fills only if the net at the touch is no worse than the decision's approved entry (C2's
   entry cash, the limit E4 already enforces); otherwise "missed, price moved". A miss is never filled at another mark
   or price. `EntryRange` stays an interface with this one class, `ApprovedLimit`, wired as decided.
   - Considered, not chosen: a ±0.5% NIFTY band on top (about 32% of overnight entries missed for the band alone, its
     width a guess) and any price (no miss bias, but an entry could cost more than C2 approved).
   - **Funds and risk at the fill** (ChatGPT review 122 point 5, response 190). Approved cash,
     available cash and margin are separate, and each can change between decision and fill (other fills that
     morning, an overnight margin change). So before any entry is written, the existing C2 and C4 entry checks (cash,
     stressed margin, per-trade cap, buckets) run again on the due-mark prices, the current verdict account and the
     pending fills. A shortfall gives "missed, insufficient funds"; a cap or bucket breach gives "missed, over risk cap".
     These are the paper desk's own checks on its own accounts, never Groww's funds or margin API.

   The card shows this same limit and never computes its own (T1's trade fields).
7. **No quote.** An entry is "missed, no quote" when the due mark has no valid quote for a leg. That covers:
   - the mark missing or failed with no stand-in;
   - a leg outside A16's strikes;
   - a stale or one-sided quote;
   - too little size.

   It is never a synthetic fill. An exit without a valid quote stays a pending exit, retried at each following mark,
   and is never missed (E4's rule). Exits are never limited.
8. **Availability calendar** (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md:219`: away dates private in Drive, a salted
   hash in the repository).
   - The repository is public, so away dates are never committed. They live in one private Drive file: a first line
     with a random salt (never committed), then one row per date with `away` or `available`. Dates only: no reason
     and no times.
   - The file is append-only. A date's latest row wins, so an early return is a new `available` row, never a deleted
     line. Because every version is a prefix of the next, the one Drive file holds every version.
   - The repository holds one hash file, `research/desk/availability_seals.csv`, one row per sealed version: the
     SHA-256 of the file's first n lines, and n. The daily run seals the current version in `owner_timing_fills`, at
     the start of the run and so before that day's card. The owner only edits the Drive file.
   - For an order at T, the version used is the last seal committed before T (git's commit time on `main`). Its first
     n lines must hash to the sealed value, or the step is refused (rule 11, fail closed). A row outside that version
     is ignored, and the report counts it as a "late away entry". So "away" can never be chosen after the prices are
     known.
   - In plain words: an away date counts only if it is in the Drive file before the run starts on the session before
     the trade (the decision day, whose run seals the file before the card).
   - **The hashed lines** are the file's first n lines with trailing whitespace and CR removed, joined with LF, so an
     editor re-saving the file with other line endings changes nothing.
   - **Repair after a mismatch.** A changed sealed line (for example the owner fixing an old typo) refuses the step,
     and the alert names the repair: restore the last sealed version from Drive's version history, then append any
     change as a new row. The step never re-seals over a mismatch.
   - The salt is there because a calendar of a few dates is guessable: a bare hash could be reversed by trying
     calendars.
   - Until the owner writes the file, every session counts as available.
   - Default (reasoning only): an entry is valid only until its first available session. If the owner is away on the
     session its fill moves to, it is "missed, owner away". An exit is never dropped: it moves to the next available
     session, or settles at expiry.
9. **Expiry.**
   - An entry whose due mark falls after its contract's last trading time is "missed, contract expired".
   - An exit whose due mark falls after expiry is settled by E7 at NSE's final settlement price, with C1's settlement
     charges. This is what an owner who did not act in time gets.
10. **Views.**
    - Each book has four paper accounts in E1's format, all in the book's private area (E2c's Drive store):
      - `verdict` (R = 60): the book's own account, read by E6, S1, S2 and C2;
      - `r5` and `r30`;
      - `e4_1515`: E4's fill at the execution snapshot, today's behaviour. It is an **unexecutable timing yardstick**:
        it fills before the card exists, so no owner could get it.
    - Each view takes the same committed decisions, fills them by its own clock, and runs E4's exit rules on its own
      positions at each daily run.
    - C2's risk view, the book's limits, the drawdown brake and S1's stop read the verdict account only. The other
      views are diagnostics and can never change them.
11. **When fills are applied** (agreed with O1, 15 Oct 2026, against `story/o1-daily-run` at 71b00878).
    - A daily-run step `owner_timing_fills` runs right after `quotes` and before every other step (`quotes` only
      starts the 3 pm parts and returns at once). The run starts at 14:33 today and 14:05 once G10 goes live, so the
      09:45 and 10:15 marks have always passed: nothing new is scheduled.
    - It applies every pending entry and exit whose due mark has passed, oldest first, and catches up after a missed
      run.
    - It prices only from that mark's recorded snapshot, so a late run gives the same fill.
    - It is idempotent: E4's fill IDs, with the view added. A rerun of the daily run skips a recorded step (O1's rule).
    - Shape: one `DayStep` class (`run(day) -> StepOutcome`, interface in `fno/desk/daily_ports.py`) in E8's package,
      listed with one line in O1's `fno/daily/wiring.py`. Its outcome carries `status` (ok, failed, refused, not_live)
      and `reason`, which O8 reads, and its account files go through E3's committer, in the run's one thread.
    - The step name joins `DAILY_RUN_STEPS` (`fno/constants_operations.py`, re-exported by `fno/constants`), so O8's
      health check expects it.
    - **A failed step fails closed for new risk.** If the step fails or is refused (Drive down, a hash mismatch), C2
      would see yesterday's positions without today's fills and understate open risk. So that day no book opens a
      new entry, through E2c's per-book `_unreviewed` block, while exits still run. O1's `Alerted` wrapper sends one
      alert and the run goes on.
    - **Its own time limit** (judge D, judge 178 addendum 5; judge 193 addendum 4). The step has 10 minutes, O1's
      part limit. A timer cannot stop a thread stuck inside a read, so the limit is enforced by the reads themselves:
      every Drive and A16 read the step makes carries a network timeout of 60 seconds, and the step checks its
      10-minute deadline before each read. A timed-out read or a passed deadline is a step failure (new entries fail
      closed, exits still run), so a hung read can never hold up the day's exits.
    - **The live date** (`daily.live_from.owner_timing_fills`, none by default; response 286). Each decision is handled
      once, on its own day, by that day's rule:
      - an entry decided before the date is filled by E4 at 15:15 and never queued;
      - an entry decided on or after it is handed over and filled by E8;
      - an exit E4 left waiting before the date (a protective leg without a quote) and still open on it is alerted at
        that day's exit review and finished by E8 at its due mark.

      Legs E4 already closed are never closed again (`tests/desk_owner_timing/test_live_boundary.py`).
12. **Point in time.**
    - The decision must be committed before its card's T.
    - T must come from a delivery record.
    - The snapshot used must have finished after T + R.
    - A fill row carries the snapshot's hash, the due mark, R, the view and T.
    - Nothing is filled from a snapshot recorded after the run's clock.

## Expected design

All new code lives in one package, `fno/desk/owner_timing/`. Every file except `cli.py` joins S1's `frozen_files`;
`wiring.py` is in. E4's desks are reused, not copied.

- **`FillClock` (strategy).** Gives, for an order time, the due mark or the reason it is missed.
  - `OwnerTimingClock(r_minutes, sessions, availability)` for R = 5, 30 and 60.
  - `ExecutionSnapshotClock` for E4's 15:15 view.
- **`MarkSnapshots` (interface plus adapters).** Gives `at(day, mark) -> ExecutionSnapshot`, or the reason there is
  none.
  - `IntradayMarkSnapshots` maps A16's document to E4's `ExecutionSnapshot`, using A4's validity rule through
    `quote_from_row`'s logic, never a second copy of it.
  - `CaptureStandIn` gives an A4 capture inside the mark's window.
  - `FirstAvailable` composes the two.
- **`Availability` (interface).** `SealedDriveAvailability` reads the private Drive file and checks it against the
  last seal committed before T (rule 8); `AvailabilitySealer` writes the day's seal.
- **`EntryRange` (interface).** One class, `ApprovedLimit` (C2's limit, the owner's rule 6). Another rule, such as a
  card range from T1, would be one class plus one line in `wiring.py`, through an owner decision and S1.
- **`PendingOrders`.** The private store of entries and exits waiting for their due mark, in E2c's Drive store,
  written through E2c's journal.
- **`OwnerTimingStep`.** Rule 11's daily-run step.
- **`TimingViews`.** The four view accounts, built in `wiring.py`.
- **`TimingReport`.** Per book, strategy version and view, it gives:
  - orders, fills, and misses by reason;
  - the entry move C against the decision price (E8a's measure);
  - net P&L after C1, both per executed fill and per eligible opportunity (a missed entry is 0 P&L but stays in the
    denominator and in the fill rate; ChatGPT review 122 point 1);
  - the delay cost (verdict minus `e4_1515`);
  - sessions pending;
  - the late away entries.
  - from the first day, over the whole opportunity set, fills and misses split by NIFTY's move between the decision and the due mark, against the
    trade's direction. With a price cap, bought options fill mostly on mornings that went against them (adverse
    selection), so their paper results run below what the 15:00 idea alone would earn. Without this split, the owner
    could read a miss-skewed record as "the strategy is bad".

  Prices stay in Drive. The public repository gets daily totals per view only (E2c's rule). LR1's weekly post-mortem
  may cite it.

## Scope

**In:**
- rules 1-12 for every paper entry and exit of every book and shadow candidate;
- the four views and the report;
- the exit alert;
- the A16 snapshot adapter;
- the availability file and its commit-time check;
- the daily-run step;
- the S1 items below.

**Out:**
- real orders (never);
- LM1's monitor and LM2's intraday exits (they use E8's clock when built);
- the card's trade fields (T1 slice B);
- choosing the decision time (the owner);
- changing R (owner decision 5);
- any entry condition other than the owner's price cap (rule 6).

## S1 items (agreed with S1's text owner, session 0185gR5D, 15 Oct 2026)

1. **`frozen_files`.** S1's freezer takes every backticked path as one file and refuses a glob, so the rule is stated
   in prose, in the sentence that already names S2, S3, S6, F8 and F9: "... the code of F8, F9 and E8's owner-timing
   package, except its cli.py". The explicit paths go in at the freeze; `wiring.py` is in.
2. **`timetable`.** These lines go in, with status "proposal, owner decides" except where an owner row is cited:
   - a paper order's time T is its delivery time to #fno-desk (the card for entries, E8's exit alert for exits);
   - the fill is at the first 15-minute mark at or after T + R, from that mark's recorded snapshot only (an A4
     capture inside the mark's 2-minute window stands in for a missing mark); a mark after 15:25, or an away session,
     moves the fill to the next session's open plus R;
   - every paper trade is filled at R = 5, 30 and 60 minutes and at the 15:15 execution snapshot, all reported; the
     verdict uses R = 60 (`docs/DESK_DECISIONS.md:181`, owner, 15 Oct 2026), the 15:15 snapshot is the common
     yardstick;
   - an availability-calendar row counts only if committed before the card it applies to; later rows are ignored and
     listed;
   - E8's fills are applied by the daily run's first step after `quotes`; when it fails, no new entry opens that day
     and exits still run.
3. **The decision time** (15:00, or 14:00) waits for the owner. This matches G10's open note 3 (judge 161 addendum 3).
4. **The entry rule: closed.** The owner chose the price cap on 16 Oct 2026 (`docs/DESK_DECISIONS.md:220`), so
   `ApprovedLimit` is wired as decided, not as a pending default.
5. These land in `PROTOCOL.md` with S1's next edit, by its text owner.

## Owner decision on the entry rule (16 Oct 2026, closed)

The owner chose "Price cap only (Recommended)" (`docs/DESK_DECISIONS.md:220`; ChatGPT review 122 agreed). The cost,
said plainly (E8a, 15:00 decision, R = 60, some evidence): a bought option's price moves by more than 10% of the trade's
risk on 23-28% of mornings, so many entries miss, and the fills that remain are mostly mornings that went against the
idea. That is what a real limit order gets. The report's NIFTY-move split and the per-opportunity P&L show it from day
one. The ±0.5% band figure behind the choice was about 32%, not the 17% of an earlier draft (the 09:15 open's gap).

## Part 2's report (ChatGPT review 128, accepted in response 228)

`TimingReport` (part 2) adds these to the list under "Expected design". It reads E6b's shared
`ExecutionOpportunities` counter, so E6 and E8 never count opportunities two ways.
1. **One cohort, four views.** R = 60 stays the frozen verdict. R = 5, R = 30 and `e4_1515` are diagnostics on the
   same decisions, never separate trials. Each view shows:
   - its fill rate;
   - its net per filled trade and per opportunity;
   - the same overnight-gap rows (item 2).
2. **Adverse selection from the price cap.** Every eligible opportunity is split by the sign and size of NIFTY's move
   between the decision and the due mark: against the trade, flat (under 0.25%), with the trade, and above or below
   1%. The edges 0.25% and 1% are reasoning only, fixed before the first report. Each row shows:
   - opened against `missed, price moved`;
   - net per filled trade and per original opportunity;
   - each trade's direction (bullish, bearish or neutral) and structure.

   A missed trade is never booked as realised profit or loss. No move filter is added without evidence.
3. **Misses in the denominator** (response 221, E6b):
   - A miss that reached the fill step adds 0 to realised profit or loss and stays in the opportunity count.
   - `missed, no card` (delivery) and `missed, owner away` (availability) stay in the owner-achievable count, but are
     shown on their own rows, apart from market-execution misses (no quote, no future, price moved, expired, funds,
     risk cap).
   - A gate refusal (`refused`) is outside the count.
   - A pending entry is in neither count until it resolves.
   - A partial unwind counts its real cash.
4. **Order of a morning's fills.** Within one book, items are filled oldest T first. Each is written before the next
   one's check reads the account, so earlier entries use funds first; books never share cash. Equal T values keep the
   step's fixed order: books in config order, then entries before exits, then the records' order.
5. **Known limits, reported and never hidden:**
   - A16 records only the near-month future, so a further-month expiry gives `missed, no future for that expiry`
     rather than a made-up future.
   - A day with no exit review orders no exit. The book stays exposed and flagged, with no backdated exit.

## Acceptance criteria

1. **Clock.**
   - A 15:16 card maps to the next session's 09:30, 09:45 and 10:15 (R = 5's 15:21 needs the 15:30 mark, after 15:25).
   - A 14:08 card (only if the card moved earlier) maps to 14:15, 14:45 and 15:15.
   - A Friday 15:16 card's R = 60 fill falls at Monday's 10:15, or at the next A7 session's open plus 60 minutes.
   - A muhurat-only day is skipped.
2. **Delivery.** T is read from the delivery record. An undelivered card gives "missed, card not delivered". An
   undelivered exit alert is sent again and fills from its first delivery.
3. **Snapshot.**
   - The fill uses exactly the due mark's A16 copy named by its ledger row, hash checked.
   - A missing mark uses an A4 capture only inside the 2-minute window.
   - A changed file is refused.
   - No test fills from a neighbouring mark.
4. **Price.** A fixture quote fills at the ask for a buy and the bid for a sell. A one-sided, crossed, sizeless or
   no-trade quote, or too little size, fills nothing and gives "missed, no quote" for an entry or a pending exit for an
   exit.
5. **All or none.** A four-leg entry with one bad leg writes no fill and no ledger row.
6. **Entry rule** (the same trade is never filled at a later mark):
   - A net at the touch one paisa worse than the approved entry gives "missed, price moved"; exactly at it, it fills.
   - The wired rule is `ApprovedLimit` (a wiring test).
   - A maximum loss on the fill prices above the per-trade cap gives "missed, over risk cap".
   - Funds: a bought option whose debit at the due mark is under the loss cap but above the verdict
     account's available cash gives "missed, insufficient funds"; a credit vertical with loss headroom but too little
     stressed margin gives "missed, insufficient funds"; a pending fill earlier that morning counts against both.
7. **Availability.**
   - An `away` row in a version sealed before T moves the fill to the next session.
   - A row appended after the last seal before T is ignored and counted as a late away entry.
   - A Drive file whose sealed prefix no longer matches its hash (a line changed or deleted) refuses the step, with an
     alert naming the restore; the step writes no new seal. The same file restored to its sealed version passes.
   - The same lines saved with CRLF endings or trailing spaces hash the same as with LF.
   - No committed file holds a date or the salt (the committed-file scan).
   - An entry whose moved fill lands on another away session gives "missed, owner away".
   - An exit keeps moving.
8. **Expiry.** An entry due after its contract's last trading time gives "missed, contract expired". An exit due after
   expiry settles at NSE's final price through E7.
9. **Views.**
   - One fixture decision gives four view fills at their own marks.
   - Only the verdict account changes C2's view.
   - The `e4_1515` view equals today's E4 result on the same fixture, bit for bit, and the report labels it an
     unexecutable timing yardstick.
   - Isolation, both ways: a fixture where `e4_1515` profits while the verdict misses or loses, and the reverse, gives
     identical verdict-account cash, caps, drawdown brake and S1 stop with the diagnostic views on or off.
10. **Daily step.**
    - The step runs right after `quotes` and catches up after a missed run, oldest first.
    - A planted step failure gives no new entry in any book or view that day, and `exits` still runs.
    - A fake Drive read that never answers hits its 60-second network timeout (a short timeout in the test); the step
      fails, no new entry opens, and `exits` still runs. A run of slow reads that passes the 10-minute deadline fails
      the same way.
    - Running it twice changes nothing.
    - A fill's row carries the snapshot hash, the due mark, R, the view and T.
11. **Report.** It gives every figure listed under `TimingReport`, the NIFTY-move split included (a fixture with one
    favourable and one adverse morning puts each in its own row). It labels the views "four views of one decision,
    not independent trials". It writes no price to the repository (the committed-file scan of E2c).
12. **Read-only.** The package's import closure reaches no order, position, margin or funds call (A16b's test
    pattern). The funds checks of rule 6 are the desk's own C2 and C4 checks on paper accounts, never Groww's.
13. **Size and wiring.**
    - No file over 350 lines.
    - Concrete classes are wired only in `fno/desk/owner_timing/wiring.py`.
    - Fixed strings and the step name are in `fno/constants.py`.

## Test plan

- Unit tests with fixture A16 documents, A4 captures, a fake delivery record, a fake git history for the availability
  file and E2c's fake Drive store: rules 1-12, one test each.
- One end-to-end fixture week: Monday to Friday plus a holiday and an away day, with an entry and an exit per view,
  checked by hand.
- The read-only closure test.
- A mutation pass:
  - a neighbouring mark;
  - a later away row counted;
  - R = 60 swapped for R = 30;
  - the bid used for a buy;
  - a partial leg fill.

  Each must fail a test.

## Judge verifies

- Recomputes the fixture week by hand: marks, prices, misses and the four views.
- Plants the mutations above and sees each test fail.
- Checks the frozen-file list against the package, and that the `e4_1515` view is today's E4 path unchanged.

## Build order

The code waits for E2c (the Drive journal) and E4c (all legs checked first), because E8 writes through the first and
relies on the second. It is built in two parts, both before S1's freeze:
1. the clock, the snapshot adapter, the availability file, pending orders, the verdict account and the daily step;
2. the three other views and the report.

**Depends:** E4, E4c, E2c, E3, E7, A7, A16 (the live routine, for any next-session fill), T1 (delivery record; trade
fields for the card's range), C2 · **Size:** L. Issue #109 says M; four view accounts, the pending-order store and the
A16 adapter make it larger, so it is built in the two parts above · **Status:** story text, revision 1 (for the judge)

**Evidence labels:**
- The fill rules carry out owner decisions and need no evidence.
- E8a's figures are some evidence: exploratory, candle last trades, 2024-26.
- The single-session entry validity, the 2-minute stand-in window and the ±0.5% band in the open question are
  reasoning only.
- E8's live record will be the first evidence of what the owner really gets.
