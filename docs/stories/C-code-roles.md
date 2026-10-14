# Epic C: code roles (deterministic)

Roles: tax and cost accountant, risk manager, data engineer, judge (hard-validity part). Goal: the numeric roles are
tested code that gives the same answer every time and cannot be argued with (design sections 3.4, 7, 8, 8.1).
Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## C1. Cost and tax accountant: three ledgers

**Repository:** trading

**Description:** As the owner, I want every result shown in three ledgers (trade P&L after charges and pads, account
result after the desk's running costs, and yearly tax), so that "profitable" always means money actually kept.

**Context and why:** Owner decisions: tax modelled at 31.2% (30% slab plus 4% cess) on each financial year's net F&O
profit. Design section 8: AI and data bills count against profit; code roles add no cash cost today.

**Scope.** In: the three ledgers for research results and paper trades. Out: tax advice, filing, turnover audit rules.

**Expected design:** `fno/accounting/ledgers.py` with `TradeLedger` (per trade: gross, charges by component from
`fno.costs.order_charges_breakdown`, pads, net), `AccountLedger` (trade net minus operating costs by month, from
`accounting/operating_costs.csv` with `month, item, category, amount_rs, source`), `TaxModel`.
**One tax scenario everywhere (research and paper):** an *assumed* scenario, not a verified tax liability: Indian
financial year (April-March); base = trade net of the year (F&O treated as business income) minus operating costs in
the categories marked deductible in `accounting/deductible_categories.csv` (default: AI and data subscriptions used
for the trading); tax = 31.2% of max(0, base); losses offset within the year; no carry-forward modelled (stated).
Research results report the scenario after the pre-tax pass/fail tests; tax never enters a pass/fail criterion.

**Acceptance criteria:**
1. Given a year with trades +10,000, -4,000 and +6,000 net and deductible operating costs Rs 3,000, then trade net =
   12,000, account result = 9,000, tax base = 9,000 and modelled tax = 2,808 (31.2% of 9,000), each shown separately
   and labelled "assumed scenario".
2. The three ledgers reconcile: account result = trade net - operating costs; tax base = trade net - deductible
   costs; a test fails if they do not.
3. Given a losing year, then modelled tax is 0 and the loss is shown, not carried forward (with a note).
4. Charges per trade equal `fno.costs` for every leg and order; pads are shown separately from charges.
5. Financial years run April to March (a trade closed on 31 Mar 2025 counts in FY 2024-25).

**Test plan:** unit tests with the known-answer year above and edge dates.

**Judge verifies:** recomputes one month's three ledgers by hand from the trade list and the costs file.

**Known limits (13 Oct 2026, judge 6):** one charges table (`config.yaml` `charges`) is applied to every trade date, so
historical research trades are charged today's rates (STT 0.15% of sell-side option premium from 1 Apr 2026, Budget
2026; before that 0.1% from Oct 2024 and lower earlier). That is conservative while today's rates are higher and is
the right test for trading from now on ("would it work at today's costs"); every research report states it. The STT
rate is confirmed by broker and press summaries of the Budget (ICICI Direct, Groww, Outlook Money); the Finance Act
text itself is still to be cited. E7 (14 Oct 2026) adds `stt_exercise_pct` (0.15% of an exercised option's intrinsic value, raised
from 0.125% by the same Budget) and `Order.charges`, one charges dispatch for traded orders and expiry settlements.

**Depends:** - · **Size:** S · **Status:** done (judge passed in round 2, `reviews/judge/judge_10_c1_three_ledgers_rejudge.md`)

---

## C2. Risk manager

**Repository:** trading

**Description:** As the risk manager, I want every proposed trade checked against the owner's limits and against stress
tests of the whole account, so that no trade or combination of trades can break the account.

**Context and why:** Design 12.4: the same owner limits apply to each of the three books, each on its own Rs 5 lakh
paper account (E1). Owner decisions: Rs 5 lakh paper account; Rs 10,000 maximum loss per trade including charges; at most
3 open trades; drawdown brake at Rs 30,000 below the closed-equity high (blocks new entries only; open trades keep
their own exits; owner restarts). Design 8.1: whole-account stress tests with full repricing; exposure limits proposed
at Rs 15,000 for a 2% NIFTY move and for a 5-point IV rise, to be set from research.

**Scope.** In: per-trade, count, drawdown, stress and exposure checks; margin tracked separately. Out: broker margin
calculation itself (an input: measured from NSE SPAN files or the broker's calculator, entered per structure).

**Expected design:**
- Package `fno/risk/` with `RiskRule` interface (`check(proposal, book, market) -> RiskVerdict(ok, reason, numbers)`).
- Rules (one class each): `MaxLossPerTrade` (10,000), `MaxOpenTrades` (3), `DrawdownBrake` (30,000, high-water mark on
  closed equity, re-arm at restart-day equity minus 30,000, restart only via an owner entry in
  `journal/<book>/owner_overrides.csv`), `StressLoss` (scenarios below, combined loss at most 30,000), `ExposureLimit`
  (delta and vega, values from `config.yaml` `risk.exposure`), `MarginRoom` (stressed margin at most available cash).
- Stress engine `fno/risk/stress.py`: reprices every leg of open trades plus the proposal with the project's
  implied-volatility model (B1's `ImpliedVolModel`; the app wires `Black76`: the option on its same-expiry NIFTY future,
  the rate only discounting; judge 43) at each leg's current implied volatility from that same model, under: NIFTY -8%, -5%, +5%, +8% (overnight, one day passes); IV x2 and
  x0.5; joint (NIFTY -8% with IV x2, NIFTY +5% with IV x0.5); and historical replays applying the NIFTY and VIX moves
  of 23 Mar 2020, 4 Jun 2024 and Feb 2026's worst day. Reports loss from current marked value and loss from entry.
- All limits read from a new `risk` block in `config.yaml` (this story adds `risk` to `ALLOWED_APP_KEYS` in
  `fno/config.py`, with tests), never hard-coded. The risk manager is called **per book**, with that book's account
  (E1) only; no book's positions affect another's limits.
- **Definitions:** closed equity = Rs 5 lakh + sum of net P&L of closed trades; marked equity = closed equity + open
  trades valued at mid of valid quotes (or last valid mark, flagged stale); available cash = the lower of cash and
  marked equity, minus margin blocked, minus premium reserved for pending orders (13 Oct 2026: "marked equity minus
  margin" counted a bought option's premium as spendable a second time; the lower of the two is conservative for both
  long premium and short-option losses; E1 implements it in `fno/books/equity.py`); judge 1: if margin blocked is the broker's total margin for a short structure, which already includes the
  mark-to-market loss, the loss is counted twice, so C2 states which margin figure it uses).
- **Margin:** per structure and lot, from the broker's margin calculator or NSE's SPAN parameter files, recorded with
  source and date in `research/data/margins/margins.csv`; older than 7 days or missing means the check **fails
  closed** (no trade). **Stressed margin, one frozen method:** set in `config.yaml` `risk.stressed_margin` before any
  proposal is evaluated: `scenario_lookup` (margin per stress scenario from SPAN parameter files, when available for
  the structure) or `multiplier` (current margin x a predeclared conservative factor, with its source and date). The
  method in force is recorded in every decision record so the judge reproduces it; a missing or expired multiplier
  (older than 30 days) fails closed.
- **Two different Rs 30,000 limits:** the drawdown brake uses closed equity against its high-water mark; the stress
  limit uses the combined stress loss of open trades plus the proposal from current marks. They are separate rules
  with separate tests.
- **Stress repricing:** each leg revalued with Black-76 on its same-expiry future (moved by the scenario's NIFTY move)
  at its current implied volatility scaled by the scenario, one calendar day of time decay (13 Oct 2026, judge 43:
  Black-Scholes on spot with Black-76 volatilities misprices an ATM leg by about Rs 1,000 a lot with no move); losses summed across all legs and trades (no netting
  assumptions beyond the legs themselves).
- **Decision record (14 Oct 2026, judge 68):** a `RiskDecision` also carries the proposal it judged and its entry cash at the
  modelled prices (`entry_cash_rs`, the same `TradeCosts` as the maximum-loss rule); the paper desk's entry limit (E4)
  reads it from there only.
- **Owner restart:** a row in `journal/<book>/owner_overrides.csv` (`date, action = restart_brake, reason, entered_by`)
  committed to the repository; the brake re-arms at that day's closing closed equity minus Rs 30,000.

**Acceptance criteria:**
1. Given a proposal with maximum loss Rs 9,999 including costs, it passes `MaxLossPerTrade`; Rs 10,001 is blocked
   with the reason and numbers.
2. Given 3 open trades, a fourth is blocked.
3. Given closed equity 30,000 below its high, any new entry is blocked; open trades are not closed; after an owner
   restart entry, entries are allowed and the brake re-arms 30,000 below that day's equity.
4. Given an open short fly and a proposed short condor, the stress engine reports per-scenario losses equal to a
   hand computation (test with fixed prices) and blocks the proposal when the combined worst scenario exceeds
   Rs 30,000.
5. Given exposure settings, a proposal pushing the account's 2%-move loss above the setting is blocked.
6. Every rule has a just-inside and a just-outside test.
7. Given two books, a brake hit in one book blocks only that book; a stress test of one book never includes another
   book's positions.

**Test plan:** unit tests per rule; stress engine tests against hand calculations; scenario replay inputs checked
against the panel's NIFTY and VIX closes for those dates.

**Judge verifies:** feeds three crafted proposals (inside, outside, borderline) and checks verdicts and numbers.

**Depends:** B2 · **Size:** L · **Status:** done: judge 43 PASS (13 Oct 2026)

---

## C3. Data checks before every decision

**Repository:** trading

**Description:** As the data engineer, I want the desk to confirm its data is present, fresh and consistent before
every decision, so that no trade is ever made on stale or broken prices.

**Context and why:** Design section 9: missing or stale data means no new trades; stale prices are never fill prices;
risk-reducing exits still run.

**Scope.** In: checks on the 3 pm quote snapshot and the latest daily files. Out: fixing data (A stories).

**Expected design:** `fno/checks/data_checks.py` with `DataCheck` interface; checks run on the common market pack
(E2) and on the execution snapshot (E3): the snapshot exists, is the day's snapshot taken inside its scheduled window
(capture times from its sidecar), and its hash matches the pack; spot present and within 2% of the previous close
unless a shock is flagged; every needed leg has a valid quote by the **A4 rule** (bid > 0, ask > 0, bid <= ask, both
sizes > 0, a trade in the contract today; quote age unknown, never claimed); the previous session's NSE file is
present (session per the A1 calendar).

**Acceptance criteria:**
1. Given a snapshot taken outside its scheduled window, or whose hash differs from the pack, the decision is "no new
   trade: stale or unverified data" with an alert.
2. **Per leg:** a leg is usable only if its own quote is valid by the A4 rule (bid > 0, ask > 0, bid <= ask, both
   sizes > 0, a trade in the contract today); no age is claimed. A trade needing an unusable leg is not opened.
   (Corrects the earlier "quote age at most 60 seconds" rule, which no provider can prove: Groww gives no quote
   timestamp, A4.)
3. Given failed data checks and an open trade due to exit, the exit is recorded as **pending exit** with an alert and
   executed at the next valid quotes; a fill is never invented from stale or last prices.

**Test plan:** unit tests per check with fake snapshots.

**Judge verifies:** runs the checks on a deliberately stale snapshot and confirms the refusal.

**Depends:** A3, A4, A7, E2 · **Size:** S · **Status:** built on `story/c3-data-checks`, judge pending (claims: reviews/claude/response_82_c3-data-checks.md)

---

## C4. Hard-validity checks (judge part 1)

**Repository:** trading

**Description:** As the judge, I want dates, contracts, arithmetic, funding and owner limits re-checked by code that is
independent of the code that proposed the trade, so that a trade with a wrong number can never pass.

**Context and why:** Design section 7: hard validity is code, not a model's opinion; nobody, the owner included, can
override a hard-validity failure. Design 12.4: **two modes**. Books 1 and 2 are checked against their playbook
version; Book 3 has no tested playbook and is checked only against hard facts and owner constraints (contracts exist,
quotes and cutoff, payoff and maximum loss, charges, margin and stress, account limits, allowed market and horizon, no
prohibited structure); the quality of Book 3's thesis is judge and red-team evidence (F3, F4), not hard validity.

**Scope.** In: independent recomputation from raw inputs. Out: judgement on research sufficiency or interpretation
(F3).

**Expected design:** `fno/checks/validity.py` re-reads the decision record's raw inputs (verifying each snapshot's
SHA-256 and that its capture time is before the decision cutoff) and recomputes **with an independent
implementation**: maximum loss from the payoff at expiry evaluated on a strike grid (not the width-minus-credit
formula the proposer uses), charges from the charge table directly (not via `fno.costs`), checked against committed
reference vectors (hand-computed trades). Checks: contract exists and expiry is the intended monthly one; dates are
today's; leg prices equal the snapshot; maximum loss and charges; all C2 limits.
`mode` = `playbook` (books 1, 2: also the strategy's version hash, structure code and that the action is permitted
by the version and, for Book 2, by its authority envelope D4) or `constitution` (Book 3: the D5 constitution's hard
constraints, the `strategy_id` registered before its first trade, defined-risk only, holding at most 3 weeks, NIFTY
options only).
Output: pass or fail with each check's numbers; failures written to `journal/<book>/validity_failures.csv`.

**Acceptance criteria:**
1. Seeded wrong proposals are all blocked: stale date, wrong expiry, strike not listed, price not matching the
   snapshot, maximum loss miscomputed by Rs 1 or more, a limit breach.
2. A correct proposal passes with every check's numbers recorded.
3. There is no code path that turns a hard-validity failure into a pass (test: the override function rejects it).
4. Tampered evidence (a snapshot whose hash differs from the record) and absent evidence (a missing snapshot) both
   fail.
5. The reference vectors (at least 10 hand-computed trades across all structures) match the independent
   implementation to Rs 0.01.
6. Constitution mode: a naked short option, a holding period over 3 weeks, a non-NIFTY contract and a trade whose
   `strategy_id` was registered after the decision are each blocked; a defined-risk Book-3 trade inside the limits
   passes even if no playbook exists.
7. Playbook mode for Book 2: an action marked `forbidden` or `shadow-only` in the envelope is blocked.

**Test plan:** a seeded set of 10 wrong proposals and 3 correct ones.

**Judge verifies:** adds a new wrong proposal of its own and confirms it is caught.

**Depends:** C2, D3 (D4 and D5 for the Book-2 envelope check and the Book-3 mode) · **Size:** M · **Status:** built on `story/c4-hard-validity`, judge pending (claims: reviews/claude/response_83_c4-hard-validity.md); criteria 1-5 built (playbook mode for Book 1 in full); criterion 6 waits for D5 and criterion 7 for D4 (both books fail closed until then)
