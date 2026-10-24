# Evaluation protocol of the three books (story S1)

Protocol version: 1

**Status: DRAFT, not frozen.** The owner decided five items on 14 Oct 2026 (`uncertainty_criterion`,
`catastrophic_loss_strategy`, `ai_cost_allocation`, `reporting_per_version`, `frozen_files`;
`docs/DESK_DECISIONS.md`) and the rules of story S6's five items on 15 Oct 2026 (their numbers stay proposals). Every
other value is still a proposal. Nothing is counted under this protocol until the
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
  - **Series and claims (story S3):** a book's series holds every session it is observed, each action on its decision
    day as (net, maximum loss), skip-only sessions as (0, 0), up to the last decision day whose actions have all
    closed. "X beats Y" uses the daily difference of one-lot nets on the sessions both are observed. Holm runs on
    one-sided bootstrap p-values (the share of resampled values at or below zero), so a single claim agrees with the
    bootstrap bound, over a fixed family: each book's head-to-head claim and every directional pair (three books: 9
    claims). A member not testable at a look (sample not met, no p-value, or incomplete) enters with p = 1, so
    eligibility never moves the others' thresholds (ChatGPT review 120, response 200).
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
- **Value:** C2's drawdown brake with the owner's 15 Oct 2026 numbers, per book (each Rs 20 lakh book has its own):
  - while closed equity is Rs 1,20,000 or more below its high, the book opens no new trade;
  - only the owner's restart row lifts it;
  - open trades are never closed by the brake.
  - Beside it, limits on new entries only, never a stop: one risk bucket at most Rs 30,000 of maximum loss; all open
    positions' maximum losses at most Rs 1,50,000; new maximum loss opened in one session at most Rs 50,000. There is
    no flat open-trade limit. The figures are `config.yaml:risk`'s books profile, which the freeze hashes.
- **Status:** proposal, owner decides
- **Reason:** The owner's decisions of 15 Oct 2026 (`docs/DESK_DECISIONS.md`: "Risk buckets and caps accepted",
  "Books drop the flat 3 open trades limit", "Risk caps and the drawdown brake apply per book") replace the 12 Oct
  Rs 30,000 brake and 3 open trades, the same for all three books. Repeating them here freezes them for the
  comparison; a test keeps these figures equal to `config.yaml`.
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
  - **When to judge:** a role or bundle (a unit) is judged only at a scheduled review (`review_dates`, coded in
    `fno/evaluation/review_dates.py`), and only with at least 30 applicable opportunities on which the two decisions
    differed (changed opportunities).
  - **Net value per opportunity:** the paired net difference, with the unit minus without it (0 when the two decisions
    agree), minus that day's allocated cost. The cost covers the same dates as the tested net.
  - **Cost, a declared split:** the book's cost for a day is F8's month allocation of its `books_and_roles` shares
    times that day's minutes over the month's minutes, rounded down to the paisa. It is split equally across the units
    consulted that day, the paise left going to the first unit in identifier order. The decider takes no part, so a
    unit's figure is an upper bound, labelled "conservative cost allocation". The mean over every consulted day is
    shown apart as the operating cost. A day without a usage row, or a month without a plan cost, is unknown, never
    zero: no verdict.
  - **Bootstrap:** S3's moving-block resampler on the net values in date order, each with a risk of 1: blocks of 20
    observations (not 20 sessions), 10,000 resamples, seed 20261014. Each block's calendar span and the observations
    per month are printed beside it. The 5th and 95th nearest-rank percentiles are printed only.
  - **Rule:** each unit makes two one-sided claims, "earns its cost" (net value above zero) and "drop" (below zero).
    Holm at 5% runs over a fixed family: both claims of every unit of the role set (2m claims for m units), a unit not
    testable at that review (sample not met, cost unknown) entering at p = 1, so eligibility never loosens another
    unit's threshold (ChatGPT review 124; the same rule as S3's family).
    - a drop is proposed when the drop claim passes; "earns its cost" is shown when that claim passes;
    - anything else is inconclusive and the unit stays.
    - The risk effects (worst month, mean maximum-loss difference) are shown beside the verdict and never decide it
      (owner, 15 Oct 2026: "money only, risk shown").
  - **Provisional:** no role verdict counts as evidence until F9b's card-withholding test passes.
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

### `do_nothing_benchmark` Against doing nothing, after tax (story S6)
- **Value:** Every scoreboard section shows the book's result against a NIFTY 50 index fund and against cash, on the
  same capital, sessions and tax scenario. It is a gate before real money (RM1 reads Book 1's value per strategy
  version) and never the verdict.
  - **View (a), per rupee-day of capital tied** (the gate). Capital tied is each held trade's broker margin plus
    premium paid at entry. Capital tied at the previous session's close earns the fund's change to this close (the
    fund) and the cash rate for the calendar days between (cash). The book's after-tax net per rupee-day is compared
    with each. `beats_index_after_tax` is a point comparison with no interval; it is null when not computable.
  - **View (b), the whole account:** the account's after-tax net plus idle cash (capital minus capital tied) at the
    after-tax cash rate, against the fund and cash on the whole account capital.
  - **Index:** NSE's daily index-close file has no NIFTY 50 total-return row, so the fund's return is the "Nifty 50"
    closing change plus its "Div Yield" / 100 x calendar days / 365, less a 0.05% a year expense pro rata. A missing
    index day makes the comparison not computable; it is never filled.
  - **Cash rate (owner, 16 Oct 2026):** 5.5% a year (set at the freeze). On the S1 freeze date the latest 91-day
    T-bill yield from RBI's published auction result replaces 5.5% here and in `Terms.cash_rate`
    (fno/scoreboard/do_nothing.py, hashed with the scoring code; a test keeps the two equal), with the auction's date
    and source written here, and the marker is removed; the rate is then fixed for the run. While the marker stands,
    `evaluation check --decided` and the freeze refuse this item.
  - **Tax (the owner's scenario, not a tax determination; checked before RM1):** F&O 31.2% on each financial year's
    positive net, no loss carried forward; the fund treated as sold at the section's last session, its gain taxed once
    at 20.8% if the section is under 12 months, else 13% above one Rs 1.25 lakh exemption, a loss untaxed; cash taxed
    at 31.2%. Every simplification leans against the book.
- **Status:** decided by the owner on 2026-10-15
- **Reason:** Owner, 15 Oct 2026: "Shown + real-money gate" (design v2 03:110-120 and 08:83, item 2). The figures are
  the owner's tax scenario, not a verified personal position.
- **Evidence:** some evidence

### `scorecard_measures` Measures beside the headline (story S6)
- **Value:** Shown on every section of both scoreboards, never the verdict:
  - net without the best trade (closed net minus the largest single trade net);
  - the profit factor (sum of winning nets over the absolute sum of losing nets), null with "no losing trade" when
    nothing lost, never infinite, with winner and loser counts and both totals; a trade netting exactly zero is in
    neither;
  - the maximum drawdown and worst day of the daily series (the running high starts at 0), in rupees, with dates, and
    on scoreboard B as a share of the books' drawdown brake; labelled "marked daily, not the brake's closed equity".
  Completed positions only; open trades are counted and left out.
- **Status:** decided by the owner on 2026-10-15
- **Reason:** Owner, 15 Oct 2026: "Yes, add all four" and "Replace": the largest-loss share sits near the Rs 10,000
  cap by design and is unstable near zero gains (judge 138, ChatGPT review 112).
- **Evidence:** reasoning only

### `t_check` t-based check beside the bootstrap (story S6)
- **Value:** A one-sided 95% t bound of net per unit of risk on k whole blocks of 20 sessions counted back from the
  section's last session (the oldest sessions that do not fill a block are left out of this check only, and counted):
  R = the blocks' net / their risk; z_b = (net_b - R x risk_b) / mean(risk_b);
  bound = R - t(0.95, k-1) x sd(z) / sqrt(k),
  with t from a fixed table (1-30 degrees of freedom; above 30 the 30 value). Null below two blocks or with no risk.
  When the t bound and the bootstrap bound fall on different sides of zero, "t-check disagrees: warning" is printed
  beside the claim. It is never a pass condition and never changes whether a claim is allowed.
- **Status:** decided by the owner on 2026-10-15
- **Reason:** Owner, 15 Oct 2026: "Warning, printed". Uncalibrated on about 6 blocks, so it warns instead of deciding.
- **Evidence:** some evidence

### `missed_runs` Missed desk runs (story S6)
- **Value:**
  - **Scoreboard B, as it ran:** each session a book had no collected decision (`missed_decision`), and each session
    with no exit review while a trade was held (`missed_exit_review`), read from E3's run logs and the NSE session
    calendar. The next run reviews every open trade at its own snapshot, dated that day, never backdated.
  - **Scoreboard A, observed decisions only:** a missed decision is not scored and is listed. A book's misses are its
    sessions with no run collected, counted from its first collected run, and its D6-unscored sessions on which another
    book was scored on the same common pack (its own operations fault; review 120, response 200). Above a cap of 10%
    of its eligible sessions (sessions without a snapshot or a common pack, sessions D6 leaves unscored for every book
    and Book 3's sessions before F7 are counted apart), the book's scoreboard A verdict is withheld for operations.
    Exactly 10% is not over the cap.
- **Status:** decided by the owner on 2026-10-15
- **Reason:** Owner, 15 Oct 2026: "A observed, B as it ran". It matches S3 criterion 3; the 10% figure is G9's.
  Decided 15 Oct, refined 16 Oct (owner: "Yes, count it", DESK_DECISIONS row "S3 missed runs: one book's unscored day
  counts as its miss"): a book's own unscored day is its miss.
- **Evidence:** reasoning only

### `random_control` Random-strategy control (story S6)
- **Value:** For each completed position, each of 1,000 runs (one `random.Random(20261014)` stream) draws a twin with
  the same entry and exit sessions, expiry, lots and shape, a random direction (PCS/CCS, CDS/PDS, LC/LP each 50%) and
  a random first strike within 10 strike steps of the at-the-money strike (widened to include the real strike),
  filled by E4's pricing with C1 charges. A draw that is not quotable, breaks the per-trade maximum-loss cap or the
  bucket cap given that run's open twins is redrawn up to 20 times; above 10% of twins missing the percentile is not
  computable. Output: the book's percentile among the runs (ties count half) of closed-trade net per rupee-day of
  risk. Descriptive, never a gate and never in Holm; it controls selection luck (direction and strike), not window
  luck. Numbers (runs, strike window, redraws) are proposals, owner decides.
- **Status:** decided by the owner on 2026-10-15
- **Reason:** Owner, 15 Oct 2026, "Scorecard ... four measures added" (random-strategy percentile); response 144 red
  team 7 and 26.
- **Evidence:** reasoning only

### `frozen_files` Files and settings the freeze hashes
- **Value:**
  - **Files:** `research/evaluation/PROTOCOL.md`, `fno/evaluation/protocol.py`, `fno/evaluation/completeness.py`,
    `fno/scorecard/review.py`, `fno/research_engine/statistics.py`, `fno/desk/timetable.py`,
    `research/evaluation/REAL_MONEY_GATE.md`, `fno/evaluation/gate.py`, and the freezer that applies this list:
    `fno/evaluation/definition.py` (it holds S1's definition, the real-money gate's requirement included),
    `fno/evaluation/freeze.py` and `fno/evaluation/order.py` (story BR1a's follow-up, response 230).
  - **Settings:** `config.yaml:desk.timetable`, `config.yaml:scorecard_review`, `config.yaml:risk`,
    `config.yaml:charges`.
  - **Scoring files (S2, S3 and S6; listed by path, since the freeze hashes only listed paths):**
    `fno/scoreboard/book_board.py`, `fno/scoreboard/book_trades.py`, `fno/scoreboard/committed_runs.py`,
    `fno/scoreboard/daily_values.py`, `fno/scoreboard/do_nothing.py`, `fno/scoreboard/entry_decisions.py`,
    `fno/scoreboard/entry_facts.py`, `fno/scoreboard/matched.py`, `fno/scoreboard/matched_actions.py`,
    `fno/scoreboard/matched_board.py`, `fno/scoreboard/matched_days.py`, `fno/scoreboard/matched_measures.py`,
    `fno/scoreboard/ports.py`, `fno/scoreboard/protocol_status.py`, `fno/scoreboard/random_control.py`,
    `fno/scoreboard/reconcile.py`, `fno/scoreboard/sections.py`, `fno/scoreboard/series.py`,
    `fno/scoreboard/sources.py`, `fno/scoreboard/standard_unit.py`, `fno/scoreboard/t_check.py`,
    `fno/scoreboard/trade_measures.py`, `fno/scoreboard/uncertainty.py`, `fno/scoreboard/whole_system.py`,
    `fno/scoreboard/wiring.py`.
  - **Score-time computation (owner, 16 Oct 2026, "Hash the ~11 modules"; judge 229):** the code the scoring calls
    to compute a scored figure: `fno/desk/pricing.py`, `fno/desk/settlement.py`, `fno/risk/open_risk.py`,
    `fno/risk/trade_costs.py`, `fno/risk/buckets.py`, `fno/contract_symbols.py` (a contract ID's underlying, story
    C5d), `fno/risk/inputs.py`, `fno/research_engine/cycle_costs.py`,
    `fno/research_engine/structures.py`, `fno/accounting/ledgers.py`, `fno/costs.py`, `fno/scorecard/scorecard.py`,
    `fno/scorecard/execution_costs.py`, `fno/scorecard/touches.py`, `fno/books/equity.py`, and the parsers that
    decide which numbers are scored: `fno/fo_bhavcopy.py` (NSE's settlement columns),
    `fno/market_read_models/nse_files.py` (the index closes) and `fno/desk/snapshot.py` (the bid and ask touch;
    judge 229 addendum 1). A test walks the imports
    from the scoring modules through every hashed module: each fno module reached is hashed or exempted with a
    one-line reason (data shapes, readers and stores, wiring). The cost, accepted by the owner: after the freeze, any
    edit to one of these files needs a new S1 version, even when it is made for the desk or the risk manager.
  - **Rules that decide an outcome (judge A, 16 Oct 2026):** `fno/scorecard/pauses.py` (E6's automatic pauses: the
    code of `catastrophic_loss_strategy` and of `immediate_pauses`' strategy rules; a pause decides which trades exist to
    be scored), `fno/playbook/run_order.py` (which run is a day's first decision, read by the freezer's order check
    and E3's collector), `fno/playbook/measurement.py` (which versions are measurements, left out of the stop rule's
    Test B, R1c), `fno/factory/registered_shadows.py` and `fno/factory/gate_log.py` (the shadows Test B counts and the
    factory verdicts they read, R1c), and `fno/budget/stop_rule_tracker.py` (Test B's count itself).
  - **Scoring code (the owner's option A, 14 Oct 2026):** the scoring code of S2, S3 and S6 (S6 added 15 Oct
    2026; listed above: every module of fno/scoreboard but its command line) and the code of F8 and F9
    is added to this list before the freeze. Version 1 is not frozen until all of it exists. There is no hashes-only
    version 2.
  - **Role-value files (F9a; ChatGPT review 124, response 191 point 5):** `fno/role_value/checks.py`,
    `fno/role_value/controls.py`, `fno/role_value/cost.py`, `fno/role_value/records.py`, `fno/role_value/render.py`,
    `fno/role_value/report.py`, `fno/role_value/role_set.py`, `fno/role_value/role_set_file.py`,
    `fno/role_value/rows.py`, `fno/role_value/score.py`, `fno/role_value/valuation.py`, `fno/role_value/verdict.py`,
    `fno/role_value/wiring.py`, `fno/evaluation/review_dates.py`, and F8's allocation that splits the plan cost:
    `fno/budget/allocation.py` (judge 235).
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
   trading days.** That goes against the recommendation of a year plus a t-based check. **Decided on 15 Oct 2026:**
   the t-based bound is added as a printed warning, never a pass condition (item `t_check`).

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
