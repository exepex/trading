# Epic R: the strategy factory (layer 4)

Roles: options strategist, statistician, F&O trader, risk manager, tax and cost accountant. Goal: turn ideas into a
forward record that can be trusted (design v2 `03_layers_factory_desk.md`; `REPLAN_new_stories.md` R1-R3). R1's
documents are in `research/FACTORY_RULES.md`, `research/DATA_SPEND.md` and `research/ideas/TEMPLATE.md`. Story template
and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

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
  - the shadow books get Book 1's recorded terms, not each shadow's own (`fno/books/book1_wiring.py` `_parts`).
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
- **Shadow fills and exits, through the desk's one fill path:** a "shadow: would trade" decision is filled into its
  shadow account exactly as a book's entry, and its exits run as a book's:
  - E8's owner-timing rule (`docs/stories/E8-owner-timing-fills.md`): order time T = that day's card delivery time,
    the same T as the books (a shadow models the owner acting on the day's card), the verdict view at R = 60, the
    price cap, and the funds re-check;
  - no card delivered: "missed, card not delivered", as for the books;
  - costs from C1 (`config.yaml` `charges`), the same as the books;
  - **the contract with E8 (agreed, below):**
    - R3 writes each "shadow: would trade" decision as a pending order in the day's journal, in exactly the order
      format Book 1's orders use, with the account id `shadow:<name>-v<n>`;
    - E8 fills every pending order whatever its account, through the same code as a book's, so no separate shadow
      fill step exists;
    - R3 fills E8's one terms lookup (funds, limits, charges), keyed by account, for each shadow, as Book 1's wiring
      does for Book 1. The fill-day funds and risk re-check runs on the shadow's own terms. It is a check only,
      never a decision counted by E6, S1 or S2;
    - E8 never creates an account. A pending order for an account that does not exist fails loudly, so R3's opening
      step must run first;
  - until E8's part 1b is merged, nothing fills a shadow (no second, earlier fill rule is built).
- **The registration procedure** (written in this story; R1's code, `CostWall` and `IdeaCard`, is not built):
  1. an idea card from `research/ideas/TEMPLATE.md` with its G0 and G1 sections, the cost wall worked by hand under
     `FACTORY_RULES.md` (expected net after costs and tail losses above zero on the conservative bound), or the label
     `measurement` (B0 only);
  2. a ledger row first (`research/ledger.csv` via B4's guard; the trial count includes screened-out ideas);
  3. the frozen playbook version (SF, SC or BF only until STR1b-2), registered `research` with
     `python -m fno playbook set-status` (owner or desk, `fno/playbook/transitions.py`);
  4. a measurement shadow's card and ledger row say "never promoted". Approving it to paper needs the owner's own
     decision, which this label does not grant.
- **Results:** the shadow accounts' closed trades, net after costs, feed:
  - E6's existing scorecard shadow section (evidence only; alerts, never pauses; `fno/scorecard/report.py`,
    `pauses.py`, unchanged);
  - the stop-rule tracker's Test B input "R3: resolved shadow trades, net after costs" (`fno/budget/stop_rule_tracker.py`,
    `path=None` today). R3 sets its path to the closed-trades file and tells BG1's owner.
- **B0's registration (owner, decision 1 A), counted in the trial total:** experiment 1's P1 rule (SC every monthly opportunity),
  its card labelled `measurement`, never promoted. It is stopped if a single loss exceeds Rs 10,000 (response 92's
  "what proves it wrong").

Out (each with where it goes):
- **V1 and V2 shadows:** later R3 work, when their blockers clear: A16's 20 sessions and G10 part 2 for V1; G7 phase 2
  and STR1b-2 for V2. A v4 forecast feature in the playbook is R3's to build then (the A16/G8/G10 builder agrees;
  playbook is D1's function). It reads through G8's `V4ForecastSource.values`, wrapped in `LateDaysOut`, live rows of
  the decision day only (final at the 14:30 cutoff).
- **R1's code** (`CostWall`, `IdeaCard`, `SamplePlan`, `fno/factory/`): R1. R3 applies the cost wall by hand.
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
8. A measurement shadow's idea card, ledger row and registry evidence say `measurement: never promoted`.
9. Nothing in R3 changes a book's account, decision or fill.

**Test plan:** fakes for the registry, the shadow accounts, E8's fill rule and the clock.
1. Positive: registration on d, account opened, one "would trade" filled, then exited and closed.
2. Negative: an unopened shadow (opened, never raised); Book 1's terms kept out; "no trade" filled nothing.
3. Empty: no research version (nothing opened, Test B "undecided").
4. Isolation: one book trade and one shadow trade on the same day, each in its own account.

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

**Build order (decision 2 A):** the account opening and the per-shadow terms are built now (criteria 1-2), and B0 is
registered after they merge. Shadow orders and fills (criteria 3-5) are built when E8's part 1b merges.

**Depends:** D1, D2, E3, E5 (Book 1's run), E8 (fills), E6 (scorecard), BG1 (stop-rule tracker), STR1b-2 and G7/A16/G10
for the V-ideas · **Size:** M · **Status:** story text, waiting for the judge
