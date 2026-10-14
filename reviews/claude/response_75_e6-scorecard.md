# Response 75: story E6, strategy paper scorecard and pause rules: builder's claims

Builder session, 14 Oct 2026. Story: `docs/stories/E-paper-desk.md` E6. Branch `story/e6-scorecard`; judge first,
nothing on `main`. Orchestrator's task included judge 67's follow-up (drift pauses one version) and scorecards for
shadow versions (owner's choice a), kept apart from Book 1's.

**Verdict in one line:** `python -m fno desk scorecard` scores every version in every account against its plan, from
the records only, after the automatic pause rules have run. A catastrophic loss or a live-feature drift pauses that
version alone. 21 scorecard tests, 10 shadow-account and shadow-book tests, 5 changed or new loader tests. 28 of 28
planted defects caught; the 32 desk plants are still caught.

## 1. Design decisions (the defaults I sent the orchestrator; no change was asked)

| # | Decision | Why |
|---|---|---|
| 1 | E4's desk records gain `strategy` (`<name>-v<n>`) on every fill and event, and the touch (`quote_bid`, `quote_ask`) on every fill. `EntryOrder.strategy` is filled by E3/E5 from the D3 decision. | Nothing linked a trade to its version; the half-spread needs the quote each fill met (point in time, never re-read). |
| 2 | A gate refusal (C2 refused, decision too late, incomplete snapshot, blocked book) is its own outcome, `refused`, apart from `not_opened` (a leg did not fill, or the entry was worse than approved). | Criterion 3's "attempted trades that did not fill" must not count risk refusals as fill failures. |
| 3 | A shadow version's forward test has its own account `journal/shadow/<name>-v<n>/account/` (named `shadow:<name>-v<n>`; E1's firewall and lock unchanged; same E4 desk and C1 costs). | Owner's experiment 2 option a: never in Book 1's account. This fits D2's `ShadowBooks` interface (merged meanwhile): storage outside every real book's folder, so it can implement it. |
| 4 | The plan gains a required number `evaluation_plan.catastrophic_loss_rs`. | D1's `pause_rules` are free text and cannot be machine-checked. Only the example file (research, unregistered) changed. |
| 5 | Review rule (reasoning only, fixed before any paper result): only on a review date and past the gate; mean C1 net per completed position with a seeded bootstrap 95% interval (experiment 1's `resampled_means`, 10,000 resamples, seed 20261014, nearest rank 2.5% and 97.5%); **retire** when the upper end is below the expected low, **pause** when the mean is below it, else **keep**; **net profit shown** only when the lower end and the whole net (legging costs included) are above zero; real money is always the owner's decision. Provisional until S1. | The plan has an expected range but no decision rule. A bootstrap reuses the research's own resampler (no scipy in the repository). |

## 1a. The orchestrator's notes on the defaults (all done on this branch)

- **D2's `ShadowBooks`:** `fno/desk/shadow_books.py` `JournalShadowBooks` is the one implementation (D2/E2's builder is
  told E6 owns it). Each registered research candidate's account is `journal/shadow/<name>-v<n>/account/`: its C2
  risk view and its trade counts come from that account only (`fno/desk/trade_counts.py` `DeskTradeCounts`, which
  E5 can reuse for Book 1). `start_shadow_books` opens the accounts once; an account that was not started is refused,
  never created on the fly. `fno/desk/wiring.py` wires both.
  - **Proof it writes only inside its declared folder:** `tests/desk/test_shadow_books.py` hashes every file under
    the repository root before and after an E4 entry in the shadow account. Every changed or new file lies inside
    `ShadowAccount.storage`, none under a book's folder, and D2's `RealBooks.overlap` is None.
  - Mutation "shadow stored in a book's folder" is caught.
- **`catastrophic_loss_rs` within C2's limit:** `fno/playbook/rule_checks.py` `CatastrophicCapWithinRisk` refuses a
  cap above `risk.max_loss_per_trade_rs` (Rs 10,000) for every file, research included. Rs 10,000 loads; Rs 10,000.01
  is refused ("could never fire"). The limit is read from config.yaml by the playbook's composition root.
  - Mutations caught: the check off, `>=` in place of `>`, and the rule checks never run.
- **Review rule provisional until S1:** the thresholds live only in config.yaml `scorecard_review` (status "provisional
  until S1", 20 positions, 3 months, 95%, 10,000 resamples, seed), read through `ReviewTerms`. S1 replaces them there
  with no code change, and every review shows the rule's status.
- **Never automatic promotion:** the field is `profit_shown`, worded "net profit shown: the owner may discuss real
  money (never automatic)". Nothing in the code promotes.

## 1b. Judge 73 (FAIL on c264ccd): my answers, on head after b5c957f

| # | Finding | Answer and evidence |
|---|---|---|
| 1+2 | An old loss re-pauses after the owner's re-approval; a shadow loss pauses the version once approved | **Accepted, root fix.** An approved version is paused only by a trade in a **book** account (never `shadow:...`) closed **on or after its latest change to paper** (registry). Tests: `test_an_owner_re_approval_after_a_pause_sticks` (and a new loss after re-approval pauses again), `test_a_shadow_loss_never_pauses_an_approved_version`, `test_a_book_loss_closed_before_the_latest_approval_never_pauses`. Plants "a shadow loss pauses an approved version" and "a loss before the latest approval pauses" are caught. Day granularity: a loss on the very day of a re-approval counts (the registry has dates, not times), which errs on pausing. |
| 3 | The cap check is missing (50,000 parses) | Already fixed in b5c957f, after the commit judged: `CatastrophicCapWithinRisk` reads `risk.max_loss_per_trade_rs` from config.yaml and refuses any cap above it, for every file. Rs 10,000 loads; Rs 10,000.01 is refused. |
| 4 | Same-day pause | **Waits for D2's start-of-day fix**, as the judge says. After it merges I add the test through D2's evaluator: a pause written before 15:00 stops that day's trade. |
| should | Pin the bootstrap interval | Accepted: `interval(range(-10, 10))` is pinned to (-3.0, 2.05); another seed or 90% (-2.6, 1.6) fails it. Both plants caught. |
| should | Label "provisional until S1" in the report | Already in b5c957f: every review line shows `rule provisional until S1`. |
| should | One shared constant for the 20-position gate | Accepted. The gate is design 6's paper gate, the same number D2 uses, so it is now `UNPROVEN_BELOW_COMPLETED_TRADES` (with a new `PAPER_GATE_MONTHS = 3`) in `fno/constants.py`. The statistics S1 will freeze (confidence, resamples, seed, status) stay in config.yaml `scorecard_review`. That way both the judge's "one constant" and the orchestrator's "S1 replaces without code" hold. |
| should | One `desk` parser | Accepted: `fno/desk/cli.py` owns the one `desk` parser; each story adds a command to its `COMMANDS` tuple and sets its own handler (E6: `add_scorecard_command`). I proposed this to E2's builder (its branch adds `pack` in `fno/desk/pack_cli.py`); whoever merges second folds into the first. |
| owed | The ShadowBooks write-containment test | Already in b5c957f: `tests/desk/test_shadow_books.py::test_trading_in_the_shadow_account_writes_only_inside_its_declared_folder`. |

Mutation checks run as the judge asks (`python -B`, caches cleared): E6 **28 of 28**, desk (E4, E7) **32 of 32**.

## 2. Acceptance criteria, claims and evidence

| # | Criterion | Claim | Evidence (tests) |
|---|---|---|---|
| 1 | Catastrophic loss: `paused` at once, no new trades in any book, owner alerted | Met. A closed trade (completed or unwound) whose C1 net loss reaches the cap, in **any** account, pauses that version: D1's status change `paper -> paused` by `hard_loss_rule`, so `approved()` drops it for every book. One #fno-desk line names the trade and the book. A rerun writes and alerts nothing more. Exactly at the cap pauses; a paisa below does not. | `tests/scorecard/test_pauses.py`: `test_a_catastrophic_loss_in_any_book_pauses_that_version_at_once_and_alerts` (the loss is in Book 2, the version stops for all books), `test_a_loss_exactly_at_the_cap_pauses_and_a_paisa_less_does_not` |
| 2 | Gate: at least 3 months and 20 completed positions, only on review dates; open positions at marks, not counted; inconclusive never promoted | Met. 19 positions: "keep: the gate is not met, not judged". 20 positions in 2 months: not met. Not a review date: no decision. An open trade is shown at the snapshot's mids (none if a leg has no valid quote) and never enters the sample. A positive total with an interval spanning zero is kept, "inconclusive: no net profit shown". | `tests/scorecard/test_review.py` (10 tests), `test_scorecard.py::test_open_positions_are_shown_at_marks_and_never_counted` |
| 3 | Execution costs equal a hand computation on fixture fills | Met. Half-spread: 4 fills x 65 units at Rs 0.50 and 2 x 65 at Rs 1.50 = Rs 0.8333 a unit (research pad Rs 1). Legging Rs 123.45 + Rs 10 = Rs 133.45. 4 attempts reached the fill step: 2 opened, 2 not filled (50%), 1 refused counted apart. Pending exits: 3 days (closed) and 4 days (still waiting at the run date): mean 3.5. C1 net of a trade equals (credit - debit) x 65 minus `order_charges` of its 4 orders; the tax line is 31.2% of it. | `test_scorecard.py::test_execution_costs_measured_from_the_record_equal_a_hand_computation`, `test_the_ledgers_carry_every_closed_trade_at_c1_s_net`, `test_each_version_in_one_account_is_scored_on_its_own_trades_only` |
| 4 | On a review date: keep, pause or retire per the plan's rules | Met. A clear loser (about -Rs 1,500 a position against -500) is retired; a winner past the gate is kept with net profit shown (the owner decides on real money). The rule's boundaries are checked by hand in `decide`. The decision is **stated**, not applied: under D1 only the owner pauses for statistics or retires (design 12.8). | `test_review.py::test_a_clear_loser_is_retired_on_the_review_date`, `test_a_winner_past_the_gate_is_kept_and_shows_profit`, `test_the_decision_rule_by_hand` |

**Judge 67's follow-up (orchestrator's task):** the loader no longer refuses the whole playbook when a paper version's
live feature drifts. That version is left out of `approved()` at once and listed in `Playbook.drifted`; the scorecard
run pauses it (`hard_loss_rule`) with one alert; the others keep loading and trading. A change **to** paper with an
unvalidated feature is still refused. Tests:
- `tests/playbook/test_loader.py::test_one_drifting_version_leaves_the_other_approved_versions_trading`
- `test_a_change_to_paper_with_an_unvalidated_feature_is_still_refused`
- `tests/scorecard/test_pauses.py::test_a_drifting_version_is_paused_and_the_other_versions_keep_trading`

`playbook check` lists drifted versions.

**Shadow versions:** scored like any account, reported under "Shadow tests (evidence only, never a book's record)". A
shadow version's catastrophic loss is alerted once (on the day the trade closed), never paused: research cannot be
paused, and the owner decides. Tests: `test_a_shadow_versions_catastrophic_loss_is_alerted_once_never_paused`,
`test_shadow_tests_are_reported_apart_from_the_books`, `tests/books/test_shadow_accounts.py`.

## 3. Mutation check and a flaw found in my own earlier mutation runs

23 E6 plants, each must fail a test: **23 caught** (5 added for the shadow books, the trade counts and the cap check). The plants covered:
- a loss exactly at the cap ignored; the pause never written; drift ignored;
- a drifted version still approved; drift refusing the whole load again;
- a shadow paused like paper; a shadow re-alerted every day;
- the half-spread sign flipped; refusals counted as fill failures;
- waiting exits not measured; legging not summed;
- a gate of 19 positions; the months not checked; retire on the mean;
- promotion without proof; judging outside review dates;
- open trades counted; versions not kept apart.

Two of those plants first **survived** ("promoted without proof", "versions not kept apart"). I strengthened two tests
(a positive-total inconclusive history; two versions in one account) until both failed.

**Flaw in my mutation script (found and fixed today):** Python's bytecode cache checks the file's size and modified
second. A plant of the same length, restored within the same second, left a stale compiled copy of the mutated code
for the next runs. That can make a later plant look "caught" when it was not. I saw it as a real test failure after a
run ("short legs first" was still compiled in). Every mutation run was repeated with caching off (`python -B`, all
`__pycache__` removed first): E6 23 of 23, desk (E4 and E7) 32 of 32. Those E4 and E7 numbers stand.

## 4. Honest limits

1. **The review rule is reasoning only.** It was fixed before any paper result, but nobody has reviewed it. The
   bootstrap interval with 20 positions is rough; the gate is a minimum, not proof (design 6). The plan's `unit` must
   mean "per completed position before tax" for the comparison to be fair; the example file says "per opportunity
   after tax". The report prints both units side by side, so a mismatch is visible, not hidden.
2. **Legging-cost trades are in the ledgers and the whole net, not in the review's sample of positions.** That is
   conservative for promotion (the whole net must be positive too), but the mean per position flatters a version that
   legs often. The legging total is printed next to it.
3. **Shared operating costs are not allocated to versions.** The account ledger here is the version's trades only; the
   desk's own costs stay at account level (C1).
4. **Who runs it:** the pauses fire when `desk scorecard` runs (or E3's daily run calls it), not on their own. The
   status change writes `playbook/registry.csv` and the version's file; the caller commits them (D1's rule).
5. **E3 must fill `EntryOrder.strategy`** from the D3 decision (D2's decisions carry name and version).

## 5. Checks on the merged tree

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py`: in the commit message and the
message to the orchestrator.
