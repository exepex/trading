# Evaluation protocol of the three books (story S1)

Protocol version: 1

**Status: DRAFT, not frozen.** The owner decided five items on 14 Oct 2026 (`uncertainty_criterion`,
`catastrophic_loss_strategy`, `ai_cost_allocation`, `reporting_per_version`, `frozen_files`;
`docs/DESK_DECISIONS.md`). Every other value is still a proposal. Nothing is counted under this protocol until the
owner decides each item, the protocol is frozen (`python -m fno evaluation freeze`), and the freeze record
is committed before the first counted decision of every book. Builder: Claude, 14 Oct 2026, branch
`story/s1-protocol`.

How to read an item:
- **Value** is the exact value or rule.
- **Status** is "proposal, owner decides" until the owner decides it, then "decided by the owner on <date>".
- **Reason** says why this value.
- **Evidence** is the project's label: strong evidence, some evidence, or reasoning only.

`python -m fno evaluation check` checks that every item is present and has a value. It rejects the words that leave
an item open. `--decided` also requires the owner's decision on every item; the freeze requires both.

## Plain facts the proposals rest on

- **Trade frequency is low.**
  - Every strategy in the playbook format enters a monthly NIFTY expiry 30-45 days out and exits 21 days before
    expiry. So it holds a position about 9-24 calendar days (about 7-17 trading days), at most one position per
    monthly expiry.
  - At one strategy version, that is about one completed position a month: **20 positions take about 20 months**.
  - Several approved strategies shorten that. Six months of one strategy gives about 6 positions, too few for any
    interval to mean much.
- **Daily account results overlap.** A position's daily profit and loss is correlated across its holding period. A
  bootstrap over days therefore needs blocks at least one holding period long.
- **The three books do not exist together yet.** Book 1 can trade once a strategy is approved. Book 2 waits for D4
  (envelope), and Book 3 waits for D5 (constitution) and F1-F5 (the AI layer).

## Items

### `common_start` Common start date
- **Value:** The rule, not a date: the first NSE session on which every one of the three books has an on-time
  committed decision record (D3, committed before that day's execution snapshot) made under a version registered
  before it (D6). The date is read from the records by code (S2), never chosen by a person.
- **Status:** proposal, owner decides
- **Reason:** Design 12.6 asks for a predeclared start "when all three books can trade". A rule read from the records
  cannot be moved after results are seen. A calendar date chosen now would be a guess, because books 2 and 3 are not
  built.
- **Evidence:** reasoning only

### `pilot_evidence` Pilot evidence
- **Value:** Every decision dated before the common start is pilot evidence:
  - Book 3's (design 12.6), and also Book 1's and Book 2's.
  - It is reported in its own section, labelled "pilot, not head-to-head", and never enters either scoreboard's
    head-to-head figures or any promotion.
  - Cash a book holds before the common start is not counted. After it, holding cash is an outcome.
- **Status:** proposal, owner decides
- **Reason:** Book 1 will likely trade months before books 2 and 3. Its early record is useful but was not earned
  under the same conditions, so it is kept apart exactly like Book 3's pilot.
- **Evidence:** reasoning only

### `timetable` Daily timetable (IST)
- **Value:**
  - Data cutoff for every book 15:00.
  - Common pack first try 14:58, retried until 15:10.
  - Decision deadline 15:12.
  - Execution snapshot 15:15.
  - Fills and exits finished by 15:20.
  - Account lock lease 60 seconds.

  Scoring at the snapshot and at the fill (story G10):
  - The 15:15 execution snapshot gives a skill score that is a diagnostic only: no book, strategy or version is
    promoted on it; the money verdict uses the 60-minute fill (E8; owner, 15 Oct 2026; story G10).
  - An instrument not available at the 60-minute fill is a no-fill, never a fabricated fill (story G10).

  These are the values in `config.yaml` `desk.timetable` today (E3, "proposed until S1"). They are confirmed or
  changed by this rule: before the freeze, at least 10 sessions of measured run times. Each step's slot must then be
  at least the measured 95th-percentile duration plus 60 seconds. If that cannot hold before 15:20, the owner
  chooses which step moves.
- **Status:** proposal, owner decides
- **Reason:** Design 13.5 asks for times "calibrated with A4 and measured run times". None are measured yet, since
  the daily run (E3) is new. The current times leave 2 minutes from deadline to snapshot and 5 minutes for fills.
  These look tight for an AI book's session.
- **Evidence:** reasoning only

### `segments` Evaluation segments
- **Value:** D6's rule, as built and judged:
  - A decision belongs to the segment of the book's version active on its day.
  - A version counts only if its registry row's commit and its `registered_in_commit` are strict git ancestors of the
    decision's commit.
  - A decision whose served components (model, prompt, roles, envelope, playbook, config) differ from the registered
    version is unscored, and scoring for that book pauses until a new version is registered.
  - Each segment is reported separately and never pooled into the primary verdict. A segment below the minimum sample
    is shown, not judged.
- **Status:** proposal, owner decides
- **Reason:** Design 12.6: a change of model, prompt, role set, envelope or strategy is a new test. Pooling versions
  would credit one version with another's results.
- **Evidence:** some evidence

### `primary_metric` Primary verdict measure
- **Value:** Net account result after every cost, within the owner's risk budget (C2), on both scoreboards.
  - **Costs:**
    - execution: E4 fills and C1 charges;
    - operating: allocated AI plan cost (F8), labelled "allocated, not a bill", plus any actual cash spend.
  - **Net per unit of risk:** the period's mean daily net account change divided by its mean daily risk at stake. Risk
    at stake on a day is the sum of the maximum loss at entry of every open position.
  - **Also reported, never as the verdict:** gross, execution costs, AI and data costs, trades, stress usage,
    margin-days. Forecast scores are secondary and never promote a book.
- **Status:** proposal, owner decides
- **Reason:** Design 12.8. A ratio of means (not a mean of daily ratios) stays defined on days with no position, and
  weights each day by the risk actually taken.
- **Evidence:** reasoning only

### `scoreboard_a_standardisation` Scoreboard A standardisation
- **Value:** Each matched decision on the common opportunity set is scored on its own standardised shadow account:
  - one lot;
  - entered at the day's execution snapshot by the E4 fill model, with C1 charges;
  - exited by the strategy's own exit rule recorded with the decision, at the E4 fill model's exit price;
  - no cash, slot or margin limits, and no compounding;
  - scored as net per unit of maximum loss at entry.

  A "no trade" scores zero. Book 3's matched shadow decision is scored the same way.
- **Status:** proposal, owner decides
- **Reason:** Scoreboard A asks whether the decision was good, so sizing and account state (which scoreboard B covers)
  are removed. One lot and the same fills make the three books' decisions directly comparable.
- **Evidence:** reasoning only

### `uncertainty_criterion` Uncertainty criterion for promotion or combination
- **Value:** A claim is made only when all of these hold. A claim is "book X makes money" or "X beats Y", and only a
  claim allows promotion or combination.
  1. **Sample:** the minimum sample is met (`paper_gate`, plus at least 120 trading days since the common start).
  2. **Lower bound:** the one-sided 95% lower bound of net per unit of risk is above zero. For "X beats Y", use the
     paired daily difference instead.
     - The bound comes from a moving-block bootstrap over trading days of (daily net change, daily risk at stake)
       pairs.
     - Block length 20 trading days; 10,000 resamples; seed 20261014; nearest-rank 5th percentile.
     - The ratio of means is recomputed on every resample.
  3. **Whole period:** the whole period's net is above zero.

  When several claims are made at one review, Holm's correction across them sets each claim's one-sided level.
- **Status:** decided by the owner on 2026-10-14
- **Reason:**
  - **The owner's decision (14 Oct 2026):** 120 trading days (about 6 months), against the orchestrator's
    recommendation of a year plus a t-based check. The known weakness stays: 120 days at 20-day blocks is about 6
    blocks, and a percentile bootstrap from 6 blocks covers less than its stated 95%, so it claims too often (some
    evidence). Whether to add the t-based check alongside is with the owner; it is not part of this rule.
  - The block covers one holding period (about 7-17 trading days), so overlapping positions are not counted as
    independent. 20 days also matches the forecast protocol's block.
  - The seed is E6's, so one seed serves all reviews.
  - Holm keeps the chance of any false claim at a review near 5% when three books and their pairs are tested.
- **Evidence:** reasoning only

### `paper_gate` Minimum paper sample
- **Value:** Design 6's gate, kept:
  - at least 3 full calendar months since the strategy version's first entry, and at least 20 completed positions;
  - open positions are reported at their marks and never counted;
  - the gate is a minimum, not proof.

  This is `PAPER_GATE_MONTHS` = 3 and `UNPROVEN_BELOW_COMPLETED_TRADES` = 20 in `fno/constants.py`.
- **Status:** proposal, owner decides
- **Reason:** With about one position a month per strategy, 20 positions take well over a year. A lower number would
  give intervals too wide to separate a real edge from noise, so I do not propose lowering it.
- **Evidence:** reasoning only

### `strategy_review_rule` Strategy review rule (E6's provisional terms)
- **Value:** E6's rule. It is unchanged except that the promotion bar becomes `uncertainty_criterion`.
  - **Sample:** each completed position's C1 net.
  - **Interval:** a two-sided 95% interval of the mean, by a seeded bootstrap of positions (10,000 resamples, seed
    20261014, nearest-rank tails).
  - **Decision at a review date, once the gate is met:**
    - retire when the interval's upper end is below the plan's expected low;
    - pause when the mean is below it;
    - keep otherwise.
  - **"Net profit shown"** requires the interval's lower end and the version's whole net above zero.
  - A review's decision is stated, never applied: only the owner pauses for statistics or retires.
- **Status:** proposal, owner decides
- **Reason:**
  - A strategy's positions do not overlap (one per monthly expiry), so resampling positions independently is sound
    here. It would not be for the books' daily series.
  - Keeping E6's terms means E6 needs no code change: config `scorecard_review` holds them, and only its status line
    changes at the freeze.
- **Evidence:** some evidence

### `catastrophic_loss_strategy` Catastrophic-loss rule per strategy
- **Value:** A strategy version is paused at once, with no new trades in any book (E6), when either of these holds:
  - one completed position's C1 net loss reaches its plan's `catastrophic_loss_rs` (at most C2's Rs 10,000 per-trade
    maximum loss); or
  - the version's cumulative realised C1 net reaches minus 3 times its `catastrophic_loss_rs` (Rs 30,000 at Rs
    10,000). The count covers the version's book trades closed since its latest change to paper, in all books
    together; shadow trades are excluded; an owner re-approval restarts the count (owner, 14 Oct 2026).
- **Status:** decided by the owner on 2026-10-14
- **Reason:**
  - The first rule is E6's, already built.
  - The second is new: a run of losses each below the per-trade limit would otherwise never pause the strategy. At
    Rs 10,000 it equals the book's drawdown brake, so one strategy alone cannot spend a whole book's brake unnoticed.
- **Evidence:** reasoning only

### `catastrophic_loss_book` Catastrophic-loss rule per book
- **Value:** C2's drawdown brake, unchanged:
  - while closed equity is Rs 30,000 or more below its high, the book opens no new trade;
  - only the owner's restart row lifts it;
  - open trades are never closed by the brake.
- **Status:** proposal, owner decides
- **Reason:** It is the owner's own decision of 12 Oct 2026 (`docs/DESK_DECISIONS.md`), the same for all three books.
  Repeating it here freezes it for the comparison.
- **Evidence:** reasoning only

### `immediate_pauses` Pauses before a scheduled review
- **Value:** Only these act before a scheduled review:
  - the book's drawdown brake;
  - the strategy catastrophic-loss rules above;
  - a data failure (C3: no new trades that day);
  - a hard-validity failure (C4: that trade is blocked);
  - an integrity failure: an edited decision record (D3), or a served component that differs from the registered
    version (D6: that book's scoring pauses);
  - a safety instruction from the owner.

  No book or strategy is switched off for statistical reasons before a scheduled review.
- **Status:** proposal, owner decides
- **Reason:** Design 12.8. Stopping early on a bad-looking streak is the main way paper results get reinterpreted.
- **Evidence:** reasoning only

### `review_dates` Scheduled review dates
- **Value:**
  - **First book review:** the last NSE session of the sixth full calendar month after the common start. Example:
    common start 2 Dec 2026 means the first review on June 2027's last session.
  - **Then:** every 3 calendar months, on the month's last session.
  - **Monthly reports:** descriptive only, never decisions.
  - **Strategy reviews:** on the dates in each playbook version's evaluation plan (E6). They act only once the paper
    gate is met.
- **Status:** proposal, owner decides
- **Reason:** Design 12.8 sets the first review after 6 months of common-start trading. Quarterly reviews after that
  limit how often the data is looked at with intent to act.
- **Evidence:** reasoning only

### `ai_cost_allocation` AI cost allocation formula (F8)
- **Value:**
  - **Formula:** for each calendar month, book b's allocated cost = the owner's recorded plan cost × (book b's
    measured Claude session minutes) ÷ (all measured Claude session minutes on the plan that month).
    - "All" includes development work: builder, judge, orchestrator and research sessions. Development's share is
      shown as "development, not a book cost".
    - Book 1 uses no AI and is allocated zero.
  - **Rounding:** to the paisa, with the remainder added to the largest share, so the shares sum exactly to the plan
    cost.
  - **Missing cost:** a month with no recorded plan cost shows "unknown", never zero.
  - **Tokens:** not used, because most sessions do not report them.
  - **Label:** "allocated, not a bill". Actual cash spend is shown apart.
- **Status:** decided by the owner on 2026-10-14
- **Reason:** Design 13.6.
  - Usage share is the simplest formula that sums exactly.
  - **The owner's choice here is real.** Counting development in the denominator lowers the books' cost, and while
    development dominates usage, the books' share will be small.
  - The alternative is to divide the plan cost among the books' minutes only, which charges the books the whole
    plan. It is stricter and makes an AI book harder to justify. I propose usage share, because the plan exists for
    development anyway (reasoning only).
- **Evidence:** reasoning only

### `role_value_schedule` Role-value evaluation and ablation schedule (F9)
- **Value:**
  - **Rotation:** for books 2 and 3, each trading day from the common start ablates exactly one role or declared
    bundle.
    - It cycles through the version's registered roles and bundles in the order of their identifiers.
    - A day the book is unavailable does not advance the cycle.
    - Mandatory control roles (data, risk, cost, validity, the judge's hard checks) are never ablated. They are scored
      on caught violations and prevented invalid actions.
  - **Shadow decision:** made with the role's card withheld, from the same packs, by the same deadline. It is valued
    like scoreboard A (one lot, E4 fills on the day's execution snapshot, C1 charges).
  - **Metric:** the paired net difference, with the role minus without it, per applicable opportunity: one where the
    role's card is consulted.
- **Status:** proposal, owner decides
- **Reason:** Design 13.6 and story F9. One ablation a day bounds the extra plan usage at one shadow session a day
  per AI book. Roles that cannot be separated are only ever judged as their declared bundle.
- **Evidence:** reasoning only

### `role_value_minimum_sample` Role-value minimum sample and rule
- **Value:**
  - **When to judge:** a role or bundle is judged only at a scheduled review, and only with at least 30 applicable
    opportunities on which the two decisions differed.
  - **Interval:** a one-sided 95% interval of the mean paired net difference minus its allocated cost per
    opportunity. It uses the moving-block bootstrap of `uncertainty_criterion`, with blocks of 20 ablation days of
    that role, 10,000 resamples and seed 20261014.
  - **Rule:**
    - a drop is proposed when the interval's upper end is below zero;
    - "earns its cost" is shown when its lower end is above zero;
    - anything else is inconclusive and the role stays.
  - **Owner decides:** nothing is dropped automatically; the owner decides.
- **Status:** proposal, owner decides
- **Reason:** Each role is ablated once every k trading days (k = the number of roles and bundles), so 30 differing
  opportunities may take years for a large role set. This is said plainly so that no early read is mistaken for an
  answer.
- **Evidence:** reasoning only

### `reporting_per_version` Results per protocol version
- **Value:**
  - **When counting starts (the owner's option A, 14 Oct 2026):** version 1 is frozen only once the scoring code of
    S2, S3, F8 and F9 exists, so every scoring rule and its code are hashed before the first counted decision. Every
    decision before that freeze is pilot evidence.
  - **Labelling:** every reported figure carries its protocol version.
  - **Which version:** a decision is counted under the latest protocol version whose freeze record's commit is a
    strict git ancestor of the decision's commit. A decision with no such freeze is not counted, only shown.
  - **No pooling:** versions are never pooled, and results already reported under a version are never recomputed
    under a later one.
  - **Changes:** a change after a freeze is a new version with its own freeze and its own ledger row, and starts its
    own section of every report.
- **Status:** decided by the owner on 2026-10-14
- **Reason:** Story S1, criterion 3: no result can be reinterpreted under rules written after it was seen.
- **Evidence:** reasoning only

### `frozen_files` Files and settings the freeze hashes
- **Value:**
  - **Files:** `research/evaluation/PROTOCOL.md`, `fno/evaluation/protocol.py`, `fno/evaluation/completeness.py`,
    `fno/scorecard/review.py`, `fno/research_engine/statistics.py`, `fno/desk/timetable.py`,
    `research/evaluation/REAL_MONEY_GATE.md`, `fno/evaluation/gate.py`.
  - **Settings:** `config.yaml:desk.timetable`, `config.yaml:scorecard_review`, `config.yaml:risk`,
    `config.yaml:charges`.
  - **Scoring code (the owner's option A, 14 Oct 2026):** the scoring code of S2 and S3 and the code of F8 and F9
    is added to this list before the freeze. Version 1 is not frozen until all of it exists. There is no hashes-only
    version 2.
  - **Refusal:** the freeze tool refuses a listed file that does not exist.
- **Status:** decided by the owner on 2026-10-14
- **Reason:**
  - The owner chose option A: code written after decisions are seen could be shaped by them, so the code is hashed
    with its rules before anything is counted.
  - Hashing settings by section means an unrelated config change does not break the freeze.
  - The real-money gate (story RM1) is frozen with the protocol, so it precedes every counted paper decision (design
    v2 8.3; owner, 15 Oct 2026, RM1 Q10 "Yes, one freeze"; the two gate files were added on 2026-10-15).
- **Evidence:** reasoning only

## Open questions for the owner (raised by judge 85)

1. **A hashes-only version 2** (`frozen_files`, `reporting_per_version`). **Decided by the owner on 14 Oct 2026:
   option A.** Version 1 is frozen only once the S2, S3, F8 and F9 code exists. Book 1 may paper-trade before
   that; those trades are pilot evidence.
2. **Too few blocks for the bootstrap** (`uncertainty_criterion`). **Decided by the owner on 14 Oct 2026: keep 120
   trading days.** That goes against the recommendation of a year plus a t-based check. **Still open:** whether to
   add the t-based lower bound alongside (the block means' mean minus the one-sided 95% t quantile × their standard
   error). The orchestrator has asked the owner.

## Mapping of the provisional terms this protocol replaces

| Provisional term (where) | Today | Protocol item | Proposal |
|---|---|---|---|
| Interval confidence (`scorecard_review.confidence`) | 0.95, two-sided | `strategy_review_rule` | keep |
| Bootstrap resamples (`scorecard_review.bootstrap_resamples`) | 10,000 | `strategy_review_rule`, `uncertainty_criterion` | keep |
| Bootstrap seed (`scorecard_review.bootstrap_seed`) | 20261014 | `strategy_review_rule`, `uncertainty_criterion` | keep |
| Completed positions before any review acts (`UNPROVEN_BELOW_COMPLETED_TRADES`) | 20 | `paper_gate` | keep |
| Months before any review acts (`PAPER_GATE_MONTHS`) | 3 | `paper_gate` | keep |
| Promotion bar (E6's "net profit shown") | interval lower end > 0 | `uncertainty_criterion` | change: the block-bootstrap rule for books and pairs; E6's bar stays for a single strategy |
| `scorecard_review.status` | "provisional until S1" | `frozen_files` | becomes "frozen in evaluation protocol v1" at the freeze |
| Data cutoff (`DESK_DECISION_TIME`) | 15:00 | `timetable` | keep |
| Pack time, retried until (`desk.timetable.pack`, `pack_wait_until`) | 14:58, 15:10 | `timetable` | keep, then calibrate by the measured-run rule |
| Decision deadline (`desk.timetable.decision_deadline`) | 15:12 | `timetable` | keep, then calibrate |
| Execution snapshot (`desk.timetable.execution_snapshot`) | 15:15 | `timetable` | keep, then calibrate |
| Fills by (`desk.timetable.fills_by`) | 15:20 | `timetable` | keep, then calibrate |
| Lock lease (`desk.timetable.lock_lease_seconds`) | 60 s | `timetable` | keep |
| `desk.timetable.status` | "proposed until S1" | `frozen_files` | becomes "frozen in evaluation protocol v1" at the freeze |

## Freezing

1. The owner decides every item.
   - Each status becomes "decided by the owner on <date>".
   - Changed values are edited here, and the measured-run calibration of the timetable is done.
   - Commit.
2. `python -m fno evaluation check --decided` passes.
3. `python -m fno evaluation freeze` writes `research/evaluation/FREEZE_v1.md`: the protocol commit and the SHA-256 of
   every frozen file and setting. It also registers the protocol in `research/ledger.csv` (B4). Commit both.
4. Before any result is computed, S2 and S3 check with `python -m fno evaluation order` that the freeze record's
   commit precedes every book's first counted decision.
