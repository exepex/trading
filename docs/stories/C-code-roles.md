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

**Depends:** A3, A4, A7, E2 · **Size:** S · **Status:** done: judge 81 PASS (round 2 0cc22a2), merged e3506ec; first real capture 14 Oct (addendum 3) (claims: reviews/claude/response_82_c3-data-checks.md)

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

**Depends:** C2, D3 (D4 and D5 for the Book-2 envelope check and the Book-3 mode) · **Size:** M · **Status:** done for criteria 1-5: judge 83 PASS (round 3 bf0d4af, merged dafbebe; A4-valid quotes e01a939, merged b03c4ef) (claims: reviews/claude/response_83_c4-hard-validity.md); criteria 1-5 built (playbook mode for Book 1 in full); criterion 6 waits for D5 and criterion 7 for D4 (both books fail closed until then)

---

## C5. Risk buckets and the Rs 20 lakh paper account

**Repository:** trading

**Description:** As the risk manager, I want every trade proposed for a paper book checked against the caps of the
owner's Rs 20 lakh account (one bucket of correlated positions, all open positions, the new risk of one session, and
the drawdown brake), C4 recomputing the same caps on its own, and the book's daily stress line computed, so that many
strategies can run in parallel without one crash taking the account.

**Context and why:** Design v2 section 6 (`docs/design_v2/06_risk_and_alerts.md` 6.1, 6.1a, 6.2, 6.3) and the owner's
decisions (`docs/DESK_DECISIONS.md`):
- 14 Oct 2026: "Paper account Rs 20 lakh, Rs 10,000 maximum loss per trade" (owner: "=> YES").
- 15 Oct 2026: "Risk buckets and caps accepted": Rs 30,000 a bucket; new risk Rs 50,000 a day; open positions' maximum
  losses at most Rs 1.5 lakh (a cap on open risk, not a stop); brake when closed equity is Rs 1.2 lakh below its high,
  until the owner restarts in writing.
- 15 Oct 2026, "1 A": "Books drop the flat '3 open trades' limit; the bucket and account caps replace it ... Paper books
  only (Rs 20 lakh); the Manual paper account keeps its 13 Oct limits, including 3 open trades".
- 15 Oct 2026, "2 A": "Books drop C2's old Rs 30,000 stress and Rs 15,000 exposure limits; the new caps replace them ...
  the daily stress line stays as information on the card; the Manual account is unchanged".
- 13 Oct 2026 (Manual account, unchanged): Rs 5 lakh, Rs 10,000 a trade, 3 open trades, Rs 30,000 brake.
- 15 Oct 2026, C5's questions: "1 B": "A position that is directional and short (or long) volatility counts in both
  of its risk buckets" (a credit vertical in its direction bucket and short volatility, a debit vertical in its
  direction bucket and long volatility, the full maximum loss in each); "2 B": the books move to Rs 20 lakh by a dated
  Rs 15 lakh top-up entry (a separate story, `story/e1-topup`); "3 A": "A trade opened and closed in the same session
  counts toward the Rs 50,000 new-risk-per-session cap"; "4 A": the stress-line assumptions are accepted (information
  only); "5 A": "Stock-option risk buckets wait for A18".

C2 was built for a Rs 5 lakh account. With Rs 20 lakh, 15-20 protected NIFTY structures could be funded at once and
would all lose in the same crash, so limits apply to correlated groups (6.2). Design 6.1a: margin data older than one
session, an unmapped bucket or a missing margin row means no new entry. C4 recomputes every C2 limit with its own
arithmetic (judge 83 must-fix 3), so it changes in step.

**Scope.** In:
- risk profiles in `config.yaml` `risk.profiles`: `books` and `manual`, each listing the rules it runs and exactly
  their settings; every profile checked at start-up;
- the books' account size (`paper_account_rs`), used by E1 to open every new book and shadow account; a book opened
  with any other amount trades nothing until the owner decides how it is reopened;
- bucket, open-risk and new-risk-per-day caps as C2 rules on B2's maximum loss; bucket assignment as 6.2 defines it,
  failing closed on anything it does not map;
- the brake at Rs 1.2 lakh for the books (C2's rule and written restart record);
- margin freshness for the books: a row older than one NSE session refuses the entry (the Manual account keeps 7
  calendar days);
- C4: the same profile's rules, recomputed with C4's own arithmetic (bucket, held maximum loss, first-fill day, margin
  age); C4 drops the 3-open, stress and exposure checks for the books and keeps them for the Manual account;
- the daily stress line of 6.2 as a computed record.

Out: the Rs 15 lakh top-up that moves the three committed books to Rs 20 lakh (owner "2 B": story `e1-topup`, whose
criteria must make `PaperAccountSize` read the opening row plus top-ups and keep a top-up out of the brake's
high-water mark: it is capital, never a closed-equity gain; judge 105 minor 4); the
structure codes of directional spreads (STR1 adds them with two sides each, per "1 B"); stock buckets and "stock results this week" (events calendar A6/A12, stock
options A18); showing the stress line on the card (T1); a Manual account ledger and its desk (MA1); S1's protocol text
(`catastrophic_loss_book`, a draft the owner decides).

**Design:**
- `fno/risk/profile_settings.py`: `ProfileSettings` per profile; `RULE_SETTINGS` names each rule's settings; an
  unknown rule, a missing setting, a setting no listed rule uses, or not exactly one margin age is an error; four rules
  in every profile (paper account, per-trade loss, brake, margin room). `all_profiles` checks every profile.
- `fno/risk/settings.py`: what profiles share (scenarios, stress line, margins file, stressed margin).
- `fno/risk/buckets.py`: `BucketMap` interface, `StructureBuckets`: group from the contracts' underlying (NIFTY or
  BANKNIFTY), sides from the structure code through `bucket_sides`: one side (SF, SC short volatility; BF long
  volatility) or a list (a directional spread: its direction and a volatility side, "1 B").
- `fno/risk/open_risk.py`: `HeldMaxLoss` (B2's maximum loss of a held position from its ledger cash flow; a net short
  tail is refused; a locked-in position counts 0) and `PositionRisks`.
- `fno/risk/caps.py`: `MaxLossCap` with `BucketCap`, `OpenRiskCap`, `NewRiskPerDay`; `PaperAccountSize`.
- `fno/risk/margin_age.py`: `MarginAge` strategy: `DaysOld` (Manual), `SessionsOld` on NSE's calendar (books).
- `RiskBook.session_trades`: every trade first filled on the decision day, open or closed ("3 A"), with its held units
  and cash after each fill time (from E1's ledger; a trade chosen earlier the same session is added by D2; kept in
  D3's codec); its new risk is the largest maximum loss it carried; unknown (an old record) means refused.
- `fno/risk/stress_line.py`: `DailyStressLine` on C2's `StressEngine`.
- C4: `fno/checks/validity_caps.py` (own bucket, own held maximum loss on C4's one-point grid, caps, paper account),
  `validity_settings.py` (profile read raw from config.yaml, its own required-settings check), `validity_limits.py`
  (runs exactly the profile's rules), `validity_account.py` (the session's trades and their states, from the ledger).
- Wiring only in `fno/risk/wiring.py` (`RULES` table by rule name), `fno/checks/wiring.py`, `fno/composition.py`.

**Acceptance criteria:**
1. Bucket cap: at exactly Rs 30,000 passes, Rs 0.01 more refused (`bucket_cap`, the bucket, the numbers); other
   buckets not counted. A position with two sides counts its full maximum loss in each of its buckets, and a two-sided
   proposal must fit every one of its buckets ("1 B").
2. Open-risk cap: the same at Rs 1,50,000 across all buckets (`open_risk_cap`).
3. New risk per day: the same at Rs 50,000 for every trade first filled this session, open or already closed ("3 A"),
   at the largest maximum loss it carried; same-session choices count; trades first filled earlier do not, even if
   traded today; unknown session trades are refused.
4. A cap only refuses: the decision judges the very proposal it was given, lots unchanged.
5. Buckets as 6.2: SF/SC NIFTY short volatility, BF NIFTY long volatility; STR1's verticals in two buckets each ("1 B"):
   PCS bullish and short volatility, CCS bearish and short volatility, CDS bullish and long volatility, PDS bearish
   and long volatility; LC bullish and long volatility, LP bearish and long volatility (orchestrator decision while
   the owner was away, 15 Oct 2026, owner to confirm: a bought option is a directional bet that gains when movement
   grows, so it follows "1 B");
   BANKNIFTY its own group; an unlisted structure, a stock ("5 A": waits for A18), another index or mixed underlyings
   refused as "unmapped bucket".
6. A held trade's maximum loss equals B2's for the same entry; a not-defined-risk held position is refused.
7. New books open with Rs 20,00,000; a book opened with any other amount is refused (`paper_account`).
8. Books' brake at Rs 1,20,000 (Rs 0.01 less passes, at and beyond refuses); only a signed `restart_brake` row lifts it,
   in C2 and in C4. "Signed" means a non-empty `entered_by` (and reason): a typed name, protected by process only
   (`journal/` is lane 1 by path); a CI guard tying each row to an owner decision would be a later story. The brake and
   every cap apply per book, each book on its own Rs 20 lakh (orchestrator's reading of the owner's "2 B", owner to
   confirm on return).
9. Daily stress line: the five 6.2 scenarios, loss from entry and from marks, below the sum of maximum losses
   (assumptions accepted, information only: "4 A").
10. Profiles: the books run exactly paper account, per-trade loss, the three caps, brake and margin room; any setting
    problem in any profile, or a stray key under `risk`, stops start-up; C4 checks its own settings and their types.
11. The Manual profile keeps its 13 Oct limits unchanged (Rs 5 lakh, Rs 10,000, 3 open, Rs 30,000 brake, stress and
    exposure, 7-day margins) and its risk manager runs exactly those rules.
12. Books' margin rows older than one trading day refuse the entry, counted as A14 writes rows (`TradingDays`: regular
    and special sessions, never a muhurat-only session); a weekend, holiday or muhurat Sunday never ages a row.
13. C4 in step: for the books C4 recomputes paper account and the three caps itself, does not run 3-open, stress or
    exposure; a bucket breach C2 allowed is refused by C4; four open trades pass C4 for the books and fail for the
    Manual account; C4's held maximum loss equals C2's; C4 refuses to start on a missing setting.

**Test plan:** `tests/risk/test_caps.py`, `test_buckets.py`, `test_c5_account.py`, `test_margin_age.py`,
`tests/checks/test_validity_caps.py`; C2, C4, D2, E1, E4 and P10 tests updated. Every criterion broken on purpose once
(mutation table in the claims file).

**Judge verifies:** re-runs each cap at its number and one paisa over; plants an unmapped structure and a stock leg;
checks a held trade's maximum loss by hand; plants an unsigned restart row; breaks the Manual profile; feeds C4 a
breach C2 passed.

**Depends:** C2, C4, A7, A14, B2, E1, D2, D3, the owner's decisions of 14-15 Oct 2026 · **Size:** M · **Status:** done:
judge 105 addendum 2 PASS (b929743), merged a8379e6; inactive infrastructure (claims: reviews/claude/response_105_c5-risk-buckets.md)

---

## C5b. A brake restart cites the owner's decision row

**Repository:** trading

**Description:** As the risk manager, I want a drawdown-brake restart to be valid only when it cites the
`docs/DESK_DECISIONS.md` row that holds the owner's own words for that brake episode, with the judge's audit checking
it, so that the only thing that lifts a book's brake is a written owner decision, never a typed name alone.

**Context and why:**
- Owner, 15 Oct 2026 (caps accepted): "brake: closed equity Rs 1.2 lakh below its high stops new trades until the owner
  restarts in writing".
- Judge 105 minor 3: "signed" today means a non-empty `entered_by`. Any session can commit a `restart_brake` row with
  `entered_by: owner`. A guard tying each row to an owner decision would be a separate story.
- Orchestrator, 15 Oct 2026: this story, before the first counted paper decision; the judge's audit checks it; no
  cryptography (owner's simplicity rule, "Keep the design simple").
- `docs/DESK_DECISIONS.md` is where the owner's decisions are recorded, each row dated, in the standard form
  `**title** (owner: "...")` in its Decision cell. Measured on main (judge 134): 152 rows; 17 have no bold title, and
  one title ("approved") is the title of 4 rows. The owner names the books "Book 1", "Book 2" and "Book 3" (14
  times), never by their IDs.
- Today no book has an `owner_overrides.csv` (no brake has ever fired), so the file format can change without
  migrating any record.

**Scope.** In:
- a fifth column, `decision`, in `journal/<book>/owner_overrides.csv`: the cited row's title, which is the **first**
  `**...**` span of its Decision cell. A row with no bold span cannot be cited. The owner's restart decision is written
  in the standard form `**title** (owner: "...")`;
- a restart row is valid only if the cited row:
  - has that title exactly once in the file (a repeated title such as "approved" is refused);
  - quotes the owner (`(owner: "`);
  - names the restarted book by its display name as a whole word ("Book 1" for `book1_rules`, "Book 2" for
    `book2_hybrid`, "Book 3" for `book3_ai`: one map in `fno/constants.py`), so "Book 1" never matches "Book 10";
  - is dated on or before the restart date;
  - is cited by no other restart row of that book;
- the check in C2 (`fno/risk/overrides.py`) and, with its own code, in C4 (`fno/checks/validity_account.py`): an
  invalid row fails closed (the book cannot be read, so it trades nothing), exactly as a malformed row does today;
- the judge's audit of every new restart row: the owner's words really restart that book's brake for that episode.

Out:
- cryptographic signatures, and a CI guard on commits (owner's simplicity rule);
- deciding the episode by code (the judge's audit does it);
- the Manual account (no ledger yet).

**Design:**
- `fno/risk/overrides.py`: `OVERRIDE_COLUMNS` gains `decision`. A small `DecisionRows` reader parses the table rows of
  `docs/DESK_DECISIONS.md`: date, title (the first bold span of the Decision cell, or none) and full text.
  `brake_restarts` validates each row against it with the five rules above, as a `RiskInputError` with the reason.
- `fno/checks/validity_account.py`: C4's own parse of the same file (no `fno.risk` import), the same five rules,
  `AccountProblem` on failure.
- In `fno/constants.py`: the decisions file path (`DESK_DECISIONS_FILE`) and each book's display name
  (`BOOK_DISPLAY_NAMES`: `book1_rules` → "Book 1", `book2_hybrid` → "Book 2", `book3_ai` → "Book 3"), used by C2 and,
  read from constants (not from C2's code), by C4.
- No other change: the brake's arithmetic and the restart's re-arm level are C2's, unchanged.

**Acceptance criteria:**
1. A restart row citing a real owner row that names the book, dated on or before the restart, lifts the brake in C2
   and in C4 (tests with a planted decisions file).
2. Each of these fails closed in C2 and C4, with a reason naming the problem, and the book stays braked: a missing
   `decision`; a title not in the file; a title appearing twice; a row without `(owner: "`; a row not naming the book
   (a row naming "Book 1" lifts `book1_rules` and not `book2_hybrid`); a row dated after the restart; the same row
   cited by two restarts of one book.
3. The real `docs/DESK_DECISIONS.md` parses: every table row yields its date, and its title when its Decision cell has
   a bold span (none otherwise: not citable). The count of rows, of rows without a title, and of repeated titles
   matches the file (test on the committed file).
4. The judge's audit step is written into `docs/JUDGE.md`'s lane-1 checks for `journal/<book>/owner_overrides.csv`:
   read the cited row and confirm the owner's words restart that book's brake for that episode.

**Gap list:**

| Requirement (source) | Criterion or reason out |
|---|---|
| A restart only by the owner's written decision (owner 15 Oct caps row) | 1, 2 |
| The row holds the owner's own words (orchestrator) | 2 (`(owner: "`), 4 (audit reads the words) |
| For that brake episode (orchestrator) | 2 (dated on or before the restart, not reused), 4 (the audit judges the episode) |
| The judge's audit checks it (orchestrator) | 4 |
| No cryptography (owner's simplicity rule) | out |
| C2 and C4 in step (judge 83, C5) | 1, 2 |
| Before the first counted paper decision (orchestrator) | status: built before S1's freeze |

**Known limits (one line each):** the decisions file is plain text in the repository; anyone who can commit could add a
row. The protection is the judge's audit of every lane-1 change to it and to `owner_overrides.csv`.
A deleted `docs/DESK_DECISIONS.md` fails closed by an error, not a reason. A shadow book's brake cannot be restarted
(it is not named in the owner's decisions; its restart is refused).

**Test plan:** `tests/risk/test_restart_decision.py` (C2: criteria 1-3), `tests/checks/test_validity_restart.py`
(C4: 1-2), with planted decisions files in the standard `**title** (owner: "...")` form. Every criterion broken on
purpose once.

**Judge verifies:** plants a restart row citing a real row, a row without the owner's words, a row for another book and
a reused row; checks C2 and C4 refuse the bad ones; reads the JUDGE.md step.

**Depends:** C2, C4, C5 · **Size:** S · **Status:** text passed (judge 134 addendum 1); code built on
`story/c5b-restart-decision` for the judge (claims: `reviews/claude/response_135_c5b-restart-decision.md`, addendum 2)

---

## C2c. The stressed margin multiplies the whole margin, not the scan alone

**Repository:** trading · **Lane:** 1 (money and risk: C2's and C4's margin stress)

**Description:** As the risk manager, I want the owner's stress factor k to multiply the whole margin C2 counts (the
SPAN part and the exposure margin), as k was measured, so that the crash buffer covers a held trade's margin rising in
a crisis instead of almost nothing.

**Context and why:** Owner, 15 Oct 2026 (relayed by the orchestrator; A14c question 1): "WHOLE MARGIN. k multiplies
the whole margin (scan plus exposure), as it was measured." Today C2 and C4 stress the scan only (judge 75):
`max(0, k x scan - NOV) + min(0, NOV) + exposure`. On the real 14 Oct rows the scan is 1-14% of the margin (exposure
59,077.07 a lot on every row), so k = 1.45 adds +0.6% to SF 100 and 0% to every BF row, while 1.45 was measured as the
rise of the whole held margin (response 77). Strong evidence (response 77's own table, recomputed with
`MarginParts`).

**The change (one term):** the exposure margin is multiplied by k too; the SPAN part, the premium rule and the STR1 cap
stay as they are:

`stressed = max(0, k x scan - NOV) + min(0, NOV) + k x exposure` (and at entry, with no premium credit:
`max(0, k x scan - NOV) + k x exposure`).

For an uncapped credit structure (SF, SC) this is exactly `k x (what C2 counts)`; for a debit (BF) it is never below
that (the premium paid is still not multiplied, judge 75). For the capped credit spreads (CCS, PCS) the STR1 cap still
bounds the SPAN part, so the figure lies between what C2 counts and `k x` that (judge 174). On the 14 Oct rows at
k = 1.45, lot 65 (per lot, recomputed):

| Row | Broker (k = 1) | Stressed today | Stressed after C2c | At entry today | At entry after C2c |
|---|---|---|---|---|---|
| SF 100 | 59,899.32 | 60,269.33 | 86,854.01 | 66,340.33 | 92,925.01 |
| SF 300 | 62,679.37 | 64,300.40 | 90,885.09 | 81,434.40 | 108,019.09 |
| SC 300 | 67,594.67 | 71,427.59 | 98,012.27 | 81,580.59 | 108,165.27 |
| BF 300 | 59,077.07 | 59,077.07 | 85,661.75 | 59,077.07 | 85,661.75 |
| CCS 300 (capped) | 38,968.08 | 38,968.08 | 52,260.42 | 38,968.08 | 63,567.17 |

CCS 300: scan 9,429.55, NOV -11,306.75, exposure 29,538.53; the cap `300 x 65 - 11,306.75 = 8,193.25` is below the
broker's SPAN figure 20,736.30, so the SPAN part stays at the broker's and only the exposure is stressed:
`20,736.30 - 11,306.75 + 1.45 x 29,538.53 = 52,260.42`, against `k x 38,968.08 = 56,503.72`.

**What the owner should know (reasoning):** every stressed figure rises by about 45%, so about a third fewer lots fit
the same paper capital (C5's buckets and C2's caps unchanged). That is the buffer the owner chose working as measured.

**STR1 cap (story STR1b, `fno/risk/capital.py`):** the cap stays on the SPAN part only (the worst terminal loss beyond
the premium: 0 for a debit row, width x lot - credit for a credit spread), never below the broker's own unstressed
SPAN figure. The exposure is outside the cap: it is charged on the short legs' notional, rises with the index and by
NSE circular, and is not bounded by the spread's loss (reasoning). So for every code the stressed figure is never below
the broker's unstressed figure (k >= 1, settings refuse k < 1), and a bought-only code (LC, LP: no exposure) is
unchanged.

**Scope.** In: `fno/risk/margins.py` (`MarginParts.stressed`, `at_entry`, the module text and `record()`'s
`"stresses"` value), C4's independent copy `fno/checks/validity_margin.py` (`stressed_per_lot`), the `capital.py` text
("The owner's factor k stresses the scanning risk" becomes the scan and the exposure; the cap's rationale is unchanged),
their tests (`tests/risk/test_margin_formula.py`, `tests/risk/test_manager.py`, C4's margin tests). Out: the value of k
and its recompute (A14c); the scenario-lookup method; the STR1 cap's values; any order.

**Acceptance criteria:**
1. The five rows above (CCS 300 included, the cap and the stressed exposure together) equal C2's and C4's figures to
   the paisa on the real 14 Oct rows at lot 65 (test).
2. For uncapped credit rows (SF, SC) C2's stressed figure equals `k x initial()`; for debit rows (BF) it is not below
   it; for the capped credit spreads (CCS, PCS) it is at least `initial()` and at most `k x initial()`, with CCS 300's
   52,260.42 as the known answer (tests over every structure and width in a planted table, judge 174).
3. C2 and C4 agree on every planted row and k (test); a mutation in either copy (exposure unstressed, premium
   stressed, cap applied to the exposure) fails a test.
4. STR1 codes: the cap still bounds the SPAN part; the stressed figure is never below the broker's unstressed figure
   (tests at the cap's edges, k = 1 and k = 1.45); LC and LP unchanged.
5. Every decision record's stressed-margin method says what is stressed: `"stresses": "scan and exposure (owner,
   15 Oct 2026; story C2c)"`.
6. The claims list every existing pinned figure that changes (`tests/risk/test_margin_formula.py`,
   `tests/risk/test_manager.py`, C4's margin tests), each with its recomputation, so a changed expected value reads as
   a recompute, never a loosened test (judge 174).
7. Code size, lint, imports and the full suite pass.

**Order:** C2c goes before STR1b-2 (which lists `fno/risk/` but has not started); STR1b-2 builds on C2c's formula.

**Judge verifies:** recomputes two rows by hand; plants the three mutations in both C2 and C4; checks an STR1 credit
spread at its cap.

**Depends:** C2, C4, STR1b-1 · **Size:** S · **Status:** text for the judge (lane 1)

---

## C2d. C2 and C4 read the stress factor from A14c's file, not from config.yaml

**Repository:** trading · **Lane:** 1 (money and risk: C2's and C4's margin input)

**Description:** As the risk manager, I want C2 and C4 to take the stress factor k from the latest dated row of
`research/data/margins/stress_factor.csv`, which story A14c's weekly job appends, so that the owner's "automatic, with
an alert" rule works without any job editing `config.yaml`.

**Context and why:** Owner, 15 Oct 2026 (relayed by the orchestrator; A14c question 3): "AUTOMATIC, with an alert. The
job applies the new factor itself and posts it to #fno-desk." The orchestrator's design: the job never edits
`config.yaml` (lane 1); it appends the factor and its evidence to a data file and C2 reads the latest row. Today
`config.yaml` `risk.stressed_margin` holds `multiplier`, `source` and `as_of` by hand; `fno/risk/settings.py` and C4's
`fno/checks/validity_settings.py` each read them. Kept apart from C2c (the formula, already judged): C2d changes only
where k comes from, and must merge before A14c's first automatic run (about 6 Nov 2026).

**Scope.** In:
- `config.yaml` `risk.stressed_margin`: `method: multiplier`, `factor_file:
  research/data/margins/stress_factor.csv`, `max_age_days: 30`; `multiplier`, `source` and `as_of` leave config (the
  settings refuse them, so two sources can never disagree);
- one reader of the file used by both C2 (`fno/risk/`) and C4 (`fno/checks/`), or two by the same rule if C4's
  independence requires it (the builder says which and why): columns as A14c writes them (`as_of, factor, computed,
  unrounded, status, peak, evidence_sha256`); the factor in force on day d is the `factor` of the latest row with
  `as_of <= d` (point in time: a replay of day d never sees a later row); a missing file, a wrong header, no row on or
  before d, a factor below 1, or a row older than `max_age_days` fails closed by name, as today;
- the seed row, in the same commit as the switch: `2026-10-14, 1.45, 1.45, 1.45, applied, response 77 (three windows,
  owner decision 14 Oct), -` so C2 keeps the owner's current factor and its 13 Nov lapse until A14c's first run;
- every decision record's stressed-margin block names the row used: `as_of`, `factor`, `status` and
  `evidence_sha256` (the judge can reproduce it from the file).

Out: the factor's computation and the guardrails (A14c); the formula (C2c); the scenario-lookup method; any order.

**Acceptance criteria:**
1. Point in time: with rows dated 14 Oct (1.45) and 8 Nov (1.50), a decision on 7 Nov uses 1.45 and one on 8 Nov uses
   1.50; a replay of 7 Nov after the 8 Nov row exists still uses 1.45 (tests, C2 and C4).
2. Fail closed: no file, a wrong header, no row on or before the day, a factor below 1 and a row older than 30 days
   each refuse every trade with one named reason (tests, C2 and C4); a `held` row's `factor` (the old one) is the one
   used (test).
3. Single source: `config.yaml` with `multiplier`, `source` or `as_of` under `stressed_margin` is refused at start-up
   (test).
4. Same figures: on the seed row, C2's and C4's stressed margins equal today's on every 14 Oct row (test), so the switch
   changes no trade.
5. The decision record names the row used (test).
6. Code size, lint, imports and the full suite pass.

**Order:** after C2c, before A14c's first automatic run and before STR1b-2 (`fno/risk/`).

**Judge verifies:** plants a later row and replays an earlier day; deletes the file; checks the seed row equals the
owner's 14 Oct decision; reads one decision record.

**Depends:** C2, C2c, C4 · **Size:** S · **Status:** text for the judge (lane 1)
