# Response 281: A14c families, code (builder's claims for judge D)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, 16 Oct 2026. Branch `story/a14c-families`. Text: the "A14c families" paragraph
of `docs/stories/A-data-foundation.md` (text PASS, judge 290). Lane 1 (risk inputs, C2 and C4).

## What changed (strong evidence: the diff and the tests named)

| Part | Where | Test |
|---|---|---|
| One family table, debit = BF, LC, LP, CDS, PDS; credit = SF, SC, CCS, PCS; tied to `payoff_bounds` | `fno/constants.py` `STRUCTURE_FAMILIES`; column names moved to `fno/constants_margins.py` (constants.py is at 350 lines) | `test_every_tradable_structure_has_the_family_its_payoff_bounds_give` (every tradable code at widths 100-300; a swapped family fails it) |
| A code with no family refuses by name, in C2 and C4 | `fno/risk/stress_factor.py` `family_of`; `fno/checks/validity_factor.py` (its own reader: story C4 is written apart) | `test_a_code_with_no_family_refuses_by_name` [C2, C4] |
| C2 and C4 read the latest row before the day whose family is the proposal's or `all`; a family with neither refuses by name | `factor_in_force(..., family)`, `factor_on(..., structure)` | `tests/risk/test_stress_factor_families.py` (6 cases x 2 readers) |
| The stressed margin, the margin at entry, and the decision record use the proposal's family | `MultiplierMargin._factor/_row/record`, `rules.py`, `validity_margin.multiplier` | `test_the_margins_use_the_k_of_the_proposal_s_structure` (NSE's real 14 Oct rows: raising only the credit k moves SF in C2 and C4, BF is unchanged); `test_the_decision_records_the_row_of_the_proposal_s_family` |
| Header-only migration: the first family run rewrites line 1 only; every data row keeps its bytes | `stress_log.StressFactorFile.append` (writes `.tmp`, then replaces) | `test_the_first_family_run_changes_only_the_header_line` (the repository's two real rows) |
| Rows before the column read as `all`: in force for both families, never a floor (so the first family run is full) | `StressFactorFile.last(family)` | `test_rows_written_before_the_family_column_are_read_as_all_and_force_a_full_run`, `test_one_family_without_its_own_measured_row_makes_the_whole_run_full` |
| Each family carries only its own measured value; a later `all` row is in force but never a floor | `last(family)` | `test_each_family_carries_only_its_own_measured_value`, `test_a_later_all_row_is_in_force_but_never_a_floor` |
| Measured structures: SF, SC, BF only (C2 caps the STR1 codes' stressed SPAN) | `fno/nse_margins/wiring.py` `build_stress_factor_run` | `test_the_wired_run_measures_only_the_structures_c2_does_not_cap` |
| Impossible entry price skipped and named (NOV per unit not strictly inside the legs' payoff bounds: B2's BAD_PRICES test, now one shared `possible_value`) | `held_rise.py` `_open_one`, `structures.possible_value` | `tests/nse_margins/test_needed_factor.py` (the real BF 200 of 8 Apr 2020: 875.55 a unit on a 0-200 position, skipped) |
| One row per family, each with its own guardrail decision, peak and approval note (named only on that family's real fall) | `fno/nse_margins/family_result.py` (new), `stress_run.py` | `test_an_approval_is_named_only_on_a_real_fall` (credit rises, debit falls in one run) |
| Evidence per family: a table (positions measured, largest needed, computed, factor in force, peak), skipped entries listed, scope column = family | `stress_evidence.py` | `test_a_rise_is_applied_at_once_with_its_evidence`, byte-identical and read-ahead tests |

The test fixtures changed in two honest ways: the span builder's SF prices were impossible (a credit of 165 on a 100
width) and are now realistic (bought legs 75/70, NOV -5,525), and the planted run now measures SF and BF (one per
family). The planted BF 100 needs exactly 1.0 every day, so in those tests the debit row is a held fall to 1.0.

## Mutations (strong evidence: each run on `tests/nse_margins tests/risk tests/checks`, bytecode off)

All 15 caught: the own-row filter replaced by the in-force one (2 failed); the header rewrite removed (1); the measured
filter removed (1); the family filter in the counted holdings removed (5); the approval named on every row (1); `any`
to `all` in the full-run rule (1); the impossible-price check removed (1); C2's family filter reduced to `all`
(9); C4's family filter removed (7); C4's multiplier reading BF's family (1); C2's stressed margin, margin at entry and
record each reading BF's family (1, 1, 2); the decision record in `rules.py` reading BF's family (2). Note: my first
pass reported two survivors that were stale bytecode (same-second restore); I reran every mutation with
`PYTHONDONTWRITEBYTECODE=1` and cleared caches.

## A choice the text does not state (for the judge to rule)

- **A family with no completed holding and nothing carried refuses the whole run** ("no debit holding completed in the
  archive"; nothing written, one #fno-desk line), rather than writing the other family's row alone. Reason: a
  partial run would leave one family on a stale row with no alert of its own; fail closed is simpler. On the real
  archive both families have thousands of holdings, so this only fires on a broken archive or wiring
  (`test_a_run_that_cannot_measure_a_family_writes_no_row`).
- An incremental run reads from the earlier of the two families' `coverage_through` minus 60 days, then counts each
  family's holdings against its own date. Both families are always written together, so the dates are equal in practice.

## Gates

`ruff check`, `ruff format --check`, `tools/check_imports.py` and the full suite on the merged tree are reported in my
message to the judge with the head SHA. Full suite on the merged tree 4765c3e6: 7976 passed, 18 xfailed. An earlier run had one unrelated failure
(`tests/versions/test_versions.py::test_a_pause_in_one_book_leaves_the_others_scored`) did not reproduce in three runs on
its own and is reported to the orchestrator as a possible load flake.

## Round 2, 21 Oct 2026: self-review findings fixed (session restarted after the 16 Oct weekly limit)

The 16 Oct commits were never lost: the container survived and `story/a14c-families` was pushed on 21 Oct. Main (489
commits) merged in cleanly. An independent self-review found no blocking defect and five minor ones; each is checked
and fixed:

| Finding | Check | Fix | Test |
|---|---|---|---|
| A quoted (valid CSV, not byte-exact) old header passed the readers but was not migrated; 9-field rows under it read as `all`, so BF took the credit k (fail open) | reproduced by the reviewer's script | the run refuses any line 1 that is not one of the two exact headers; C2, C4 and A14c refuse a row with more fields than the header | `test_a_header_that_is_not_one_of_the_two_exact_lines_writes_nothing`, `test_a_row_with_more_fields_than_the_header_is_refused`, `test_a_family_row_under_the_old_header_is_refused_not_read_as_all` [C2, C4] |
| The skip used inclusive bounds with a 1e-9 slack; B2's BAD_PRICES is strict (a credit of exactly the width is bad there); and it was a second copy of the rule | read `simulator._entry_trial` | one `possible_value(legs, value)` in `structures.py`, used by B2's entry check and A14c (B2's exit check stays inclusive, as before) | `test_a_price_is_possible_only_strictly_inside_the_payoff_bounds` (SF and BF edges, credit side included); B2's four-leg regression and frozen-code tests still pass |
| `record(day)` without a structure silently dropped the factor row | read `margins.py` | a day without a structure refuses by name | `test_a_decision_record_on_a_day_needs_the_structure` |
| Docstrings still said one factor row (stress_run, stress_log, held_rise, the workflow) | read | rewritten per family | - |
| Test gaps: CRLF and missing last newline in the header change; per-family 30-day age; one approval for a fall in both families | - | tests added | `test_the_header_change_keeps_crlf_bytes_and_a_missing_last_newline` [2], `test_the_30_day_age_applies_to_each_family_s_own_row` [C2, C4], `test_one_owner_approval_applies_a_fall_in_both_families` |

**Added (lane 1, workflow):** `stress-factor.yml` gains an `approve_fall` dispatch input, checked as a 7-40 hex commit
(else one #fno-desk line and nothing written), passed as `--approve-fall`. Without it the first per-family run would
have to run outside Actions to cite the owner's approval.

Round 2 mutations, all 7 caught: strict bounds made inclusive (8 failed); each of the three extra-field refusals
removed (1 each); the exact-header refusal removed (1); the record's structure check removed (1); A14c's skip removed
(1).

**Note for the owner [strong]:** the weekly run of Sun 18 Oct worked (incremental, k 2.1 carried, data commit
1986afbf). After this merges, the next Sunday run is full (no family has a measured row yet; about 2-2.5 hours) and
holds any family result below 2.1 until the approved dispatch.

## After the PASS (orchestrator's order)

1. Merge with the full gates on the exact pushed tree.
2. Dispatch the full run with `--approve-fall` citing the owner's 16 Oct DESK_DECISIONS family rows (the orchestrator
   confirms before the run). Report each family's k and the holding that sets it. The global 2.1 stays in force for
   both families until their first own rows.

## Limits (said plainly)

- Prices on later held days are not bound-checked (the owner's rule names entries); an impossible price on a peak day
  shows in the evidence's peak column.
- I have not run the real archive with this code yet: the run reads about 1,680 Drive files (about 2 hours with 8
  downloads ahead; fewer structures now, so likely less) and must wait for the PASS.
