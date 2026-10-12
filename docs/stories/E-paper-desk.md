# Epic E: code-only daily paper desk

Roles: head of desk (owner), F&O trader, risk manager, portfolio manager. Goal: paper-trade the first approved
strategy every trading day at about 3 pm exactly as tested, with no AI (design sections 4 and 10 step 3). Template
and shared definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## E1. Daily 3 pm loop

**User story:** As the owner, I want the desk to run every trading day at about 3 pm (check data, evaluate rules,
check risk and validity, paper-fill, review open trades), so that the first approved strategy is paper-traded exactly
as tested.

**Background:** Owner decisions: decisions once a day at about 3 pm; holdings up to 2-3 weeks; paper account Rs 5 lakh.
Design 2.2 and 8: fresh quote check before a fill; protection bought first and sold last.

**Scope.** In: the daily sequence, paper fills, exits, scheduling. Out: real orders (never), intraday watching
(later, only if proven useful).

**Expected design:** `fno/desk/daily_loop.py` (`DailyDesk.run(now)`) composed in `fno/live/services.py`: A4 snapshot,
C3 data checks, D2 evaluation, C2 risk, C4 validity, paper fill, open-trade review, D3 records, E2 report.
**Fill model (stated as a model, not a guaranteed fill):** a leg fills at the ask (buy) or bid (sell) of a valid quote
taken within 2 minutes before the fill, only if the quote's size covers the lot; otherwise that leg does not fill.
Legs are filled in order: protective legs first, then short legs; if a protective leg does not fill, nothing opens;
if a short leg does not fill after the protection filled, the protective legs are sold back at their bids (legging
cost recorded) and the trade is "not opened: partial fill". Exit: short legs bought back first, then protection sold;
a leg without a valid quote becomes a **pending exit** with an alert, retried every 15 minutes until the close and the
next day; never an invented price.
**Scheduling:** one run per trading day, idempotent (a run id per day; a second start sees the completed run and
does nothing); a crash mid-run resumes from the last completed step recorded in the D3 records.
**Validation note:** the research tested next-day-close fills; this 15:00 desk is a different execution and is
judged on its own forward paper record (E3), never assumed equal to the backtest.

**Acceptance criteria:**
1. Given any failed step, no new trade opens and the record states the failed step and reason; exits still run.
2. Given a fill, each leg's price is the ask (buy) or bid (sell) of a valid quote at most 2 minutes old with enough
   size, and the snapshot hash is in the record.
3. Partial fill: a failed short leg after filled protection unwinds the protection and records the legging cost;
   the trade does not open.
4. Restart: killing the process after the paper fill and restarting the same day does not fill twice.
5. Missing exit quotes produce a pending exit and an alert, never a closing price taken from stale or last data.
6. Given a structure whose protective leg cannot be filled, the trade is not opened. If protection is absent or invalid
   on an open position (e.g. a protective leg's contract unquotable), the desk blocks new risk, raises a critical
   alert, marks the position `protection_unverified`, and attempts the risk-reducing exit at the next valid executable
   quotes; the position is recorded closed only when every required exit fill is recorded. The end-to-end test
   includes this case.
7. Given an open trade reaching its exit rule, it is closed at the next valid quotes and recorded.
8. The loop never calls an order function (test with a provider fake that fails on any order call).

**Test plan:** an end-to-end test over 5 simulated days with fakes (open, hold, exit, failed data day, brake day).

**Judge verifies:** reads one week of records and checks each step ran in order with its numbers.

**Depends:** C2, C3, C4, D1, D2, D3, A4 · **Size:** L · **Status:** later

---

## E2. Daily report

**User story:** As the owner, I want a daily #fno-desk message with the day's decision and each step's reason, so
that I can follow and question the desk without reading code.

**Background:** F&O output goes only to #fno-desk (`C0C89E8QCCD`) with `FNO_SLACK_*` settings; never #market-brief.

**Scope.** In: the message and its content. Out: AI commentary (F1).

**Expected design:** `fno/desk/report.py` builds plain text: data status; rules checked and which fired; trade or no
trade with reasons and numbers; open trades with P&L and days left; limits used (open trades out of 3, rupees at
risk, distance to the drawdown brake).

**Acceptance criteria:**
1. The message is posted only to #fno-desk; a test asserts the channel ID and that `SLACK_*` variables are never read.
2. A no-trade day still posts a message with the reasons.
3. Numbers in the message equal the day's decision records.

**Test plan:** message rendering tests from fixed records.

**Judge verifies:** compares one posted message with its records.

**Depends:** E1 · **Size:** S · **Status:** later

---

## E3. Paper scorecard

**User story:** As the portfolio manager, I want each strategy measured against its own evaluation plan, so that
pausing, keeping or retiring it follows rules fixed in advance, not mood.

**Background:** Design 6: paper gate at least 3 months and 20 positions (a minimum, not proof); evaluation plan fixed
before paper trading; hard-loss pauses at once, statistical reviews only on scheduled dates.

**Scope.** In: scorecard, plan checks, three ledgers, fill comparison. Out: changing a strategy (needs a new version).

**Expected design:** command `python -m fno desk scorecard` reading decision records and the playbook's evaluation
plan; shows results against the expected range, three ledgers (C1), and real fill prices against the backtest's pad
assumption.

**Acceptance criteria:**
1. Given a hard-loss pause rule hit, the strategy's status becomes `paused` at once (no new trades) and the owner is
   told.
2. **Gate to any real-money discussion:** at least 3 months of paper trading **and** at least 20 completed positions
   (closed, not open), judged only on the predetermined review dates; open positions at a review are reported
   separately at their marks and do not count as completed; an inconclusive result is never promoted.
3. Execution costs are measured from the paper record: average half-spread paid, legging costs, the share of attempted
   trades that did not fill, and pending-exit delays, against the Rs 1 pad assumed in research.
4. Given a review date, the scorecard compares results with the plan and states keep, pause or retire per the plan's
   own rules.
5. The fill comparison shows the average real half-spread against the Rs 1 pad used in research.

**Test plan:** tests with simulated paper histories.

**Judge verifies:** recomputes one scorecard number from the records.

**Depends:** E1, C1 · **Size:** M · **Status:** later

---

## E4. Retire or separate the old live desk

**User story:** As the risk manager, I want the old intraday desk (whose kill switch closes all trades) switched off
or clearly separated, so that two desks never trade the same paper account under different rules.

**Background:** The old live desk (`fno/live/runner.py`) uses chart-rule option buying with a kill switch that closes
everything; the approved design's brake blocks entries only.

**Scope.** In: one active desk per paper account; README status. Out: deleting old code (kept for reference).

**Expected design:** a setting `desk.active` in `config.yaml` (`daily_paper_desk` or `old_live_desk`); each desk
refuses to run when it is not the active one; separate journals. Because a setting cannot stop two processes started
at once, every desk must also take an **account-scoped single-writer lock** (an exclusive lock file
`journal/paper_account.lock` held with an operating-system lock and a lease time) before writing to the paper
account; a second process fails at start.

**Acceptance criteria:**
1. With `desk.active: daily_paper_desk`, the old runner exits at start with a clear message; and the reverse.
2. Two desk processes started at the same moment: exactly one gets the lock; the other exits without writing (test).
3. A lock left by a crashed process is released when its lease expires, never while its holder is alive.
4. The README states which desk is active and why.

**Test plan:** unit tests for both settings.

**Judge verifies:** tries to start the inactive desk and confirms the refusal.

**Depends:** E1 · **Size:** S · **Status:** later
