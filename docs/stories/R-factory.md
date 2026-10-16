# Epic R: the strategy factory (layer 4)

Roles: options strategist, statistician, F&O trader, risk manager, tax and cost accountant. Goal: turn ideas into a
forward record that can be trusted (design v2 `03_layers_factory_desk.md`; `REPLAN_new_stories.md` R1-R3). R1's
documents are in `research/FACTORY_RULES.md`, `research/DATA_SPEND.md` and `research/ideas/TEMPLATE.md`. Story template
and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## R1. The factory's code: idea gates G0-G6, the cost wall, the data spend, the sample plan, the trial count

**Repository:** trading · **REPLAN:** slice B (`docs/design_v2/REPLAN_new_stories.md` l.64-68) · **Lane:** 1 (new
story; registration of trials) · **Owner decision:** "Yes: R1 code + G7 phase 2 now (Recommended)", 16 Oct 2026
(`docs/DESK_DECISIONS.md` row 239).

**Description:** As the owner, I want every strategy idea to pass through the factory's gates by code, not by hand:
written down and counted as a trial from its first line, stopped at the cost wall if it cannot make money after costs
and rare large losses, labelled exploratory when its data is already used, given an honest sample size and time, and
judged once, with every report saying how many trials came before it. Then a passed idea is evidence, not luck found by
trying many things.

**Context and why (strong evidence: `main` read on 16 Oct 2026, unless marked):**
- **The rules exist as text only.** `research/FACTORY_RULES.md` (gates G0-G6, the G1 cost wall, `exploratory_shadow`,
  the cumulative Holm family per research question, "trial k of K"), `research/DATA_SPEND.md` (one row per data set:
  `fresh`, `exposed`, `spent`, `forward`, `registered`) and `research/ideas/TEMPLATE.md` (the idea card). None of the
  gates is in code: no `screened_out`, `thin margin`, `exploratory_shadow`, sample plan or "trial k of K" in any `.py`
  file. The three cards so far (`research/ideas/R2.md`, `FT1.md`, `B0.md`, trials 53-55) were screened by hand.
- **The trial record exists and is guarded (story B4).** `research/ledger.csv` (55 rows; columns `trial_id,
  experiment, description, kind, hypothesis, registered_on, protocol_path, protocol_commit, first_run_on, run_commit`)
  through `fno/research_engine/ledger.py`: `Ledger.register` (one new row, no duplicate id), `require_committed`,
  `require_registered` (frozen protocol commit, unchanged file), `mark_run`, `count`. `read_ledger` refuses any column
  other than these ten, so a status column would change B4's guard and every writer (`fno/evaluation/freeze.py`, two
  study packages). The status lives today in free text in `research/LEDGER.md` (which says 54 trials, one behind the
  55 rows: the hand-kept count already drifts).
- **What R1 can reuse (DRY):** C1's charges (`fno/costs.py` `order_charges`, `settlement_charges`, the config rates);
  measured half-spreads (`fno/quotes/report.py`, A4; A16's 15-minute quotes); Holm's step-down
  (`fno/scoreboard/uncertainty.py` `holm`, a plain list in, verdicts out); D1's playbook statuses and transitions
  (`fno/playbook/transitions.py`, `research` = shadowed).
- **Who else is involved.** R3 (owner 0145TfSwzmpk6MBrH92f5h4G) runs the shadows: accounts, books, B0, part B's fills.
  R-factory.md R3 says R1 owns `CostWall`, `IdeaCard`, `SamplePlan` and `fno/factory/`, and that R3 applies the cost
  wall by hand until then. The budget's stop-rule tracker expects from R1 "shadow strategies registered in the ledger
  with pass mark and minimum useful net" (`fno/budget/stop_rule_tracker.py` l.49). S1's `freeze.py` registers
  protocols in the same ledger; BR1a uses it too. R1 changes none of these.

**Scope.**
- In: the gate code G0-G4 and G6's verdict arithmetic for registered ideas and shadows, the gate log, the trial count,
  the research-question families, the commands, and `FACTORY_RULES.md`'s one sentence about the status field
  (below).
- Out: running tests or shadows (G5: B4's experiments, R3's shadows, S1's protocols do that); opening shadow accounts
  (R3); changing the ledger's columns (B4); any strategy rule; promotion to paper (D1, the owner); the dashboard
  (paused, row 238).

**Expected design.**
- **Package `fno/factory/`**, wired only in a new `fno/factory/wiring.py`.
- **`IdeaCard`** (data class) from `research/ideas/<id>.md`: the card keeps its human tables, plus one fenced
  ` ```factory ` YAML block with the gate inputs as numbers. Fields:
  - id, trial id, research question id;
  - frequency per year;
  - gross: bound in rupees per trade and its source kind (`measured` with mean, SD and n; `published` least
    favourable value; `arithmetic` least favourable input), and the source text;
  - tail: the probability and size of the maximum loss;
  - legs: side, lots, entry premium, exit premium or settlement, and the half-spread pad per leg with its measurement
    path;
  - data sets read (DATA_SPEND rows) and the quantity measured;
  - SD per trade for the plan, and the one-sided level of its pass mark.
  - `TEMPLATE.md` gains the block (lane 1). A card without a valid block fails G0 with the field named.
- **G0 registration:** `fno factory register <id>` validates the card, then writes the ledger row through B4's
  `Ledger.register` (kind `prospective`, hypothesis `yes`), and the first gate-log row (`idea`). The card and both
  rows are committed together (the command prints the files to commit and checks nothing else is staged).
- **The gate log, instead of a status column** (reasoning only: B4's ten columns stay frozen and every writer keeps
  working). `research/factory/gates.csv`, append-only: `trial_id, gate, outcome, on, commit, numbers` (`numbers` is a
  short `k=v;k=v` text of the gate's figures, never a market value of a test's outcomes). A guard (same pattern as
  B4's) refuses an edit or deletion of an existing row. An idea's status is its last row. `FACTORY_RULES.md` section
  1's sentence "Until R1's code adds a status field to `research/ledger.csv`" becomes "R1's gate log
  (`research/factory/gates.csv`)" (lane 1, this story).
- **`CostWall` (G1, strategy pattern over the source kind):**
  - The conservative bound: measured = the lower one-sided 90% bound of the mean (Student t, n - 1: the quantile
    inverts the existing `fno/forecast_v4/student_t.py` `t_cdf` by bisection, since scipy is not installed; no third t
    table beside `fno/scoreboard/t_check.py`'s 95% one); published = the
    least favourable value; arithmetic = the stated least favourable input.
  - Round-trip cost = C1's charges for every leg in and out (or settlement) at the screen date's config rates, plus
    the measured pads.
  - Tail = the worse of the card's figure and a measured family rate where the card cites one.
  - Expected net = bound - cost - tail loss beyond the gross. Above zero passes; at or below zero writes
    `screened_out` with the numbers. The 2x ratio is printed as `thin margin` only, never a reason.
  - "no stated edge" when the card has no source. The cost-hurdle study (judge 97) is labelled `assumed hurdle` and
    never logs a G1 pass for an idea.
- **`DataSpendRegister` (G2):** reads `research/DATA_SPEND.md`'s table. Any data set `spent` or `exposed` for the
  measured quantity gives `exploratory` (cannot pass G6); all `fresh` or `forward` gives `fresh`. It names the rows it
  read. Updating the register's rows stays a hand edit in the same commit (the rule of the file); R1 checks it.
- **`SamplePlan` (G3):** n = (z x SD / expected net)^2, with z from the card's one-sided pass level and the expected
  net from G1. Time = n / frequency. Above 3 years: logged `exploratory_shadow` only (rule section 3).
- **G4:** `fno factory freeze <id>` uses B4's `require_registered` (frozen protocol commit, unchanged file) and logs
  `registered` with the frozen sample and pass mark. A shadow then goes to D1's `research` status by the owner's
  existing `playbook set-status`; R1 never opens an account.
- **Research questions and the cumulative Holm family:** `research/factory/questions.csv` (id, plain question,
  alpha), append-only. G6 for a shadow: p-values of every shadow ever registered on the question. A shadow stopped,
  retired or short of its frozen sample enters with p = 1. Holm via `uncertainty.holm`. A verdict is logged once and
  never relabelled. The shadow's results come through a `ShadowResults` port. Its adapter reads R3's records, as
  agreed with R3's owner (16 Oct 2026):
  - decisions: `DecisionStore(root, BOOK1_RULES)`, records with `mode: "shadow"` only (filtered by mode, never by file
    name);
  - nets: E6's `strategy_records(account, DeskRecords(PaperAccount(root, account)), charges)` `.closed[i].line.net`
    for account `shadow:<name>-v<n>`, read only after E2c's `download_private_records`, since the accounts are Drive
    only;
  - no CSV is parsed by R1.
- **B0 and every measurement version** (`fno.playbook.measurement.is_measurement`) count in "trial k of K" but never
  enter a family's Holm, the expected false passes or `RegisteredShadows`. If R1's Holm is the first code to decide a
  figure with `is_measurement`, `measurement.py` moves from S1's exempt list into the frozen files in the same change
  (judge A's condition, through R3's owner).
- **The trial count:** `fno factory report` prints, for every idea, "trial k of K" (K = the ledger's rows) and the
  expected false passes at the pass level (K x alpha), plus each idea's last gate. Reports by other stories call the
  same `TrialCount`.
- **For the budget's stop rule:** `RegisteredShadows` lists shadows registered in the ledger with their pass mark and
  minimum useful net, for `stop_rule_tracker` l.48-49. R3 part B provides the resolved closed trades (its criterion
  12), and the stop rule's `money_test` joins the two. R1 never reads closed trades for Test B.
- **R3's hand step goes in the same change that merges `CostWall` (R1b).** Step 1 of R3's registration procedure
  ("the cost wall worked by hand", R-factory.md R3 scope) becomes a call to `CostWall`, keeping B0's `measurement`
  exception. That way the hand step and the code never both apply (agreed with R3's owner, who does not edit that
  step meanwhile).

**Staged rounds (each judged before the next; judge G):**
- **R1a: records.** `IdeaCard` and its block, G0 registration, the gate log and its guard, `TrialCount`, `fno factory
  register | status | report`, `TEMPLATE.md`'s block and `FACTORY_RULES.md`'s sentence. The three existing cards get
  their blocks and back-filled `idea` rows dated by their ledger rows (labelled back-filled). Size M.
- **R1b: the screens.** `CostWall`, `DataSpendRegister`, `SamplePlan`, `fno factory screen | spend | plan`, and R3's
  step 1 rewritten to call `CostWall`. The three existing cards are re-screened by code and compared with their hand
  screens; any difference is reported, never silently replaced. Size M.
- **R1c: shadows and families.** `questions.csv`, `freeze`, the `ShadowResults` port and its R3 adapter, the
  cumulative Holm verdict, `RegisteredShadows`. Size M.

**Acceptance criteria.**
1. A card with a valid block is registered by one command; the ledger row (through B4) and the gate log's `idea` row
   are written; a card with a missing or malformed field is refused with the field named, and nothing is written.
2. The gate log's guard refuses any edit or deletion of an existing row (a planted edit fails the test).
3. "Trial k of K" equals the ledger's row count and order; expected false passes = K x alpha.
4. `CostWall` reproduces `FACTORY_RULES.md`'s worked example from its source (response 92, l.39-40: the monthly
   condor, n 33, mean gross +978, SD 2,667, cost Rs 824; n 57, +408, SD 3,403, Rs 814).
   - On the means, the nets are +154 and -406. Response 92 prints +153 from unrounded means; the test uses the rounded
     inputs.
   - On the conservative bound (lower one-sided 90%, t 1.3086 and 1.2969), the bounds are +370.5 and -176.5 and the
     nets are -453.5 and -990.5 (checked with `fno/forecast_v4/student_t.py`), so both are `screened_out`.
   - Both carry `thin margin` (ratios 1.19 and 0.50).
5. A card with no gross source is `screened_out` with "no stated edge"; a cost-hurdle study never logs a G1 pass.
6. A test reading a `spent` or `exposed` data set for its measured quantity is `exploratory`, with the rows named.
7. `SamplePlan` gives n and the time; above 3 years it logs `exploratory_shadow` only.
8. Holm across a question's whole family (planted: 20 shadows, 19 stopped at p = 1, one at p = 0.004 with alpha 5%)
   never passes the survivor alone; the family is recomputed at each verdict, and earlier verdicts are unchanged.
9. R3's, B4's, S1's and D1's files and behaviour are unchanged (their tests pass untouched), except R3's step 1 in
   R1b and, if R1c triggers it, `measurement.py` into the frozen files.
10. A measurement version (B0) counts in "trial k of K" and never in a Holm family, the expected false passes or
    `RegisteredShadows` (a planted measurement shadow at p = 0.001 does not pass anything).

**Test plan.** Unit tests per gate with fixed inputs (the worked example, planted families); a guard test with a
planted edit; an end-to-end test on a temporary repository: register, screen, plan, freeze, report; the three real
cards re-screened (R1b) with their figures printed beside the hand screens.

**Judge verifies (judge G).** Re-runs the worked example and the planted Holm family; plants an edit in the gate log;
registers a card with a missing field; checks that no ledger column changed and that R3's files are untouched; compares
the code's re-screen of R2, FT1 and B0 with their cards.

**Settled (orchestrator, 16 Oct 2026, reasoning only):**
- The gate log stays in the repository, like `ledger.csv`.
- z for the sample plan is each idea's registered one-sided pass level.
- `FACTORY_RULES.md`'s worked example gets the corrected figures of criterion 4, as a dated correction, in this
  change.

**Depends:** B4 (done), C1 (done), D1 (done), A4 (done); R3 for R1c's adapter. **Size:** L in total (three M rounds).
**Known limits (R1c, agreed with R3's owner, 16 Oct 2026):**
- A counterexample study (`FACTORY_RULES.md` section 3, rule 2) is frozen by hand until a real one exists: `fno
  factory freeze` refuses any idea whose last gate is not G3, so a `screened_out` idea is never frozen by code.
- The verdict's p uses completed positions only. A "shadow: would trade" decision that is never filled (missed, no
  card, price cap) is not a position, so clustered misses would bias the sample. The miss share is printed as "not
  reported" until E6b's missed-execution counter is merged; then it is read from there (one counter, not two). R1c
  therefore reads no decision records.
- Until E8 part 1b and R3 part B merge, every shadow has zero positions: no verdict is given and the stop rule's Test B
  stays undecided.

**Status:** R1a done (judge 261 PASS, 29a0707a); R1b done (judge 266 addendum 1 PASS, 9a20155a); R1c (shadows and
families) with judge G.

---

## R3. First forward shadows

**Repository:** trading · **Issue:** #124 · **REPLAN:** slice B · **Lane:** 1 (new story; fills and records)

**Description:** As the owner, I want the first registered ideas recorded every session as shadows: decided by their
own frozen rules at the day's real quotes, filled as I could have filled them, never in a book. Then a strategy can
earn rung 2 ("shadow", design 01) on a forward record, which is the road to an approved strategy and to the AI books.

**Context and why (strong evidence: code on `main` read on 16 Oct 2026, unless marked):**
- **The decision half exists.**
  - A playbook version registered with status `research` is shadowed from the next day (`Playbook.shadow_on`,
    `fno/playbook/loader.py`).
  - Book 1's D2 run evaluates each shadow alone in its own book, and records "shadow: would trade" or "no trade" with
    `mode: shadow` under `journal/book1_rules/decisions/<d>/` (`fno/playbook/evaluate.py`, `decision_run.py`).
  - This is the owner's "experiment 2" (decision of 14 Oct 2026, option a, `docs/DESK_DECISIONS.md`). Its paper
    result was meant to use the desk's fills and costs.
- **The money half does not exist:**
  - nothing fills a "shadow: would trade" decision (the desk's fill step and Book 1's orders read the three books'
    chosen outcomes only: `fno/desk/daily_steps.py` `fill`, `fno/books/book1_orders.py`);
  - nothing opens the shadow accounts. `start_shadow_books` (`fno/desk/wiring.py`) is called only by a test, so the
    first registered candidate makes Book 1's run raise (`JournalShadowBooks.account`: "has not been started");
  - the shadow books get Book 1's recorded terms, not each shadow's own (`fno/books/book1_wiring.py` `_parts`). That
    is a second crash path: once a shadow holds an open trade, `fno/risk/book_view.py` `_open_trade` raises
    `RiskInputError` ("open trade ... has no recorded terms"), because that trade's terms are not in Book 1's
    (judge 208 note; the error is `RiskInputError`, not `KeyError`);
  - **Book 1's readers do not filter shadows.** The shadow decision records sit in Book 1's own decision folder
    (`journal/book1_rules/decisions/<d>/`), and a "shadow: would trade" record has `chosen_action: trade`. Book 1's
    `_chosen` (`fno/books/book1_records.py`) checks only `chosen_action` and the structure, never `mode`. Today no
    shadow record enters Book 1's trades, only because they key on Book 1's own fills (`opening_runs`) and shadow trade
    ids carry the `shadow-` prefix. The isolation rests on that prefix alone (judge 208).
- **No idea passes the cost wall today:**
  - desk meeting 2 found zero candidates with an edge after costs (`reviews/claude/response_92_...`, strong evidence:
    Rs 814-939 per four-leg round trip against the premium);
  - weekly weather W1-W5 all failed;
  - R2 (stock options) stopped at the cost wall;
  - the only item response 92 offered is **B0, a monthly short condor benchmark shadow, "labelled as a measurement and
    not a candidate"**.
- **The V-ideas are blocked** (design 03, first queue; A16/G8/G10 builder, 16 Oct):
  - **V1** (sell protected premium when the volatility forecast is well below implied):
    - G7's `v1_close_blend` gives `not_started` until A16 has 20 live non-void sessions (first live session 16 Oct;
      earliest about mid-November, some evidence);
    - V1 is a next-session variance, so "below implied" needs a frozen units rule against the pack's IV30, which
      exists only after G10 part 2;
    - the playbook vocabulary has no v4 forecast feature (`fno/playbook/vocabulary.py`: F1-F3 only).
  - **V2** (buy protected movement): its forecasters are G7 phase 2 (not built); its debit spreads need STR1b-2 (not
    started; only SF, SC and BF are usable today, `fno/playbook/activation.py`); the same feature gap applies.
- So R3 delivers the money half now, so that any shadow can run, and a registration procedure. Its first shadow is
  B0, the measurement the owner chose (decision 1 A). Nothing is invented to fill the queue.

**Scope.** In:
- **Shadow accounts opened at registration time.** The step that runs Book 1's decision opens every research version's
  shadow account once, before D2 evaluates it (`start_shadow_books`, existing code, unchanged), so a registered shadow
  never breaks Book 1's run. Opening an account writes only `journal/shadow/<name>-v<n>/account/` (Drive-kept, E2c).
- **Each shadow's own terms:** the shadow books are built from each shadow account's own filled trades (structure,
  width, lots), never from Book 1's.
- **Book 1 isolation:** every Book 1 reader of the shared decision folder skips records with `mode: shadow`:
  - E5's opening trades, recorded terms and decided exits (`fno/books/book1_records.py`);
  - E5's one-decision-a-day finder.
  A shadow's own readers take only `mode: shadow` records of that version. The decision records stay where D2 writes
  them (D2 is unchanged). A shadow's orders, fills and account live only under `journal/shadow/<name>-v<n>/`, never
  under `journal/book1_rules/`.
- **Shadow fills and exits, through the desk's one fill path:** a "shadow: would trade" decision is filled into its
  shadow account exactly as a book's entry, and its exits run as a book's:
  - E8's owner-timing rule (`docs/stories/E8-owner-timing-fills.md`): order time T = that day's card delivery time,
    the same T as the books (a shadow models the owner acting on the day's card), the verdict view at R = 60, the
    price cap, and the funds re-check;
  - no card delivered: "missed, card not delivered", as for the books;
  - costs from C1 (`config.yaml` `charges`), the same as the books;
  - **the contract with E8 (agreed, below):**
    - R3 writes each "shadow: would trade" decision as a pending order in the shadow account's own journal
      (`journal/shadow/<name>-v<n>/`), in exactly the order format Book 1's orders use, with the account id
      `shadow:<name>-v<n>`;
    - E8 fills every pending order whatever its account, through the same code as a book's, so no separate shadow
      fill step exists;
    - R3 fills E8's one terms lookup (funds, limits, charges), keyed by account, for each shadow, as Book 1's wiring
      does for Book 1. The fill-day funds and risk re-check runs on the shadow's own terms. It is a check only,
      never a decision counted by E6, S1 or S2;
    - E8 never creates an account. A pending order for an account that does not exist fails loudly, so R3's opening
      step must run first;
  - until E8's part 1b is merged, nothing fills a shadow (no second, earlier fill rule is built).
- **The registration procedure** (written in this story; steps 1 and 2 run by R1's code since R1b):
  1. an idea card from `research/ideas/TEMPLATE.md` with its `factory` block, screened by R1's `CostWall` with
     `python -m fno factory screen <id>` once its registration is committed (`FACTORY_RULES.md` section 2: expected net
     after costs and tail losses above zero on the conservative bound), or the label `measurement` (B0 only), which
     is registered but never screened;
  2. a ledger row first, written with the card's `idea` row by `python -m fno factory register <id>`
     (`research/ledger.csv` via B4's guard; the trial count includes screened-out ideas);
  3. the frozen playbook version (SF, SC or BF only until STR1b-2), registered `research` with
     `python -m fno playbook set-status` (owner or desk, `fno/playbook/transitions.py`), only for a card whose G1
     screen passed (`python -m fno factory status <id>`), or a measurement. A `screened_out` idea gets no research
     version, so no shadow account, unless a registered counterexample study shadows it (`FACTORY_RULES.md` section
     3, rule 2). R1b's code does not enforce this at `set-status` (D1's command); the owner or desk checks the status;
  4. a measurement shadow's card and ledger row say "never promoted". Approving it to paper needs the owner's own
     decision, which this label does not grant.
- **Results:** the shadow accounts' closed trades, net after costs, feed:
  - E6's existing scorecard shadow section (evidence only; alerts, never pauses; `fno/scorecard/report.py`,
    `pauses.py`, unchanged);
  - the stop-rule tracker's Test B input "R3: resolved shadow trades, net after costs" (`fno/budget/stop_rule_tracker.py`,
    `path=None` today). R3 sets its path to the closed-trades file and tells BG1's owner.
- **With B0 as the only shadow, the stop rule's Test B stays "undecided" for years:** about 12 trades a year, and a
  measurement is not an economic test of an idea (`fno/forecast_v4/stop_rule.py`).
- **B0's registration (owner, decision 1 A), counted in the trial total:** experiment 1's P1 rule (SC every monthly opportunity),
  its card labelled `measurement`, never promoted (ChatGPT review 129, accepted):
  - every output that shows B0 (E6's scorecard, the stop-rule tracker, the post-mortem) carries the label
    `measurement`;
  - B0 is excluded from G6 promotion and from every count of positive candidates.
  Response 92's stop ("a single loss above Rs 10,000"):
  - **prevented by code:** D2 evaluates each shadow with C2's rules on its own book, so C2's per-trade cap
    (`max_loss_per_trade`, `fno/risk/rules.py`) refuses any B0 trade whose maximum loss with costs exceeds the cap.
    A defined-risk condor cannot lose more than its maximum loss, except through a settlement or data error;
  - **if it happens anyway:** E6 alerts #fno-desk on the day the trade closes (a research shadow is alerted, never
    paused: `fno/scorecard/pauses.py`). For B0 the alert reads: "B0 measurement: realised loss over Rs 10,000; owner
    review or retirement required; no further promotion. B0 stays eligible for further hypothetical entries until
    the owner acts" (review 129). A second such loss is escalated in the same alert as a possible simulator defect
    (fill or settlement path), to be checked before any strategy relies on that path. Retiring B0 is the owner's
    action (`playbook set-status ... retired`; only the owner may retire, `fno/playbook/transitions.py`). Judge 208
    asked who stops it: the owner, on E6's alert. Code cannot pause a research version (design 12.8). The alert's
    wording is built with B0's registration (one message constant in E6's pause alerts).

Out (each with where it goes):
- **V1 and V2 shadows:** later R3 work, when their blockers clear: A16's 20 sessions and G10 part 2 for V1; G7 phase 2
  and STR1b-2 for V2. A v4 forecast feature in the playbook is R3's to build then (the A16/G8/G10 builder agrees;
  playbook is D1's function). It reads through G8's `V4ForecastSource.values`, wrapped in `LateDaysOut`, live rows of
  the decision day only (final at the 14:30 cutoff).
- **R1's code** (`CostWall`, `IdeaCard`, `SamplePlan`, `fno/factory/`): R1. R3 applied the cost wall by hand until R1b;
  since R1b, step 1 calls `CostWall` (`fno factory screen`).
- **S6's measures on shadow accounts:** a separate small story, if the owner wants it (S6 builder: S3 and S6 read no
  shadow account today).
- **Promotion to paper:** the owner (rung 3, S1).

**Design:**
- No new fill or exit code: E8 fills pending orders of any account (E8 builder's code, part 1b). R3 adds only:
  - the shadow orders, written by Book 1's existing order writer for the shadow outcomes;
  - the per-account terms entries for E8's lookup (its interface name comes with E8's part 1b; reasoning only until
    then).
- The account-opening call and the per-shadow terms: one change each in Book 1's run wiring (`fno/books/book1_wiring.py`,
  E5's root; agreed with its owner at code time).
- The Test B path: one constant.
- Every file under 350 lines.

**Acceptance criteria:**
1. A version registered `research` on day d gets its shadow account opened before D2's first evaluation of it; Book
   1's run never raises for an unopened shadow. A second run opens nothing.
2. Each shadow's book holds only its own trades' terms; Book 1's terms never reach a shadow (a test with one open
   trade in each).
3. A "shadow: would trade" decision becomes one pending order with account `shadow:<name>-v<n>`, in Book 1's order
   format. E8 fills it into that shadow account only, by E8's rule: T = the day's card delivery time from the card
   record, the R = 60 verdict with r5, r30 and e4_1515 beside it, the price cap, and the funds re-check on the
   shadow's own terms. "No trade" writes no order. No card gives "missed, card not delivered".
4. Each shadow's entry in E8's terms lookup is the shadow's own; a test plants different book and shadow terms and
   checks that neither reaches the other.
5. A shadow's exits run by the same exit rules as a book's, and its costs come from C1.
6. Nothing fills a shadow before E8's code is merged (no other fill rule exists).
7. The stop-rule tracker's Test B path points at the shadow accounts' closed trades; zero shadows still give
   "undecided" (`fno/forecast_v4/stop_rule.py`).
8. A measurement shadow's idea card, ledger row and registry evidence say `measurement: never promoted`. Every
   output showing it carries `measurement`, it is never counted as a positive candidate or promoted at G6, and its
   E6 loss alert has review 129's wording, with the repeat escalation.
9. Book 1's scoring is isolated: with one Book 1 trade and one shadow trade on the same day, each of these returns
   exactly what it returns with the shadow absent:
   - E5's trade counts and its one-decision-a-day rule;
   - E5's opening trades and recorded terms;
   - E6's Book 1 scorecard section;
   - S2's Book 1 board;
   - S3's Book 1 actions.
   Nothing in R3 changes a book's account, decision or fill.

**Test plan:** fakes for the registry, the shadow accounts, E8's fill rule and the clock.
1. Positive: registration on d, account opened, one "would trade" filled, then exited and closed.
2. Negative: an unopened shadow (opened, never raised); Book 1's terms kept out; "no trade" filled nothing.
3. Empty: no research version (nothing opened, Test B "undecided").
4. Isolation (criterion 9): one Book 1 trade and one shadow trade on the same day. Each listed Book 1 reader is run
   with and without the shadow's record and account, and the results must be equal. A planted reader that ignores
   `mode` fails the test.

**Known limits:**
- Until a strategy is registered, R3 changes nothing a day records.
- A monthly rule makes about 12 trades a year. A forward shadow of it can expose a disaster but never confirm an edge
  within S1's horizon (response 92: about 100-165 years for 2 standard errors). B0 is a measurement for that reason.
- Shadows wait for E8's code; E8's own code waits for E2c and E4c (work register).

**Split with other builders (16 Oct 2026):**
- **S3/S6 (R2/G7) builder, session 0185gR5DmoDh2zBAvgRU4CEB:** Test B's path is R3's (BG1's tracker; tell BG1's
  owner). S3 and S6 read no shadow account and need nothing from R3. S3's "shadow" is F7's matched decisions, a
  different thing.
- **A16/G8/G10 builder, session 01VK88LxJvV1Gi7Wbr3D4fzp:** the V-idea blockers above are confirmed. A future v4
  feature reads through `V4ForecastSource`, wrapped in `LateDaysOut`, and R3 builds it behind `FeatureEntry`. They
  will warn R3 before changing that interface.
- **E8 builder, session 01H1CmuWzBtbtjzoQNJUz2Dz: agreed, 16 Oct 2026.**
  - A shadow's T is the day's card delivery time, taken from the card record; the verdict is R = 60, with r5, r30
    and e4_1515 reported.
  - E8 owns all fills through one path: it fills pending orders of any account.
  - R3 writes the shadow orders in Book 1's format, fills E8's per-account terms lookup, and opens the accounts. E8
    never creates one, and an order for a missing account fails loudly.
  - The interface names are reasoning only until E8's part 1b (which waits for O1's merge). E8 notes cite R3.

**Owner's decisions (16 Oct 2026, decision row on `main`, relayed by the orchestrator): 1 A and 2 A.** The questions as asked:
1. **Register B0 now?** (A) Yes: the monthly short condor, P1, labelled `measurement: never promoted`. It is the only
   way to exercise the whole shadow path (fills, exits, costs at real quotes) before V1 or V2 can start, and it
   measures real premium and costs (response 92). Cost: one trial counted, and a monthly rule gives about 12 trades a
   year. (B) No: register nothing until V1 or V2 clears its blockers. **Recommendation: A** (some evidence on cost
   measurement, reasoning only on the value of exercising the path).
2. **Build order:** (A) the account opening and the per-shadow terms now (small, and needed before any registration),
   with fills when E8's code merges; (B) everything after E8. **Recommendation: A** (reasoning only: the crash on the
   first registration is real today).

**Build order (decision 2 A):** the account opening, the per-shadow terms and the Test B path are built now (criteria 1, 2,
6-9); B0 is registered after they merge. Shadow orders and fills (criteria 3-5) are built when E8's part 1b merges.

**Depends:** D1, D2, E3, E5 (Book 1's run), E8 (fills), E6 (scorecard), BG1 (stop-rule tracker), STR1b-2 and G7/A16/G10
for the V-ideas · **Size:** M · **Status:** text PASS (judge 208 add. 1); part A merged (0d796a1c, judge 210 add. 2, ChatGPT 132 / response 229);
B0's registration and part B: text below, waiting for the judge

### R3 addendum (16 Oct 2026): B0's registration and part B

**Why:** part A is merged. The build order puts B0's registration next, then part B (shadow orders and fills) when
E8's part 1b merges. ChatGPT review 132, accepted in response 229, adds three conditions to part B; the orchestrator
requires them in this text.

**B0's registration (built now, criterion 8):**
- **Files** (desk registration: `(None, research)` is allowed for the desk, `fno/playbook/transitions.py`; the owner
  chose it, decision 1 A):
  - `research/ideas/B0.md`, from `TEMPLATE.md`;
  - a ledger row through B4's guard (`prospective`, hypothesis `no`, description starting "B0 measurement: never
    promoted");
  - `playbook/b0-monthly-sc-v1.yaml`: experiment 1's P1 rule exactly, which is response 92's B0 row (SC, spot x
    1.02 / x 0.98, widest of 300/250/200/150/100 within the Rs 10,000 cap, every monthly cycle 30-45 days out, exit at
    the last 15:00 with 21+ days left, `entry_conditions: []`, `catastrophic_loss_rs: 10000`). P1 and D2 centre on spot;
    response 92 wrote "forward" (judge 233 note 1);
  - its registry row (`research`, `approved_by: desk`) by `python -m fno playbook set-status`.
- **The label's one source:** the version file's `edge_family: measurement` (an existing D1 field, no schema change).
  One predicate, `is_measurement(strategy)`, reads it, and every output below calls it. Its constant is named at the top of the predicate's
  module, `fno/playbook/measurement.py` (`fno/constants.py` is at its size limit).
- **Outputs (code):**
  - E6's shadow section shows `<version> (measurement)`;
  - E6's single-trade alert (a closed trade's net at or below -`catastrophic_loss_rs`, E6's `<=`) for a measurement
    uses review 129's wording as one message constant in `pauses.py`, with "Rs 10,000 or more" in place of "over
    Rs 10,000" to match that `<=`;
  - from its second such loss, the alert adds the escalation "possible simulator defect (fill or settlement path):
    check it before any strategy relies on that path". The count comes from the version's closed trades at or beyond
    its cap, read from its own account;
  - **E6's cumulative alert** (a research shadow's realised net at or below -3 x its cap, Rs -30,000 for B0, on each day
    one of its trades closes; `cumulative_losses`) will fire for B0 in normal running. P1 ended 2019-23 at -34,486
    (-23,140 without the stale closes), with a maximum drawdown of 40,607 (judge 226). For a measurement it reads:
    "{version} (measurement) shadow test, not paused: cumulative loss Rs ... (3 x cap Rs ...); expected for a
    measurement (no edge), not a defect; the owner decides". It is one message constant beside the single-trade one;
  - **the repeat stays:** it fires on each close day while the total is at or below the line. That is about once a
    month for B0, which is the owner's monthly reminder of the measurement's running cost, so it is not noise (reasoning
    only). Changing E6's repeat rule would also change it for non-measurement shadows, which R3 does not touch;
  - E6 sends at most one alert per version a day (`AutoPauser.apply`), and it lists the single-trade triggers before
    the cumulative ones (`fno/scorecard/run.py`). So on a day both fire, B0's single-trade wording is sent.
- **Not counted:** at Test B's integration (condition 3 below), a measurement shadow is listed, never counted.
- **What B0 is, honestly** (strong evidence, `research/2026-10-12-experiment-1/RESULTS.md` and response 92):
  - over 2019-23, P1 lost Rs 34,486 over 60 opportunities, or Rs 23,140 without the 7 impossible stale-close exits
    (`RESULTS.md`: impossible exits);
  - its worst trade was -11,346, over the cap, on a stale close; the clean worst was -8,937;
  - funds at entry are about Rs 1,00,784 a lot.
  B0 measures premium, costs and the fill path at real quotes. It can never show an edge.

**Part B (built when E8's part 1b merges): criteria 3-5 above, plus:**

10. **With/without isolation after real shadow orders and fills** (review 132, point 1). One session holds a Book 1
    trade and a shadow trade, both filled by E8's real path. Each of these is run with and without the shadow's
    orders, fills and account, and must be identical:
    - C2's risk view of Book 1;
    - C4's recorded pass for Book 1's order;
    - E6's Book 1 section;
    - S2's Book 1 board;
    - S3's Book 1 actions;
    - Book 1's ledger files (`journal/book1_rules/account/`), byte for byte.
    This test gates part B's merge.
11. **Mode-aware order readers** (review 132, point 3). Before any shadow order is written, `book1_orders._stored_action`
    and `recorded_c4` take an explicit mode and account, and look records up by `record_file(id, mode)`.
    - Test: a book record and a shadow record with the same ID; each reader takes only its own.
    - A missing shadow record fails closed (no order, or C4 "no D3 record"), never falling back to Book 1's file.
12. **Test B readiness** (review 132, point 4).
    - At Test B's integration, R3's input is ready only when resolved shadow closed-trade records are read after E2c's
      download, and checked against the registered trial requirements (R1's pass mark and minimum useful net), never
      when a folder exists (`StopRuleInput.exists`, `stop_rule_tracker.py:41`, is replaced for R3 by a reader of
      closed trades).
    - Zero resolved, counted shadows stays `undecided / no_economic_test`, never NO. Measurement shadows are never
      counted.
    - A review run before the download reports "data not loaded".

**Tests (added to the plan):**
- 5. B0's version file parses, is registered `research`, and is shadowed the next session.
- 6. `is_measurement` is true for B0 and false for the worked example.
- 7. E6 alert wording for B0's first and second single-trade loss, including a loss of exactly the cap (E6's `<=`),
  and for B0's cumulative loss on a close day; a day with both sends the single-trade wording. A non-measurement
  shadow keeps E6's current wording for both alerts (unchanged bytes).
- 8. Conditions 10-12 as stated.

**Known limits:**
- No G6 promotion code exists yet (R1/S1). B0's exclusion from G6 and from positive-candidate counts is held by the
  label, the card and the ledger row until that code reads `is_measurement`.
- The post-mortem (LR1) shows no strategy lines today, so it has nothing to label.
- Until part B, B0 is decided and recorded daily but never filled: its account stays at its opening cash.
- **A realised B0 loss can still pass Rs 10,000** (code read: `fno/risk/rules.py` `MaxLossPerTrade`,
  `fno/risk/open_risk.py` `of_legs`). C2 runs on the shadow's own book, so it refuses any entry whose modelled maximum
  loss is above the cap. That model takes the worst payoff at expiry and adds the entry cash and the exit charges, with
  B2's pads.
  - Experiment 1's -11,346 came from an exit priced on a stale close. Live exits use the day's snapshot quotes after
    A4's validity checks (E4), so a stale close is not used as such.
  - The live exit happens 21 or more days before expiry, buying back at the ask and selling at the bid. The cost of
    closing the losing side can exceed its width when its bid-ask spread is wider than B2's pad. Nothing re-sizes an
    open trade.
  - So the cap prevents a modelled loss above Rs 10,000, not a realised one. A realised loss above it is caught after
    the fact by E6's alert above. A second one is escalated as a possible fill or settlement defect (reasoning only;
    no live condor exit has been measured).

**Split:**
- E6's files (`pauses.py`, `report.py`) are shared with E6b's builder (session 0134MoC6f7aAJVcHRBiyATo6). Agreed on
  16 Oct:
  - R3 makes both edits. E6b changes only the entries line of `card_lines`, never the title, the shadow section or
    `pauses.py`; whichever merges second resolves any text conflict and re-runs the full suite;
  - `is_measurement` is public, in its own module `fno/playbook/measurement.py`, so E6b can read it too;
  - a test pins the non-measurement title and alert bytes.
- D1's fields are unchanged; only the new predicate is added.
- E8's builder (session 01H1CmuWzBtbtjzoQNJUz2Dz) confirmed that E8 adds no caller of the two record readers
  (condition 11 is R3's).
