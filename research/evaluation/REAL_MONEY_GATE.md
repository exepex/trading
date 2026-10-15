# Real-money gate (story RM1)

**Status: DRAFT, not frozen. Nothing here allows, enables or places a real order.** The tool never places, modifies or
cancels an order; the owner places every real order by hand (design v2 8.4, `docs/DESK_DECISIONS.md` decision 8 as
amended on 15 Oct 2026). This file only fixes, before any counted paper result exists, when a strategy version may be
*put to the owner* for the small real-money test, and how that test is judged and stopped.

**Freeze.** This file is listed in evaluation protocol S1's `frozen_files` and is hashed by S1's freeze
(`python -m fno evaluation freeze`), which refuses while any item below is not complete or not decided by the owner.
So the gate is frozen before the first counted paper decision of every book (S1's `order` check). A change after the
freeze is a new protocol version; the pass mark is never lowered because time passed (owner, 14 Oct 2026, principle 4).

Item format: as `PROTOCOL.md` (Value, Status, Reason, Evidence). Items marked "owner number" need the owner's written
answer (questions in `reviews/claude/response_163_rm1-real-money-gate.md`); the others are the builder's proposal,
which the owner may accept as a set.

Terms used below:
- **Version:** one strategy version (playbook id and version; a changed rule is a new version and starts again).
- **Evidence record:** the version's completed forward paper positions in Book 1 (pure rules) or its registered
  shadow account, filled by E8's owner-timing rule at R = 60 minutes (owner, 15 Oct 2026), after C1 charges and pads.
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
- **Status:** proposal, owner decides (the "and" in 2 is owner question Q6)
- **Reason:** 8.3 condition 1. The t-check is a printed warning on scoreboards (owner, 15 Oct 2026, decision 167);
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
  one record (Book 1 or the shadow), the one whose trades the real test copies.
- **Evidence:** reasoning only (a point comparison, no interval; tax labelled an assumption until verified)

### `loss_caps` Condition 3: every loss stayed within its cap, in the record and in the crash replays
- **Value:** (a) Every completed position's net loss is at most its risk unit (no loss beyond the modelled maximum).
  (b) The version's rules replayed through 20 Feb-30 Apr 2020 and 3-7 Jun 2024, at 1 lot, from NSE's daily F&O
  settlement files: every replayed position's loss is at most the real cap. A replay that cannot be run (missing
  data) counts as not met.
- **Status:** proposal, owner decides (the replay windows; the replay cap is owner question Q7)
- **Reason:** 8.3 condition 3; owner principle 4 (14 Oct 2026) names the 2020 and 2024 crashes.
- **Evidence:** reasoning only

### `fill_honesty` Condition 4: paper fills were not kinder than the market
- **Value:** For each paper fill leg, the gap per unit = how much better the paper price was than the first A16
  snapshot after the fill (buys: that snapshot's ask minus the paper price before pad; sells: the paper price before
  pad minus its bid). The mean gap over all the record's legs is at most the pad in force at each fill. Fewer than 20
  legs with a snapshot counts as not met.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 4: a positive mean gap larger than the pad means paper bought cheaper than the market let.
- **Evidence:** reasoning only

### `selection_adjustment` Condition 5: the edge survives the number of ideas tried
- **Value:** The version's registration names one route before its first counted entry; with none named, route (a).
  - **(a) Second untouched period:** after condition 1 first passes, a new forward paper period of the same version,
    with the same sample size as condition 1's, must pass conditions 1 to 4 on its own positions only. No rule,
    setting or code of the version changes between the two periods.
  - **(b) Multiplicity:** condition 1's lower bounds use one-sided level 0.05 ÷ m instead of 0.05, where m is the
    research ledger's trial count (every registered idea, screened-out and abandoned ones included) on the review
    date (Holm's first step, which is the step the best idea faces).
- **Status:** owner number (the default route, Q4)
- **Reason:** 8.3 condition 5 (owner decision 8 amended, "B ... => I accept"). With m = 50, route (b) needs a 99.9%
  bound: about 10 of 10,000 bootstrap resamples set it, so it is noisy; route (a) costs time but is cleaner.
- **Evidence:** some evidence

### `real_cap_fit` Condition 6: the trade fits the real cap and the rules of the day
- **Value:** At the review date: (a) the version's structure at 1 lot, at the NSE lot size in force that day, has a
  risk unit at most the real cap, checked on the last 20 sessions' 15:00 quotes (every one must fit); (b) a dated
  note in `docs/DESK_DECISIONS.md` records a fresh check of SEBI's F&O and retail algo rules and of the tax treatment,
  with sources.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 6. Fact for the owner: NIFTY's lot is 65 (`config.yaml`), so a Rs 5,000 cap allows about
  76 index points of maximum loss per unit, charges included; one bought at-the-money monthly NIFTY option usually
  costs more than that, so in practice only spreads or far-from-the-money options fit (some evidence).
- **Evidence:** some evidence

### `owner_approval` Condition 7: the owner says yes in writing
- **Value:** A dated row in `docs/DESK_DECISIONS.md` quoting the owner, naming the version and accepting the test.
  The tool never starts the test on its own.
- **Status:** proposal, owner decides
- **Reason:** 8.3 condition 7.
- **Evidence:** reasoning only

### `real_test_account` The small test's account, cap and size
- **Value:** Real account Rs 2,00,000 funded by the owner; per-trade cap Rs 5,000 (2.5%), every charge included;
  1 lot per trade.
- **Status:** owner number (Q1, Q2)
- **Reason:** 8.4; owner decision 8 requires the exact numbers in writing before the freeze.
- **Evidence:** reasoning only

### `real_test_sample` How long the test runs
- **Value:** The later of 20 trades placed and 6 months from the first real entry.
- **Status:** owner number (Q3)
- **Reason:** 8.4 says "its registered number of trades or 6 months, whichever is later"; 20 matches S1's paper gate.
- **Evidence:** reasoning only

### `real_test_pass` The paired real-versus-paper test
- **Value:** Each real trade is paired with the paper trade of the same card (E8, R = 60). At the end:
  1. **Net:** the real trades' mean net per trade is at or above the lower end of the one-sided 95% prediction
     interval for the mean of n new trades, built from the version's evidence record (m positions, scaled to 1 lot):
     paper mean − t(0.95, m−1) × paper SD × √(1/n + 1/m).
  2. **Slippage:** the mean of real-minus-paper fill slippage per unit is at most the paper pad + Rs 0.50.
  3. **Discipline:** the owner placed at least 80% of the version's cards in the period; skipped cards are listed and
     their paper results shown, never counted as real.
  The paired mean real-minus-paper net and its 95% confidence interval are reported, not judged.
- **Status:** owner number (one-sided side, Q5; discipline share, Q8)
- **Reason:** 8.4 (owner decision 8 amended): a prediction interval, never the narrower interval of paper's mean.
  Only underperformance fails, so the interval is one-sided.
- **Evidence:** some evidence

### `real_test_stops` When the test stops early
- **Value:** Stop and report at once when either holds: (a) cumulative real net from the first real entry reaches
  minus Rs 20,000, every charge included; (b) the mean real slippage per unit over any 5 consecutive trades exceeds
  twice the paper pad. A stop is a fail; a new test needs a new owner decision.
- **Status:** owner number (the base of (a), Q9)
- **Reason:** 8.4; both numbers are the owner's (decision 8).
- **Evidence:** reasoning only

## Known limits

- A real trade is filled by the owner's hand and time; the paper side uses E8's 60-minute fill, so timing differences
  sit inside the paired gap.
- 20 real trades give a wide prediction interval: the test finds only a large shortfall, not a small one.
- The 2020 replay uses daily settlement prices, not intraday quotes.
- SEBI and tax rules can change between the freeze and the test; condition 6 re-checks them, it cannot freeze them.
