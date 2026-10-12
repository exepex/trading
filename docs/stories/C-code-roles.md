# Epic C: code roles (deterministic)

Roles: tax and cost accountant, risk manager, data engineer, judge (hard-validity part). Goal: the numeric roles are
tested code that gives the same answer every time and cannot be argued with (design sections 3.4, 7, 8, 8.1).
Template and shared definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## C1. Cost and tax accountant: three ledgers

**User story:** As the owner, I want every result shown in three ledgers (trade P&L after charges and pads, account
result after the desk's running costs, and yearly tax), so that "profitable" always means money actually kept.

**Background:** Owner decisions: tax modelled at 31.2% (30% slab plus 4% cess) on each financial year's net F&O
profit. Design section 8: AI and data bills count against profit; code roles add no cash cost today.

**Scope.** In: the three ledgers for research results and paper trades. Out: tax advice, filing, turnover audit rules.

**Expected design:** `fno/accounting/ledgers.py` with `TradeLedger` (per trade: gross, charges by component from
`fno.costs.order_charges_breakdown`, pads, net), `AccountLedger` (trade net minus operating costs by month, from
`accounting/operating_costs.csv` with `month, item, amount_rs, source`), `TaxModel` (financial year April-March: tax =
31.2% of max(0, year net), losses offset within the year, no carry-forward in the model, stated as a simplification).

**Acceptance criteria:**
1. Given a year with trades +10,000, -4,000 and +6,000 net and operating costs Rs 3,000, then trade net = 12,000,
   account result = 9,000 and modelled tax = 2,808 (31.2% of 9,000), each shown separately.
2. Given a losing year, then modelled tax is 0 and the loss is shown, not carried forward (with a note).
3. Charges per trade equal `fno.costs` for every leg and order; pads are shown separately from charges.
4. Financial years run April to March (a trade closed on 31 Mar 2025 counts in FY 2024-25).

**Test plan:** unit tests with the known-answer year above and edge dates.

**Judge verifies:** recomputes one month's three ledgers by hand from the trade list and the costs file.

**Depends:** - · **Size:** S · **Status:** later

---

## C2. Risk manager

**User story:** As the risk manager, I want every proposed trade checked against the owner's limits and against stress
tests of the whole account, so that no trade or combination of trades can break the account.

**Background:** Owner decisions: Rs 5 lakh paper account; Rs 10,000 maximum loss per trade including charges; at most
3 open trades; drawdown brake at Rs 30,000 below the closed-equity high (blocks new entries only; open trades keep
their own exits; owner restarts). Design 8.1: whole-account stress tests with full repricing; exposure limits proposed
at Rs 15,000 for a 2% NIFTY move and for a 5-point IV rise, to be set from research.

**Scope.** In: per-trade, count, drawdown, stress and exposure checks; margin tracked separately. Out: broker margin
calculation itself (an input: measured from NSE SPAN files or the broker's calculator, entered per structure).

**Expected design:**
- Package `fno/risk/` with `RiskRule` interface (`check(proposal, book, market) -> RiskVerdict(ok, reason, numbers)`).
- Rules (one class each): `MaxLossPerTrade` (10,000), `MaxOpenTrades` (3), `DrawdownBrake` (30,000, high-water mark on
  closed equity, re-arm at restart-day equity minus 30,000, restart only via an owner entry in
  `journal/owner_overrides.csv`), `StressLoss` (scenarios below, combined loss at most 30,000), `ExposureLimit`
  (delta and vega, values from `config.yaml` `risk.exposure`), `MarginRoom` (stressed margin at most available cash).
- Stress engine `fno/risk/stress.py`: reprices every leg of open trades plus the proposal with `fno.analytics.bs_price`
  at each leg's current implied volatility, under: NIFTY -8%, -5%, +5%, +8% (overnight, one day passes); IV x2 and
  x0.5; joint (NIFTY -8% with IV x2, NIFTY +5% with IV x0.5); and historical replays applying the NIFTY and VIX moves
  of 23 Mar 2020, 4 Jun 2024 and Feb 2026's worst day. Reports loss from current marked value and loss from entry.
- All limits read from `config.yaml` `profiles.paper.risk`, never hard-coded.

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

**Test plan:** unit tests per rule; stress engine tests against hand calculations; scenario replay inputs checked
against the panel's NIFTY and VIX closes for those dates.

**Judge verifies:** feeds three crafted proposals (inside, outside, borderline) and checks verdicts and numbers.

**Depends:** B2 · **Size:** L · **Status:** later

---

## C3. Data checks before every decision

**User story:** As the data engineer, I want the desk to confirm its data is present, fresh and consistent before
every decision, so that no trade is ever made on stale or broken prices.

**Background:** Design section 9: missing or stale data means no new trades; stale prices are never fill prices;
risk-reducing exits still run.

**Scope.** In: checks on the 3 pm quote snapshot and the latest daily files. Out: fixing data (A stories).

**Expected design:** `fno/checks/data_checks.py` with `DataCheck` interface; checks: snapshot exists and was captured
within the last 15 minutes; spot present and within 2% of the previous close unless a shock is flagged; every needed
leg has a two-sided quote or is marked unquotable; the previous trading day's NSE file is present.

**Acceptance criteria:**
1. Given a snapshot older than 15 minutes, the decision is "no new trade: stale data" with an alert.
2. Given a leg without a two-sided quote, that leg cannot be used for a fill; a trade needing it is not opened.
3. Given failed data checks and an open trade at its loss limit, the exit still runs at the next valid quote and is
   marked as such.

**Test plan:** unit tests per check with fake snapshots.

**Judge verifies:** runs the checks on a deliberately stale snapshot and confirms the refusal.

**Depends:** A3, A4 · **Size:** S · **Status:** later

---

## C4. Hard-validity checks (judge part 1)

**User story:** As the judge, I want dates, contracts, arithmetic, funding and owner limits re-checked by code that is
independent of the code that proposed the trade, so that a trade with a wrong number can never pass.

**Background:** Design section 7: hard validity is code, not a model's opinion; nobody, the owner included, can
override a hard-validity failure.

**Scope.** In: independent recomputation from raw inputs. Out: judgement on research sufficiency or interpretation
(F3).

**Expected design:** `fno/checks/validity.py` re-reads the decision record's inputs and recomputes, without importing
the proposer's pricing code paths beyond shared primitives (`fno.costs`, `fno.analytics`): contract exists and expiry
is the intended monthly one; dates are today's; leg prices equal the snapshot; maximum loss and charges; all C2 limits.
Output: pass or fail with each check's numbers; failures written to `journal/validity_failures.csv`.

**Acceptance criteria:**
1. Seeded wrong proposals are all blocked: stale date, wrong expiry, strike not listed, price not matching the
   snapshot, maximum loss miscomputed by Rs 1 or more, a limit breach.
2. A correct proposal passes with every check's numbers recorded.
3. There is no code path that turns a hard-validity failure into a pass (test: the override function rejects it).

**Test plan:** a seeded set of 10 wrong proposals and 3 correct ones.

**Judge verifies:** adds a new wrong proposal of its own and confirms it is caught.

**Depends:** C2, D3 · **Size:** M · **Status:** later
