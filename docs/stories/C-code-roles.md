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
  (older than 30 days) fails closed. Judge 75 (14 Oct 2026, story A14): the file holds a structure's scanning risk,
  net option value (NOV) and exposure apart; C2 counts `max(0, scan - NOV) + min(0, NOV) + exposure`, the multiplier
  stresses the scan only, and MarginRoom also never leaves more than cash + the entry's cash flow + each trade's own
  liability, so a debit trade's premium is not counted free against an open credit trade's liability.
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

**Where C4 runs, and what E3 reads (judge 83 ruling, 14 Oct 2026):**
- C4 runs once, inside D3's decision run, on the A4 snapshot the common pack names (the mids D2 priced with). Its
  verdict is stored in the decision record's `validity.c4`.
- E3's `ValidityGate` reads the committed decision record's completed C4 pass. It never re-runs C4 on the 15:15
  execution capture: those mids differ, so every leg's "price equals the mid" check would fail.

**What C4 recomputes itself (judge 83):**
- the lot size and the monthly expiry, from NSE's own daily F&O file of the previous session;
- every owner limit, from raw inputs:
  - the drawdown brake, from the book's committed ledger;
  - stress and exposure, by its own Black-76 on the snapshot's mids;
  - margin room, from A14's three-part margins file and the account.

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

**Depends:** C2, D3 (D4 and D5 for the Book-2 envelope check and the Book-3 mode) · **Size:** M · **Status:** judge 83 FAIL (3 must-fixes) fixed on `story/c4-hard-validity`, re-judge pending (claims: reviews/claude/response_83_c4-hard-validity.md, addendum 1); criteria 1-5 built (playbook mode for Book 1 in full); criterion 6 waits for D5 and criterion 7 for D4 (both books fail closed until then)

---

## C5. Risk buckets and the Rs 20 lakh paper account

**Repository:** trading

**Description:** As the risk manager, I want every proposed trade checked against the caps of the owner's Rs 20 lakh
paper account (one bucket of correlated positions, all open positions, the new risk of one session, and the drawdown
brake), and the book's daily stress line computed, so that many strategies can run in parallel without one crash taking
the account.

**Context and why:** Design v2 section 6 (`docs/design_v2/06_risk_and_alerts.md` 6.1, 6.1a, 6.2) and the owner's
decisions (`docs/DESK_DECISIONS.md`): paper account Rs 20 lakh with Rs 10,000 maximum loss per trade (14 Oct 2026);
risk buckets and caps accepted on 15 Oct 2026: Rs 30,000 a bucket; open maximum losses at most Rs 1.5 lakh (a cap on
new entries, not a stop); new maximum loss at most Rs 50,000 a session; drawdown brake when closed equity is Rs 1.2 lakh
below its high, lifted only by the owner's written restart. C2 was built for a Rs 5 lakh account with at most 3 open
trades and a Rs 30,000 brake. With Rs 20 lakh, 15-20 protected NIFTY structures could be funded at once and would all
lose in the same crash, so the limits must apply to correlated groups (6.2). Design 6.1a: an unmapped bucket means no
new entry.

**Scope.** In:
- the paper account size as a setting (`risk.paper_account_rs`), used by E1 to open every new book and shadow account;
  a book opened with any other amount trades nothing until the owner decides how it is reopened;
- the bucket, open-risk and new-risk-per-day caps, one `RiskRule` class each inside C2, on B2's maximum loss;
- bucket assignment as 6.2 defines it, failing closed on anything 6.2 does not map;
- the drawdown brake at Rs 1.2 lakh (C2's rule and restart record, new amount);
- the daily stress line of 6.2 as a computed record for the card (T1 shows it);
- every setting in `config.yaml` `risk` through `fno/config.py`'s allowed key, checked at start-up.

Out: reopening the three books committed on 13 Oct at Rs 5 lakh (owner's choice); new values for C2's Rs 5 lakh-era
limits the owner has not rescaled (`max_open_trades` 3, `max_stress_loss_rs` 30,000, exposure Rs 15,000 each); bucket
sides for directional structures (STR1, owner's mapping first); stock buckets and the "stock results this week" group
(needs the events calendar, A6/A12, and stock options, A18); C4's independent recomputation of the new caps; showing
the stress line on the card (T1); S1's protocol text (`catastrophic_loss_book`, a draft the owner decides).

**Design:**
- `fno/risk/cap_settings.py`: `CapSettings` from `risk.paper_account_rs`, `risk.caps` (`bucket_cap_rs`,
  `open_risk_cap_rs`, `new_risk_per_day_rs`, `bucket_sides`) and `risk.stress_line`; no defaults; a cap larger than the
  account is an error.
- `fno/risk/buckets.py`: `BucketMap` interface, `StructureBuckets` adapter. Group: the contracts' underlying (symbol
  letters before the first digit), NIFTY or BANKNIFTY only; side: the structure code through `bucket_sides` (SF and SC
  short volatility, BF long volatility). Legs on two underlyings, an unlisted code, a stock or another index raise an
  input error (refused).
- `fno/risk/open_risk.py`: `HeldMaxLoss` (B2's maximum loss of a held position from its ledger cash flow, its worst
  terminal value at a strike, exit pads and exit charges; a net short tail is refused, a locked-in position counts 0);
  `PositionRisks` gives each open trade's and the proposal's bucket and maximum loss (the proposal by B2's model, the
  number `MaxLossPerTrade` checks).
- `fno/risk/caps.py`: `MaxLossCap` (sum of the selected positions' maximum losses plus the proposal's, at most the
  limit) with `BucketCap`, `OpenRiskCap`, `NewRiskPerDay`; `PaperAccountSize`. A cap only refuses.
- `OpenTrade.opened_on`: first fill day from the ledger (E1), the decision day for a trade chosen earlier the same
  session (D2's `book_after_entry`), kept in D3's decision codec; unknown means refused by the new-risk cap.
- `fno/risk/stress_line.py`: `DailyStressLine` reuses C2's `StressEngine` on the open positions; per scenario the loss
  from entry and from marks, next to the sum of maximum losses.
- Wiring only in `fno/risk/wiring.py` (`build_position_risks`, `build_stress_line`, `build_risk_manager`) and
  `fno/composition.py` (`paper_account_rs` for E1's writer).

**Acceptance criteria:**
1. Bucket cap: a proposal whose bucket's open maximum losses plus its own reach exactly Rs 30,000 passes; Rs 0.01 more
   is refused with the rule name `bucket_cap`, the bucket and the numbers; another bucket's positions do not count.
2. Open-risk cap: the same at Rs 1,50,000 across all buckets (`open_risk_cap`).
3. New risk per day: the same at Rs 50,000 for trades opened this session, the proposal included; trades opened on
   earlier sessions do not count; an open trade with no known first-fill day is refused (`new_risk_per_day`).
4. A cap only refuses: the decision judges the very proposal it was given, lots unchanged; no cap resizes or enlarges a
   trade.
5. Buckets as 6.2: SF and SC are NIFTY short volatility, BF NIFTY long volatility, BANKNIFTY its own group; an unlisted
   structure, a stock, another index or legs on two underlyings are refused as "unmapped bucket" (6.1a).
6. A held trade's maximum loss equals B2's maximum loss for the same entry (to Rs 0.000001); a held position that is
   not defined risk is refused, never measured.
7. Paper account: a new book or shadow account opens with Rs 20,00,000; a book opened with any other amount (the
   committed Rs 5 lakh books included) is refused with the rule name `paper_account`.
8. Drawdown brake at Rs 1,20,000: Rs 0.01 less passes, at and beyond refuses; only a signed `restart_brake` row in the
   book's `owner_overrides.csv` lifts it; an unsigned row makes the book unreadable (nothing trades).
9. Daily stress line: the five 6.2 scenarios, loss from entry and from marks, below the sum of maximum losses; zero for
   an empty book.
10. Every C5 number comes from `config.yaml` `risk`; a missing or malformed one is an error at start-up; the repository
    holds exactly the owner's numbers.
11. No Rs 5 lakh account size or Rs 30,000 brake is left in `fno/`; E1's writer has no default cash; the Rs 5 lakh-era
    limits not rescaled are marked "NOT rescaled" next to their keys in `config.yaml`.

**Test plan:** `tests/risk/test_caps.py` (criteria 1-4, 7), `tests/risk/test_buckets.py` (5-6),
`tests/risk/test_c5_account.py` (7-11), and C2, C4, D2, E1 and E4 tests updated to the new account and brake.

**Judge verifies:** re-runs each cap at its number and one paisa over; plants an unmapped structure and a stock leg;
checks a held trade's maximum loss against B2's by hand for one structure; plants an unsigned restart row; greps for
any Rs 5 lakh or Rs 30,000-brake value still in use.

**Depends:** C2, A14, B2, E1, D2, D3, the owner's numbers (14-15 Oct 2026) · **Size:** M · **Status:** built on
`story/c5-risk-buckets`, judge pending (claims: reviews/claude/response_105_c5-risk-buckets.md)
