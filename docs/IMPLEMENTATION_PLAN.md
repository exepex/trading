# Implementation plan: desk design v2.1 as stories

Status: **draft for ChatGPT review** (12 Oct 2026). Source: `docs/DESK_DESIGN.md` v2.1 (owner-approved framework).
The owner started development on 12 Oct 2026; the AI layer (epic F) stays on hold until the owner says otherwise.

**Story format:** heading (ID and name), description (who it serves, what it is, why it is needed), acceptance
criteria (testable checks), then dependencies, size and status. Sizes: S = under a day, M = 1-3 days, L = more.

**Definition of done (every story, in addition to its own criteria):** tests and `ruff` pass; no file or class over
350 lines; new behaviour behind an interface, concrete classes wired only in `fno/live/services.py` or
`fno/storage/wiring.py`; fixed strings in `fno/constants.py`; docs updated; any research trial registered in
`research/LEDGER.md` before its result is read; the other AI reviews the result in the repository.

## Milestones
| Milestone | Stories | Outcome |
|---|---|---|
| M1 Data and first experiment | A1-A6, B1-B5, C1 | Experiment 1 run on 2024-26 (discovery) and 2019-23 (challenge) with the frozen protocol |
| M2 Risk, playbook, validity | C2-C4, D1-D3 | A strategy that passed can be written as a playbook version and checked by code |
| M3 Code-only paper desk | E1-E4 | Daily 3 pm paper decisions on the first approved strategy, no AI |
| M4 AI layer (on hold) | F1-F5 | Only after the owner starts it; each role kept only if it adds net value |

Started early because only time builds it: **A4** (record real 3 pm bid/ask quotes every trading day).

---

## Epic A: data foundation

### A1. Raw NSE archive complete and checked
**Description:** As the data engineer, I want every raw NSE file the research needs (F&O in both formats, daily index
closes with India VIX) stored unchanged in the project's Drive folder, with a check that lists what is missing or
damaged, so that every later result rests on complete, verified inputs.

**Acceptance criteria:**
- The laptop tool downloads current-format F&O (1 Jan 2024 onwards), old-format F&O (1 Jan 2019 to 5 Jul 2024) and
  index closes (1 Jan 2019 onwards), asking only for a folder, resuming after a stop, never overwriting a file.
- `python -m fno data-coverage` lists, per dataset, the trading days with no file and every file that fails its zip
  check; it reads Drive without writing to it.
- Run on the owner's upload, it reports zero missing trading days and zero damaged files (or names each exception).

**Depends:** - · **Size:** S · **Status:** doing (tool done; owner downloading; coverage command next)

### A2. One reader for both F&O formats
**Description:** As the quant researcher, I want old-format and current-format NSE F&O files read into the same
columns, so that 2019-2026 research uses one format without converting or altering the originals.

**Acceptance criteria:**
- Both formats produce records with the current (UDiFF) column names; fields the old format lacks stay empty.
- Index options from old files get the underlying price from NSE's index close for that day.
- On every day both formats exist, contracts and all shared fields are identical.
- Damaged or unknown files are refused whole.

**Depends:** - · **Size:** M · **Status:** done (128 of 128 overlap days identical; `research/2026-10-12-legacy-format`)

### A3. NIFTY option-chain panel
**Description:** As the quant researcher, I want one table of every NIFTY option on every trading day (all strikes and
expiries, with the underlying and India VIX), built from the raw files, so that experiments can price any structure,
including far strikes the old extract lacked.

**Acceptance criteria:**
- Built from Drive first (NSE only for missing files), for 2019 onwards, through the A2 reader.
- One row per day, expiry, strike and type, with close, settlement, volume, open interest, underlying, and the day's
  India VIX; every value marked as known at that day's close.
- Rebuilding from the same raw files gives byte-identical output; row counts per day match the raw files.
- The derived file lives with the research, never in `raw/`.

**Depends:** A1, A2 · **Size:** M · **Status:** next

### A4. Daily 3 pm quote recorder
**Description:** As the execution specialist, I want real bid, ask and last prices of NIFTY monthly options near the
money recorded at about 3 pm every trading day, so that the Rs 1 fill-cost assumption can be replaced by measured
spreads and the 3 pm desk can be tested on what it would really have seen.

**Acceptance criteria:**
- On each trading day it records, for the nearest two monthly expiries and strikes within 5% of spot: bid, ask, last
  price, quote time and source, through the existing `Provider` interface.
- Stored as dated raw files (never changed afterwards); a missed day is logged, not filled in later.
- Never places or modifies orders; credentials only from the environment.
- After 20 trading days, a report shows the median half-spread by distance from the money.

**Depends:** - · **Size:** M · **Status:** next (start early)

### A5. Monthly-expiry identity in the package
**Description:** As the data engineer, I want the rule that identifies NIFTY monthly expiries (listed that day and
listed more than 50 days ahead) in the `fno` package with its tests, so that research and the desk use one tested
definition.

**Acceptance criteria:**
- `monthly_as_of` lives in `fno`, research scripts import it, and its existing tests move with it.
- Results of desk meeting 1 and the capacity screen are unchanged after the move.

**Depends:** - · **Size:** S · **Status:** next

### A6. Events calendar
**Description:** As the macro economist, I want a dated list of RBI policy announcements, Union Budgets and
general-election results for 2019-2026, each with its official source, so that the "event inside the holding window"
condition can be tested without hindsight.

**Acceptance criteria:**
- `events.csv` with date, type, description and source link for every event; dates checked against official RBI and
  government announcements.
- Committed before experiment 1 reads any 2019-2023 result.

**Depends:** - · **Size:** S · **Status:** next

---

## Epic B: research and discovery engine

### B1. Feature library
**Description:** As the volatility trader and the quant modeller, I want each entry condition (implied minus past
realised volatility, India VIX level, event in window, and later ones) as a small named feature with a declared
availability time, so that the engine can combine them and can never use information from after the decision.

**Acceptance criteria:**
- Each feature is a class behind one interface, with name, inputs and availability time.
- A test feeds data that changes after the decision time and proves no feature's value changes.
- F1, F2 and F3 from the experiment 1 protocol reproduce hand-computed values on three sample days.

**Depends:** A3, A6 · **Size:** M · **Status:** later

### B2. Cycle simulator
**Description:** As the F&O trader and the tax and cost accountant, I want one simulator that takes a structure
through a monthly cycle exactly as the protocol says (entry, exit, fills, costs, cap), so that every policy is judged
on identical, realistic terms.

**Acceptance criteria:**
- Decision day, next-day close entry, exit at the last close with 21 or more days left, Rs 1 worse per leg, current
  charges and lot.
- Settlement price used for untraded legs and flagged; "unfillable" and "bad prices" rules applied as written.
- Width rule: the widest allowed protection whose maximum loss including costs is at most Rs 10,000; otherwise
  "no trade (cap)".
- Three hand-worked cycles (one each for short fly, short condor, long fly) match to the rupee.

**Depends:** A3 · **Size:** M · **Status:** later

### B3. Policy runner and verdict
**Description:** As the statistician, I want registered policies and controls run over a period with the protocol's
metrics and pass/fail computed by code, so that the verdict is reproducible and nobody judges by eye.

**Acceptance criteria:**
- Runs policies and both controls (coin toss with a fixed seed, opposite rule); refuses any policy not in the ledger.
- Reports total and mean net, win rate, worst cycle, longest losing run, yearly net after 31.2% tax, and counts of
  no-trade, unfillable and bad-price cycles.
- Computes the cycle bootstrap bound and each pass/fail criterion; same inputs give an identical results file.

**Depends:** B1, B2, B4 · **Size:** M · **Status:** later

### B4. Ledger guard
**Description:** As the red team, I want the engine to refuse to run a trial that is not registered in the ledger
first, so that the number of ideas tried is always counted and lucky winners cannot hide.

**Acceptance criteria:**
- A run for an unregistered trial stops with a clear message; a registered one records its run date.
- The ledger shows the trial count per experiment.

**Depends:** - · **Size:** S · **Status:** later

### B5. Experiment 1
**Description:** As the head of desk, I want experiment 1 (protected sell, protected buy or no trade, by entry-known
conditions) run under its frozen protocol, so that the desk learns, with a fair test, whether any NIFTY monthly rule
deserves paper trading.

**Acceptance criteria:**
- Protocol reviewed by ChatGPT, frozen, and its commit recorded before any 2019-2023 result is read.
- Discovery results (2024-26) published; challenge results (2019-23) published once A1 is complete.
- Each policy gets pass or fail per the protocol; ChatGPT reviews the results; decisions recorded.

**Depends:** B1-B4, A1 · **Size:** M · **Status:** doing (protocol in review)

### B6. Candidate scan
**Description:** As the quant researcher, I want a systematic scan of feature, structure and action combinations on
discovery data, each counted as a trial, so that the desk uses its computing power to find candidates a person
would miss, without fooling itself.

**Acceptance criteria:**
- Every combination is registered automatically and counted; the significance bar rises with the count as fixed in
  the scan's protocol.
- Survivors are listed with net P&L, worst case and stability by year; nothing is promoted without a challenge test.

**Depends:** B3 · **Size:** L · **Status:** later

---

## Epic C: code roles

### C1. Cost and tax accountant
**Description:** As the owner, I want every result in three ledgers (trade P&L after charges and pads, account result
after the desk's running costs, and yearly tax), so that "profitable" always means money actually kept.

**Acceptance criteria:**
- Trade ledger: charges and pads per leg and order. Account ledger: actual AI and data bills entered as amounts.
- Tax: 31.2% of each financial year's net F&O profit, losses offset within the year, shown separately.
- A test year with a known answer matches to the rupee.

**Depends:** - · **Size:** S · **Status:** later

### C2. Risk manager
**Description:** As the risk manager, I want every proposed trade checked against the owner's limits and against
stress tests of the whole account, so that no trade or combination of trades can break the account.

**Acceptance criteria:**
- Blocks a trade whose maximum loss including costs exceeds Rs 10,000, or a fourth open trade.
- Drawdown brake: at Rs 30,000 below the closed-equity high, blocks new entries only; open trades keep their own
  exits; restart only by the owner, re-armed Rs 30,000 below restart-day equity; history kept.
- Stress test with full repricing of all open trades plus the new one: NIFTY +/-5% and +/-8%, IV doubled and halved,
  joint shocks, passage of time, replays of 23 Mar 2020, 4 Jun 2024 and Feb 2026; combined stress loss within
  Rs 30,000; stressed margin within available cash.
- Exposure limits are settings (not code), defaulting to the proposed values until research sets them.
- Each rule has a test that a trade just inside passes and just outside is blocked.

**Depends:** B2 · **Size:** L · **Status:** later

### C3. Data checks
**Description:** As the data engineer, I want the desk to confirm its data is present, fresh and consistent before
every decision, so that no trade is ever made on stale or broken prices.

**Acceptance criteria:**
- Missing, stale or inconsistent data means no new trade that day and an alert.
- Stale prices are marked and never used as fill prices; risk-reducing exits still run.

**Depends:** A3, A4 · **Size:** S · **Status:** later

### C4. Hard-validity checks (judge part 1)
**Description:** As the judge, I want dates, contracts, arithmetic, funding and owner limits re-checked by code that
is independent of the code that proposed the trade, so that a trade with a wrong number can never pass.

**Acceptance criteria:**
- Recomputes the trade's legs, prices, maximum loss and limits from the raw inputs; any difference blocks the trade.
- A hard-validity failure cannot be overridden by anyone, the owner included; it is logged with the reason.
- Seeded wrong trades (stale date, wrong strike, wrong arithmetic, limit breach) are all caught.

**Depends:** C2 · **Size:** M · **Status:** later

---

## Epic D: playbook and decisions

### D1. Playbook format
**Description:** As the portfolio manager, I want each approved strategy written as a versioned file with its payer,
rules, limits, evaluation plan and evidence, so that the desk trades only what was tested and any change is visible.

**Acceptance criteria:**
- YAML with every field of design section 5; the loader rejects a missing or invalid field.
- Changing any parameter requires a new version file; the old one stays.
- A strategy cannot reach "paper" status without links to its test, red-team note, judge verdict and owner approval.

**Depends:** B5 · **Size:** M · **Status:** later

### D2. Rule evaluation and allocation
**Description:** As the portfolio manager, I want the day's approved rules evaluated on measured inputs and a fixed
allocation rule to choose when several fire, so that daily decisions are consistent and comparable with no trade.

**Acceptance criteria:**
- A rule fires only if all its conditions hold on that day's data.
- When several fire, the fixed rule ranks by expected net money per rupee of risk after funding, exposure and slot
  limits; no trade is always one option.
- A strategy without a paper record holds at most 1 of the 3 slots.

**Depends:** D1, C2 · **Size:** M · **Status:** later

### D3. Decision record
**Description:** As the head of desk, I want one stored record per opportunity (what was seen, expected, decided and
why), so that every decision can be reproduced, reviewed and learned from.

**Acceptance criteria:**
- Holds observations with availability times, the forecast (the rule's tested P&L distribution), legs, prices, size,
  expected net value, account room, the no-trade alternative and the reasons.
- Re-running the record's inputs reproduces the same decision.

**Depends:** D2 · **Size:** M · **Status:** later

---

## Epic E: code-only daily paper desk

### E1. Daily 3 pm loop
**Description:** As the owner, I want the desk to run every trading day at about 3 pm (check data, evaluate rules,
check risk and validity, paper-fill, review open trades), so that the first approved strategy is paper-traded exactly
as tested.

**Acceptance criteria:**
- Runs the steps in order; any failed check means no new trade, with the reason recorded.
- Paper fills only after a fresh quote check; protection bought first and sold last; a missing protective leg is
  closed.
- Open trades follow their own exit rules; wired in `services.py`; never places real orders.

**Depends:** C2-C4, D1-D3, A4 · **Size:** L · **Status:** later

### E2. Daily report
**Description:** As the owner, I want a daily #fno-desk message with the day's decision and each step's reason, so
that I can follow and question the desk without reading code.

**Acceptance criteria:**
- Posted to #fno-desk only (never #market-brief); includes data status, rules checked, trade or no trade with
  reasons, open trades and limits used.

**Depends:** E1 · **Size:** S · **Status:** later

### E3. Paper scorecard
**Description:** As the portfolio manager, I want each strategy measured against its own evaluation plan, so that
pausing, keeping or retiring it follows rules fixed in advance, not mood.

**Acceptance criteria:**
- Shows results against the expected range, by the plan's unit and review dates, in all three ledgers.
- Hard-loss pauses act at once; statistical reviews only on the scheduled dates.

**Depends:** E1, C1 · **Size:** M · **Status:** later

### E4. Retire or separate the old live desk
**Description:** As the risk manager, I want the old intraday desk (whose kill switch closes all trades) switched off
or clearly separated, so that two desks never trade the same paper account under different rules.

**Acceptance criteria:**
- Only one desk can write to the paper account; the old desk's status is stated in the README.

**Depends:** E1 · **Size:** S · **Status:** later

---

## Epic F: AI layer (on hold until the owner starts it)

### F1. Role agents
**Description:** As the head of desk, I want one AI agent per judgement role producing finding cards independently,
so that each field's expertise reaches the decision without groupthink.

**Acceptance criteria:**
- Fixed finding-card format (observations with sources, interpretation, implication, confidence, counter-evidence,
  missing data); "not applicable" allowed; no agent sees another's card before submitting.

**Depends:** E1 · **Size:** L · **Status:** on hold

### F2. Red team
**Description:** As the owner, I want an agent on a different model from the author attacking every thesis, so that
luck, flattering periods and disaster cases are found before money is at risk.

**Acceptance criteria:**
- Runs on a different model from the author; its objections are recorded and shown to the judge.

**Depends:** F1 · **Size:** M · **Status:** on hold

### F3. AI judge (parts 2 and 3)
**Description:** As the owner, I want research sufficiency and interpretation checked by a model different from the
author, audited monthly, so that the judge itself stays honest.

**Acceptance criteria:**
- Verdicts pass or fail with reasons; monthly audit on a stratified sample plus seeded known-answer cases, counting
  false approvals and false rejections.

**Depends:** C4, F1 · **Size:** M · **Status:** on hold

### F4. Role scorecards
**Description:** As the portfolio manager, I want each optional AI role scored by the net money it adds after its own
cost, so that roles that do not earn their keep are removed.

**Acceptance criteria:**
- Paired shadow decisions with and without the role on the same opportunities; abstentions counted; mandatory
  control roles scored on correctness only.

**Depends:** F1, E3 · **Size:** M · **Status:** on hold

### F5. Operating-cost tracking
**Description:** As the tax and cost accountant, I want actual AI and data bills fed into the account ledger, so that
the desk's own running cost is counted against its profit.

**Acceptance criteria:**
- Monthly bills entered as actual amounts; the account ledger shows result after operating costs.

**Depends:** C1 · **Size:** S · **Status:** on hold

---

## Questions for review
1. Is anything in the approved design missing from these stories, or any story not justified by it?
2. Is every acceptance criterion testable as written? Which would you tighten?
3. Is the order right: data and experiment 1 first, then risk and playbook, then the paper desk, AI last?
4. A4 (recording real 3 pm quotes) is started early because only time builds that history: agree?
