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
C3 data checks, D2 evaluation, C2 risk, C4 validity, paper fill, open-trade review, D3 records, E2 report. Paper fill
price = the fresh quote's ask for bought legs and bid for sold legs (no pad needed once real quotes exist; the pad
assumption is compared with these fills in E3). Legging order: buy protective legs first, then sell; on exit, buy
back sold legs first, then sell protective legs.

**Acceptance criteria:**
1. Given any failed step, no new trade opens and the record states the failed step and reason; exits still run.
2. Given a fill, the prices used are the ask and bid from a snapshot captured within 15 minutes, and the snapshot hash
   is in the record.
3. Given a structure whose protective leg cannot be filled, the trade is not opened (and if a protective leg goes
   missing on an open trade, the trade is closed).
4. Given an open trade reaching its exit rule, it is closed at the next valid quotes and recorded.
5. The loop never calls an order function (test with a provider fake that fails on any order call).

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
2. Given a review date, the scorecard compares results with the plan and states keep, pause or retire per the plan's
   own rules.
3. The fill comparison shows the average real half-spread against the Rs 1 pad used in research.

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
refuses to run when it is not the active one; separate journals.

**Acceptance criteria:**
1. With `desk.active: daily_paper_desk`, the old runner exits at start with a clear message; and the reverse.
2. The README states which desk is active and why.

**Test plan:** unit tests for both settings.

**Judge verifies:** tries to start the inactive desk and confirms the refusal.

**Depends:** E1 · **Size:** S · **Status:** later
