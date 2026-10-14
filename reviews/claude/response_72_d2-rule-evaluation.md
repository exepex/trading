# Response 72: story D2, rule evaluation and allocation (builder's claims for the judge)

Story: `docs/stories/D-playbook-decisions.md` D2. Builder: Claude, 14 Oct 2026. Branch `story/d2-rule-evaluation`
(nothing on `main` until the judge passes it). Research and paper only: nothing here places, modifies or cancels
orders, and the playbook approves nothing today.

## 0. The verdict in two lines

Book 1's daily decision is built as code. Each approved version's rule is evaluated on the live 15:00 feature values;
a fired rule builds its trade on live quotes; and a fixed rule allocates slots and cash in rank order through the
risk manager (C2). Registered research candidates are evaluated the same way in shadow, each against its own shadow
book, and never touch Book 1's account (owner's option (a), 14 Oct). With nothing approved, nothing is allocated.

## 1. Format additions to D1 (orchestrator's decisions 1-5, 14 Oct 2026)

D2 needs, in machine form, things D1 only had as text or did not have. All are required fields and part of the
version's fingerprint. No version is registered, so no fingerprint breaks; only the example file changed.

| Field | Meaning |
|---|---|
| `structure.widths` | wing widths in points, widest first; the desk keeps the widest whose maximum loss (all costs) is within C2's Rs 10,000 (B2's rule) |
| `structure.lots` | whole number, at least 1; a size that breaks Rs 10,000 is refused, never trimmed |
| `structure.expiry` | `{kind: monthly, min_days, max_days, exit_days_before_expiry}`; the opportunity is the first trading day the expiry is in the window; exit is the last trading day at least N days before expiry. Experiment 1's 30/45/21 are the example's values, not defaults |
| `evaluation_plan.expected_net_per_opportunity` | the frozen estimate D2 ranks by; `none` allowed for research only; `paper` needs a number (new approval check `ExpectedNetSet`) |
| `evaluation_plan.expected_net_source` | where the estimate comes from (e.g. the discovery results); a new estimate is a new version, never an update from shadow results |

Parsing: `fno/playbook/structure_spec.py` (new) and `schema.py`.

## 2. Design

| Part | File | Job |
|---|---|---|
| Opportunities | `opportunities.py` | (version, monthly expiry) opportunities today; E2 is meant to reuse this |
| Conditions | `conditions.py` | each condition on its **live** B7 feature; `None` is unmet; every unmet condition is written out with the value seen |
| Candidate | `candidates.py` | body strikes from the structure code (B2's classes), widths widest first on valid (non-stale) quotes only, C2's cost model for maximum loss; maximum loss of 0 or less is a validity failure (no trade); score = expected net / maximum loss |
| Allocation | `allocation.py`, `book_effects.py` | rank order (score desc; then lower maximum loss, earlier expiry, name, version); no-trade threshold Rs 0 (paper only); the unproven limit per version (fewer than 20 completed trades: at most 1 open); C2's full risk manager on the book **as it would be after the trades already chosen today** (cash, marked equity, open trades) |
| Evaluator | `evaluate.py` | Book 1 = approved versions against the book's account; shadow = each registered research version alone against its own shadow book (`ShadowBooks` interface), threshold off; a shadow book named like a real book is refused |
| Outcomes | `outcomes.py` | one outcome per opportunity (chosen, not chosen, no trade, shadow trade, shadow no trade) with live values, unmet conditions, legs, maximum loss, score, C2 verdicts and reason; `DayEvaluation.record()` is deterministic |
| Wiring | `wiring.py`: `build_rule_evaluator`, `build_live_feature_values` (`live_values.py`) | session calendar, B2 structures and costs, `build_risk_manager` with all six C2 rules, lot size and cap from `config.yaml` |

Interfaces left for later stories:
- `StrategyTradeCounts`: Book 1's completed and open trades per version; E5 implements it, tests use a fake.
- `ShadowBooks`: each candidate's shadow account; the E4/C1 side.
- C2's `Market` (live quotes, IV, futures) is an input: nothing builds it from the A4 snapshot yet (E2/E5).

## 3. Claims per acceptance criterion (`tests/playbook/test_evaluate.py` unless named)

| # | Criterion | Tests |
|---|---|---|
| 1 | All conditions true except one: no fire, the unmet condition recorded | `test_one_unmet_condition_stops_the_rule_and_is_recorded` (number below threshold, unknown value, flag true) |
| 2 | Two fired candidates, one free slot: higher expected net per rupee of risk chosen, the other "not chosen: slot" | `test_with_one_free_slot_the_better_expected_net_per_rupee_wins`, `test_ranking_is_per_rupee_of_risk_not_raw_expected_net` (higher raw net, lower score, loses), `test_ties_go_to_the_strategy_name_when_score_loss_and_expiry_are_equal` |
| 3 | Negative expected net after costs: no trade | `test_expected_net_not_above_zero_trades_nothing` (-50 and exactly 0) |
| 4 | Unproven version with one open trade: a second refused | `test_an_unproven_strategy_with_an_open_trade_gets_no_second` (19 completed refused; 20 completed or no open trade allowed) |

Further claims:
- Shadow: `test_a_registered_research_candidate_is_evaluated_in_shadow_only`, `test_shadow_and_book_never_share_slots`,
  `test_a_misconfigured_shadow_book_never_draws_on_a_real_account` (each of the 3 book names; Book 1's outcome is
  byte-identical to the run without the shadow), `test_an_unregistered_candidate_is_not_tested`,
  `test_a_shadow_version_without_an_estimate_still_records_what_the_rule_would_do`,
  `test_the_no_trade_threshold_binds_paper_only_not_the_shadow`.
- Nothing approved: `test_nothing_approved_allocates_nothing`, `test_paused_and_retired_versions_are_not_evaluated`.
- Size and validity:
  - `test_lots_whose_max_loss_breaks_the_cap_are_refused_never_trimmed` (3 lots: about Rs 14,550, refused; 1 lot of
    the same trade passes);
  - `test_c2_refuses_the_same_oversized_trade_on_its_own`;
  - `test_impossible_prices_are_a_validity_failure_not_a_trade`;
  - `test_no_width_within_the_cap_is_no_trade`;
  - widths 300 and 200 refused and 100 kept, in `test_all_conditions_true_fires_and_the_widest_width_within_the_cap_is_traded`.
- Opportunities (`test_opportunities.py`): first session in the window only, the first session after a weekend,
  outside the window, a non-session day, the exit day.
- Determinism: `test_the_same_inputs_give_the_same_record`. Wiring: `test_evaluation_wiring.py` (all six C2 rules,
  cap Rs 10,000, lot 65).
- Approval check: `test_loader.py::test_paper_needs_a_number_for_expected_net`,
  `test_a_research_version_may_have_no_estimate`. The D1 test helpers now use the app's own wiring
  (`build_playbook_loader`), so the check list is defined once.

## 4. Mutation checks (each made, `tests/playbook` run, reverted): 15 of 15 caught

| Mutation | First failing test |
|---|---|
| condition check off | `test_one_unmet_condition_stops_the_rule_and_is_recorded` |
| score not divided by maximum loss | `test_ranking_is_per_rupee_of_risk_not_raw_expected_net` |
| rank order reversed | `test_with_one_free_slot_the_better_expected_net_per_rupee_wins` |
| threshold `<=` becomes `<` | `test_expected_net_not_above_zero_trades_nothing[0.0]` |
| unproven limit `>=` becomes `>` | `test_an_unproven_strategy_with_an_open_trade_gets_no_second` (confirmed by hand) |
| book not updated after a choice | `test_with_one_free_slot_the_better_expected_net_per_rupee_wins` |
| shadow decision label not applied | `test_a_registered_research_candidate_is_evaluated_in_shadow_only` |
| unregistered candidates shadow-tested | `test_an_unregistered_candidate_is_not_tested` |
| cap check off | `test_all_conditions_true_fires_...` |
| validity check off | `test_impossible_prices_are_a_validity_failure_not_a_trade` |
| "first day in window" check off | `test_later_sessions_in_the_window_are_not_new_opportunities` |
| real-book guard off | `test_a_misconfigured_shadow_book_never_draws_on_a_real_account` |
| shadow threshold on | `test_a_shadow_version_without_an_estimate_...` |
| `ExpectedNetSet` off | `test_paper_needs_a_number_for_expected_net` |
| shadow uses Book 1's book | `test_a_registered_research_candidate_is_evaluated_in_shadow_only` |

## 5. Limits and doubts, said plainly

- **No CLI and no real day run yet.** C2's `Market` from the A4 snapshot, `StrategyTradeCounts` and the shadow books
  come with E2/E5. D2's "judge verifies" (re-run a day from its decision record) needs D3's record. Until then,
  determinism is tested on the same inputs.
- **A maximum loss of zero or less stops the opportunity** (no trade, "validity"), as D2's text says. The research
  skipped such a width and tried the next one. The story's wording wins here; the judge may disagree.
- **The unproven limit counts per version** (name and version): a new version starts unproven again. Reasoning: a
  changed rule is a new strategy.
- **The three book names are hard-refused as shadow books**, but a shadow book named anything else is trusted to be
  the candidate's own: the `ShadowBooks` implementation (E-side) owns that.
- **Ranking without an estimate** (shadow only) puts such candidates last; it matters only if one candidate had two
  opportunities the same day, which the monthly window rules out.

## Addendum 1 (14 Oct 2026): judge 69's findings, all accepted and fixed

1. **Must-fix: impossible prices follow the research exactly. Accepted.**
   - What the research does: experiment 1's protocol ("Impossible prices") and `simulator._entry_trial` skip a width
     whose entry prices lie at or beyond the position's payoff bounds, then try the next width.
   - What D2 did instead: it caught only "maximum loss at most 0" (the cannot-lose half), and it stopped the whole
     opportunity there.
   - The fix: `candidates.py` now uses the research's own `payoff_bounds` and `position_value`. A width that cannot
     lose or cannot win is recorded as "bad prices" and skipped. The old "validity" stop is gone.
   - Story line amended, with the orchestrator's sign-off.
   - Tests: `test_a_width_that_cannot_lose_is_skipped_as_bad_prices`, `test_a_width_that_cannot_win_is_skipped_as_bad_prices`
     (a debit condor, whose small maximum loss would otherwise pass the cap) and
     `test_after_a_bad_wide_width_the_narrower_tradable_width_trades` (300 and 200 cannot lose; 100 trades). All three
     fail on the old stop-the-opportunity code.
2. **Should-fix: tie order. Accepted.**
   - Test: `test_equal_scores_go_to_the_lower_maximum_loss_before_the_earlier_expiry`. Both candidates score exactly
     0.1, and the larger-loss one has the earlier expiry.
   - The judge's plant (expiry before loss) now fails it.
3. **Shadow separation proven when built. Accepted.**
   - `ShadowBooks.account()` now returns a `ShadowAccount` with the folder it is stored in (`fno/playbook/shadow.py`).
   - `RealBooks` (wired with `journal/<book>` for the three books) refuses a shadow account in any of these cases:
     - it is named like a real book or like Book 1's book;
     - it is stored in a real book's folder;
     - it is stored inside a real book's folder;
     - it is stored above a real book's folder (e.g. `journal/`);
     - it reaches any of those through `..`.
   - Tests: `tests/playbook/test_shadow.py`, including Book 1's records being unchanged when a misplaced shadow is
     refused.
4. **Number:** response 72 stays D2's.

Checks on the tree merged with `main`: full suite 2238 passed (`tests/playbook` 244), ruff and check_imports clean; 19 of 19 mutations
caught, run with bytecode caching off. An earlier run on the same container showed wrong "first failing test" labels
from stale `.pyc` files; the kills themselves held, and the labels above are from the clean run.

## Addendum 2 (14 Oct 2026): the playbook as of the start of the decision day (branch `story/d2-start-of-day`)

Orchestrator's decision, from E2's response 74 §4.1: an approval counts from the next session's start, everywhere.

- `Playbook` now carries the registry rows; `status_on(day)` is each version's latest change dated before the day.
- `approved_on(day)` and `shadow_on(day)` replace the old current-status reads in `RuleEvaluator`.
- `approved()` (the status now) stays for `playbook check`. The old `registered` field and `shadow()` are gone.
- Tests:
  - `test_an_approval_made_on_the_day_trades_from_the_next_session_only`: a candidate registered before the day and
    approved on it is still evaluated in shadow that day; Book 1 chooses nothing, and it is approved from the next day.
  - `test_a_pause_on_the_day_takes_effect_from_the_next_session`.
- Mutations, both caught by the first test:
  - `changed_on <= day`;
  - the evaluator reading `approved()`.
- Consequence, said plainly: a hard-loss pause made during a session also takes effect from the next session. The
  same day had only one decision at about 15:00, so no new trade is lost. E6 must still stop new entries at once if it
  pauses before that day's decision; that is E6's design point.
- When E2 merges, its `opportunity_set.approved_on` should call `Playbook.approved_on` (one rule, not two). I will
  make that one-line change in E2's next round or after both merge.

## Addendum 3 (14 Oct 2026): judge 74, stops take effect at once (accepted)

Judge 74 is right, and my addendum 2 reasoning was wrong. A pause dated on the day can be written before the 15:00
decision (a morning hard-loss pause, the owner's stop at 10:00). Nothing after D2 checks the playbook status (E4's
entry desk does not), so D2 must stop it.

- **Rule (risk manager's, judge 74):** a version trades on day D only if it was `paper` at the start of D **and**
  is still `paper` after every change dated D.
  - Approvals and resumptions wait for the next session.
  - A pause or retirement stops new entries at once.
  - Code: `Playbook.status_through(day)` (changes dated on or before the day); `approved_on` requires both.
- **Rebuilds stay stable:** both read registry dates only. On the live day no later row exists, so "through the day"
  is "now".
- **Not included:** E6's "drifted" set is not on `main`; E6 adds that check after this merges, as judge 74 sets out.
- **Tests:**
  - `test_a_stop_on_the_day_takes_effect_at_once`, for a hard-loss pause, the owner's pause and retirement: empty that
    day and after, unchanged the day before, and the evaluation chooses nothing;
  - `test_a_resumption_on_the_day_waits_for_the_next_session`;
  - the old "pause from the next session" test is replaced.
- **Mutations:**
  - dropping the "through the day" condition fails 3 tests;
  - dropping the "start of the day" condition fails the approval and resumption tests.
- The shadow side is unchanged; judge 74 accepts it.
