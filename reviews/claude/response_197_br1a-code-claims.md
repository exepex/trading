# Response 197: BR1a code round, claims for judge A (lane 1)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/br1a-protocol`. Story: `docs/stories/BR-breadth.md`, BR1a
(text PASS: judge 186; ChatGPT review 121 ACCEPT, answered in response 183). The orchestrator gave GO for the code after
RM1's freezer change merged (RM1 is on main and merged into this branch).

## The outcome first: claims are POSTPONED

Each study ran once, in the story's order, on 2,058 bhavcopies (1,366 old format, 692 UDiFF) whose SHA-256 matched
the archive manifests.

| Study | Result | File |
|---|---|---|
| 1 | Agreement **96.0%** (22,364 of 23,296) < 97%, so the fixed fallback applies: 2024-01-01 to 2025-12-31. Primary **`trail60`** (0.1924; `cal60` 0.1931; `market` 0.1941). δ = 0.0038 | `research/breadth/studies/results/study1.json` |
| 2 | Worst: 2024, `market`/`trail60`, SD 0.0199, lag-1 0.254, inflated variance 0.000666 | `study2.json` |
| 3 | **No rate passes.** +d is within the limits at every rate. -d on the whole window fails at every rate (at 0.02: 0.092 / 0.082 / 0.136; at 0.005: 0.052 / 0.033 / 0.071, against 0.025 / 0.025 / 0.045) | `study3.json` |

The diagnostics, which change no rule, are in `studies/results/DIAGNOSTICS.md` (some evidence). The daily differences
are strongly skewed (crash days), and the two `market` pairs over-reject under -d (0.064 and 0.088 against 0.0067
per member). A valid BR1 test needs a new protocol version: the owner's decision, with a new judge and ChatGPT round.

## Criteria and their tests

| # | Claim | Test |
|---|---|---|
| 1 | `research/breadth/PROTOCOL.md` parses, is complete for BR1's 18 items, every item a proposal; the freezer refuses it | `tests/evaluation/test_breadth_protocol.py`: `..._complete_for_its_own_items...`, `..._refuses_the_breadth_protocol_while_any_item_is_a_proposal` |
| 2 | S1's tests unchanged (none edited); a decided BR1 fixture freezes to `research/breadth/FREEZE_v1.md` with its own ledger row (`breadth-protocol-v1`), no gate; verify finds a changed hashed file | `..._freezes_to_its_own_record_and_ledger_row_without_the_gate`, `test_verify_finds_a_hashed_breadth_file_changed...`; the suite test `test_the_suite_fails_when_a_frozen_breadth_target_changes` |
| 3 | No "beats all" wording in `claim_meaning`, `PROTOCOL.md` or the README | `test_no_breadth_text_words_a_claim_as_beating_all_baselines` |
| 4 | The outcome screen reads t+1 only; a replaced strike set is excluded, a crash keeping every strike is scored | `tests/research/test_breadth_studies.py::test_a_replaced_strike_set...` |
| 5 | Studies 1-2 from SHA-checked files; the look-count formula by hand | `run.py panel` verifies first; `test_the_look_counts_follow_the_formula_by_hand`; the legacy roll test |
| 6 | Study 3's machinery on a Gaussian AR(1) null, lag 0.3: its count equals the frozen test run on every path | `test_on_a_gaussian_ar1_null_of_lag_0_3...`, `test_the_bootstrap_shortcut_gives_the_same_decisions...`, `test_false_futility_counts...` |
| 6b | Review 121: the same block starts for all members and the primary's loss; centring within the tested population | `test_every_series_of_a_path_uses_the_same_block_starts`, `test_each_null_series_is_centred_within_the_population_tested` |
| 7 | The single loop writes every rate tried, per sign, per population; a rate failing only for -d is skipped | `study3.json`; `test_the_loop_skips_a_rate_that_fails_only_for_minus_d` |
| 8 | `evaluation freeze --protocol breadth` refuses undecided, freezes decided; the default is `evaluation` | `test_the_freeze_command_takes_protocol_breadth_and_defaults_to_s1` |
| 9 | The owner's wording in `PROTOCOL.md` and `research/breadth/README.md` | `test_the_owners_wording_appears_in_the_protocol_and_the_readme` |
| 10 | No file over 350 lines; names in `fno/constants.py`; gates | `ruff`, `ruff format`, `check_imports`, `pytest -n auto`: 6,561 passed |

## The freezer change (scope 3), as agreed with S1, RM1 and F9

- New `fno/evaluation/definition.py`: a `ProtocolDefinition` (file, required items, freeze-record path and wording,
  ledger row, `requires_gate`). `EVALUATION` is S1's, the default everywhere.
- New `fno/evaluation/breadth.py`: `BREADTH` (`requires_gate=False`). Only `wiring.py` maps the names
  (`PROTOCOL_EVALUATION`, `PROTOCOL_BREADTH` in `fno/constants.py`) to definitions.
- `freeze.py`, `order.verify` and `cli.py` read the definition. `protocol.py`, `completeness.py`, `gate.py` and
  `review_dates.py` are untouched; `parse_protocol` and `PROTOCOL_FILE` keep their names. `_require_gate` runs only
  when the definition asks (S1). S1's record, ledger row and messages are byte-for-byte the same.

## Deviations from the story text, for the judge to accept or reject

1. **Item key `target`, not `target_t1`.** S1's parser takes `[a-z_]+` keys only. Widening it would edit
   `protocol.py`, which S1's `frozen_files` lists, for a name. The item's title is "T1 target".
2. **The sign of d.** The story writes d = primary minus family; the code and `PROTOCOL.md` use v4's sign (family
   minus primary, negative favours the family), because `confirmatory_test` is one-sided in that direction. The claim
   is the same.
3. **The fallback window applies to the inputs too.** After study 1 failed its gate, the panel was cut to 2024-2025
   before the trailing baselines were built. So no old-format row enters any baseline, and the first 60 sessions of
   2024 are history only: 2024 has 189 scored sessions, 2025 has 248 (437 in all). The other reading (score 2024-2025
   but let Dec 2023's old-format rows feed `trail60` and `cal60`) would mix in the data study 1 had just failed. I
   chose this reading before the run; it is stated in `primary_baseline_rule`.
4. **The whole window (437 days) is shorter than look 2 (495-642 days).** The circular bootstrap wraps. The
   diagnostics show the failure is not caused by this: 300-day paths still give 0.110 / 0.085 under -d.
5. **No rolling real windows** were possible for the same reason (`windows: 0` in `study3.json`).

## What the judge can re-run

- The study tests and the freezer tests: `python -m pytest -q tests/research/test_breadth_studies.py tests/evaluation`.
- The studies: fetch both formats with `research/2026-10-15-breadth-sizing/fetch.py udiff|legacy`, then
  `python -I research/breadth/studies/run.py panel <legacy> <udiff> <scratch>` and `... studies <scratch> <out>`.
  The other-seed check: change `SEED` in `brstudy/study3.py` and compare within 2 SE (SE at 2,000 paths is about
  0.006 near 0.08).
- `python -m fno evaluation check --protocol breadth` prints "complete"; S1's `check` output is unchanged.

## A note for S1's owner (not this story's change)

S1's `frozen_files` lists `protocol.py` and `completeness.py` but not `freeze.py` or the new `definition.py`.
`requires_gate=True` for S1 now lives in `definition.py`, as the gate call lived in the unfrozen `freeze.py` before.
Nothing is weaker than before, but S1's owner may want both listed (reasoning only).
