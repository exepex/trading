# Real-money gate (story RM1)

**Status: DRAFT, not frozen. Nothing here allows, enables or places a real order.** The tool never places, modifies or
cancels an order; the owner places every real order by hand (design v2 8.4, `docs/DESK_DECISIONS.md` decision 8 as
amended on 15 Oct 2026). This file only fixes, before any counted paper result exists, when a strategy version may be
*put to the owner* for the small real-money test, and how that test is judged and stopped.

**Freeze.** This file is listed in evaluation protocol S1's `frozen_files` and is hashed by S1's freeze
(`python -m fno evaluation freeze`), which refuses while any item below is not complete or not decided by the owner.
So the gate is frozen before the first counted paper decision of every book (S1's `order` check). A change after the
freeze is a new protocol version; the pass mark is never lowered because time passed (owner, 14 Oct 2026, principle 4).

Item format: as `PROTOCOL.md` (Value, Status, Reason, Evidence). Items whose Reason names a question (Q1-Q13) need the owner's
written answer (questions in `reviews/claude/response_163_rm1-real-money-gate.md`); the others are the builder's
proposal, which the owner may accept as a set. The gate has no version line: it is versioned with S1's protocol.
The owner's answers to Q1-Q12 are the `docs/DESK_DECISIONS.md` row "RM1 real-money gate numbers" (15 Oct 2026, commit
946bb8e7); the review 118 changes are answered in `reviews/claude/response_171_chatgpt-review-118-answer.md`.

Terms used below:
- **Version:** one strategy version (playbook id and version; a changed rule is a new version and starts again).
- **Evidence record:** the version's completed paper positions in Book 1 (pure rules) whose entry decision is
  counted under the protocol version that holds this gate: the decision's commit has that version's freeze record as
  a strict git ancestor (S1 `reporting_per_version`, `fno/evaluation/order.py`). Filled by E8's owner-timing rule at
  R = 60 minutes (owner, 15 Oct 2026), after C1 charges and pads. Pilot positions (before the freeze) and positions
  of any shadow account are shown, never counted: no order check proves a shadow's decisions follow the freeze.
- **Paper price before pad:** the quote price a paper leg filled at (E8's snapshot ask for a buy, bid for a sell),
  without `FILL_PAD_RS`. Signed so that worse is positive, like every slippage below.
- **Valid quote:** a recorded ask (for a buy) or bid (for a sell) of the same contract, both sides present, with at
  least the leg's units quoted at that price (depth: Groww's bid and offer quantities, which A16 keeps in its raw
  answer). Its source and age (owner, 15 Oct 2026, Q12): for a real order, the owner's screenshot of Groww's bid and
  ask at the order, saved to Drive, at most 5 minutes old, with A16's snapshot as fallback within the same 5 minutes;
  for recorder-only uses (paper fills, cap fit), a recorder quote (A16 or the 3 pm recorder, A4) at most 15 minutes
  old. No valid quote means "unknown", which counts as not met; it is never zero and never a pass.
- **Execution slippage per unit:** a real leg's fill price minus the valid quote at the owner's order time (sells: the
  reverse), worse positive. This isolates execution from market movement; E8's paper fill is often next session
  (about 10:15), so the real-minus-paper price gap also holds the market's move and is reported apart as the
  **timing gap**, never judged as slippage (ChatGPT review 118).
- **Risk unit:** the position's modelled maximum loss at entry, every charge and pad included (B2, C2).
- **Real cap, real account:** the two owner numbers of `real_test_account`.

### `scope` What the gate decides
- **Value:** A version is "eligible to put to the owner" only when every condition item (`paper_evidence` to
  `owner_approval`) holds on the same review date. Eligibility is a report line, never an order, a setting or a
  switch. The small real-money test then runs under `real_test_account` to `real_test_stops`. Scaling beyond 1 lot and
  any Groww API automation stay outside this gate: each needs a test pass and a separate written owner decision
  (automation also a fresh check of SEBI's retail algorithmic trading rules).
- **Status:** proposal, owner decides
- **Reason:** Design v2 8.3 and 8.4; the hard line "never place orders" stays.
- **Evidence:** reasoning only

### `paper_evidence` Condition 1: the paper record makes money after costs
- **Value:** On the version's evidence record, all three hold:
  1. **Sample:** the larger of S1's `paper_gate` (3 full calendar months and 20 completed positions) and the sample
     the version's registration named (G3 sample plan).
  2. **Lower bound:** the one-sided 95% lower bound of net per risk unit (sum of net ÷ sum of risk units, recomputed
     on each resample) is above zero: a bootstrap of completed positions, 10,000 resamples, seed 20261014,
     nearest-rank 5th percentile (E6's method, S1 `strategy_review_rule`). **And** the t-based lower bound (mean of
     net per risk unit minus the one-sided 95% t quantile × its standard error) is above zero.
  3. **Whole period:** the record's total net is above zero.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 1. Both bounds binding is the owner's answer to Q6 (15 Oct 2026). The t-check is a printed warning on scoreboards (owner, 15 Oct 2026, decision 167);
  for real money the proposal makes it a pass condition because a bootstrap of few, skewed positions claims too
  often (some evidence: S1's own note on 6 blocks), and an extra condition can only make the gate stricter.
- **Evidence:** some evidence

### `index_benchmark` Condition 2: beats doing nothing after tax
- **Value:** S6's `beats_index_after_tax` (view (a), net per rupee of capital tied, against the NIFTY 50 index fund
  on the same capital-days) is true over the evidence record's months, with F&O net taxed at 31.2%. Null (not
  computable) counts as not met. Only the evidence record counts; Books 2-3 trades of the version are shown, never
  combined into it.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 2; owner decision 168. Judge 158 asked how several books' values combine: the gate reads
  one record, Book 1's, the one whose trades the real test copies. A point comparison with no interval; tax is
  labelled an assumption until verified.
- **Evidence:** reasoning only

### `loss_caps` Condition 3: every loss stayed within its cap, in the record and in the crash replays
- **Value:** (a) Every completed position's net loss is at most its risk unit (no loss beyond the modelled maximum).
  (b) The version's rules replayed through 20 Feb-30 Apr 2020 and 3-7 Jun 2024, at 1 lot, from NSE's daily F&O
  settlement files, with C1 charges and the pad in force at the review added to every leg: every replayed
  position's loss is at most the real cap. This is a **daily-settlement proxy**, not an executable intraday result. A
  replay that cannot be run (missing data) counts as not met.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 3; the replay cap is the real cap at 1 lot, Rs 5,000 (owner, 15 Oct 2026, Q7); owner principle 4 (14 Oct 2026) names the 2020 and 2024 crashes.
- **Evidence:** reasoning only

### `fill_honesty` Condition 4: paper fills were not kinder than the market
- **Value:** (a) **Binding, quote validity:** every paper fill leg on the evidence record was priced from a valid
  quote at its fill time (fresh, two-sided, with depth), checked against the hashed snapshot E8 filled from; one
  invalid leg is not met.
  (b) **Reported, never judged, independent check:** for each leg with a valid quote from a *different* recorder at
  the fill time, gap per unit = that quote minus the paper price before pad (buys: its ask minus the paper price;
  sells: the paper price minus its bid), with its mean and count; with no such leg it reads "unknown" (owner,
  15 Oct 2026, Q13 (a)).
  A16 records only the nearest weekly and nearest monthly NIFTY expiries, so a version trading any other expiry
  cannot meet (a) until A16 records it.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 4; the owner's answer to Q13 (a). ChatGPT review 118: a later snapshot moving is not
  proof of a dishonest fill, and the fill's own snapshot cannot prove its price by itself. An independent quote at
  fill time will be rare (E8 fills at about 10:15 next session from A16; the 3 pm recorder runs near 14:30-14:55), so
  a binding independent check would block every version; the real execution cost is judged by `real_test_pass` 3.
- **Evidence:** reasoning only

### `selection_adjustment` Condition 5: the edge survives the number of ideas tried
- **Value:** The version's registration names one route before its first counted entry; with none named, route (a).
  - **(a) Second untouched period:** after condition 1 first passes, a new forward paper period of the same version,
    with the same sample size as condition 1's, must pass conditions 1 to 4 on its own positions only. No rule,
    setting or code of the version changes between the two periods.
  - **(b) Multiplicity:** condition 1's lower bounds use one-sided level 0.05 ÷ m instead of 0.05, where m is the
    research ledger's trial count (every registered idea, screened-out and abandoned ones included) on the review
    date, fixed at that one predeclared review (Bonferroni, which is also Holm's first step; valid for one fixed
    family and one look, so a later re-check is a new review with its own count).
- **Status:** proposal, owner decides
- **Reason:** Route (a) is the default by the owner's answer to Q4 (15 Oct 2026). 8.3 condition 5 (owner decision 8 amended, "B ... => I accept"). With m = 50, route (b) needs a 99.9%
  bound: about 10 of 10,000 bootstrap resamples set it, so it is noisy; route (a) costs time but is cleaner.
- **Evidence:** some evidence

### `real_cap_fit` Condition 6: the trade fits the real cap and the rules of the day
- **Value:** At the review date: (a) the version's last 20 eligible entry opportunities (the cards it actually
  issued), each re-priced at 1 lot with its own contracts, its dated NSE lot size, the valid quotes at its entry and
  C1 charges, have a risk unit at most the real cap; fewer than 20 opportunities, or any missing quote, is not met;
  (b) the next proposed real trade fits the real cap at current valid quotes before the owner places it; (c) a dated
  note in `docs/DESK_DECISIONS.md` records a fresh check of SEBI's F&O and retail algo rules and of the tax treatment,
  with sources.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 6; ChatGPT review 118 (opportunities, not arbitrary days). Fact for the owner: NIFTY's lot
  is 65 (`config.yaml`), so a Rs 5,000 cap allows 76.9 index points of maximum loss per unit before charges
  (Rs 4,000: 61.5). A credit vertical's loss per lot is 65 × (width − credit) + charges: width 100, credit 30,
  charges Rs 200 gives Rs 4,750 (fits Rs 5,000); width 200 gives Rs 11,250 (fails). One bought at-the-money monthly
  option usually costs more than the cap, so in practice only spreads or far options fit (some evidence).
- **Evidence:** some evidence

### `owner_approval` Condition 7: the owner says yes in writing
- **Value:** A dated row in `docs/DESK_DECISIONS.md` quoting the owner, naming the version and accepting the test.
  The tool never starts the test on its own.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 7.
- **Evidence:** reasoning only

### `real_test_account` The small test's account, cap and size
- **Value:** Real account Rs 2,00,000 funded by the owner; per-trade cap Rs 5,000 (2.5%), every charge included;
  1 lot per trade (owner, 15 Oct 2026, Q1 and Q2).
- **Status:** proposal, owner decides
- **Reason:** Owner questions Q1 and Q2. 8.4; owner decision 8 requires the exact numbers in writing before the freeze.
- **Evidence:** reasoning only

### `real_test_sample` How long the test runs
- **Value:** The later of (a) max(30, the version's registered number of trades) real trades placed and (b) 6 months
  from the first real entry (owner, 15 Oct 2026, Q3).
- **Status:** proposal, owner decides
- **Reason:** 8.4: "its registered number of trades or 6 months, whichever is later" (decision 8). The floor of 30
  is the owner's answer to Q3; it only matters when a registration names fewer.
- **Evidence:** reasoning only

### `real_test_pass` The paired real-versus-paper test
- **Value:** Each real trade is paired with the paper trade of the same card (E8, R = 60, scaled to 1 lot). All four
  must hold at the end:
  1. **Paired net (binding):** d = real net − paper net per paired trade, charges included. The one-sided 95% lower
     bound of the mean of d (mean − t(0.95, n−1) × SD(d) ÷ √n) is at or above −Rs 500 per trade at 1 lot (owner,
     15 Oct 2026, Q11).
  2. **Prediction floor:** the real trades' mean net per trade is at or above paper mean − t(0.95, m−1) × paper SD ×
     √(1/n + 1/m), from the evidence record's m positions. This is a model-based prediction bound (independent,
     normally distributed trades assumed; option returns are skewed and can cluster, so it is a floor, not a
     guarantee).
  3. **Execution:** the mean execution slippage per unit over all real legs is at most the paper pad (`FILL_PAD_RS`
     in force) + Rs 0.50; more than 10% of real legs with unknown slippage is not met (owner, 15 Oct 2026, Q12).
  4. **Discipline:** the owner placed at least 90% of the version's eligible cards in the period (owner, 15 Oct 2026,
     Q8); every skipped card is listed with its paper net, never counted as real.
  Reported, not judged: the timing gap per leg and its mean, and the paired mean with its two-sided 95% interval.
- **Status:** proposal, owner decides
- **Reason:** 8.4 (owner decision 8 amended) asks for a paired test and a prediction interval, never the narrower
  interval of paper's mean; ChatGPT review 118 showed the paired comparison must bind, not only be reported. The
  margin (Q11), the one-sided side (Q5) and the discipline share (Q8) are the owner's answers of 15 Oct 2026. Only underperformance fails, so bounds are one-sided.
  Fact: with n = m = 20 and SD Rs 5,000 the prediction floor sits about Rs 2,160 below paper's mean, a weak filter.
- **Evidence:** some evidence

### `real_test_stops` When the test stops early
- **Value:** Stop and report at once when any holds (owner, 15 Oct 2026, Q9: both loss stops): (a) cumulative real
  net from the first real entry reaches minus Rs 20,000, every charge included; (a2) cumulative real net falls
  Rs 20,000 below its highest value since the first real entry (peak to trough), every charge included; (b) the mean execution slippage per unit over the legs of any 5
  consecutive real trades exceeds twice the paper pad (legs with unknown slippage left out of the mean and listed). A stop is a fail; a new test needs a new owner decision.
- **Status:** proposal, owner decides
- **Reason:** (a) and (a2) are the owner's answer to Q9. 8.4; both numbers are the owner's (decision 8).
- **Evidence:** reasoning only

## Known limits

- The paired net (`real_test_pass` 1) compares the owner's fill with E8's later paper fill, so it holds market moves
  as well as execution; execution alone is judged by `real_test_pass` 3, from quotes at the owner's order time.
- 20 real trades give a wide prediction interval: the test finds only a large shortfall, not a small one.
- The 2020 and 2024 replays are daily-settlement proxies with today's charges and pad, not intraday fills.
- Shadow records never count toward the gate until a story proves their decisions follow the freeze (judge 171 SF1).
- SEBI and tax rules can change between the freeze and the test; condition 6 re-checks them, it cannot freeze them.
