"""Story STR1 broken-code proof (JUDGE.md quality rule 4): plant one mutation per criterion, run its test, expect a
failure, restore the file. From the repo root: python research/2026-10-15-str1-samples/mutate.py [ids]."""

import pathlib
import subprocess
import sys

M = [
    (
        "1",
        "fno/research_engine/one_side.py",
        "return 1 if kind == OPTION_CALL else -1",
        "return -1 if kind == OPTION_CALL else 1",
        "tests/research_engine/test_one_side.py::test_each_code_builds_its_legs_from_the_atm_strike",
    ),
    (
        "2a",
        "fno/research_engine/structures.py",
        "        require_covered(legs)\n        return legs if",
        "        return legs if",
        "tests/research_engine/test_one_side.py::test_no_structure_can_return_a_naked_short_leg",
    ),
    (
        "2b",
        "fno/research_engine/cycle_costs.py",
        "        require_covered(legs)\n",
        "",
        "tests/research_engine/test_one_side.py::test_the_cost_model_refuses_to_price_a_naked_short_leg",
    ),
    (
        "3",
        "fno/research_engine/structures.py",
        "math.inf if upward > 0 else max(values)",
        "max(values)",
        "tests/research_engine/test_one_side.py::test_a_bought_call_can_be_worth_without_limit_and_a_bought_put_up_to_its_strike",
    ),
    (
        "4a",
        "fno/checks/validity_shapes.py",
        "(outer - inner) * _away(self.kind) != width",
        "False",
        "tests/checks/test_validity_shapes.py::test_wrong_legs_fail_the_shape",
    ),
    (
        "4b",
        "fno/checks/validity.py",
        'CheckResult("bounded_loss", not naked,',
        'CheckResult("bounded_loss", True,',
        "tests/checks/test_validity_shapes.py::test_bounded_loss_is_checked_from_the_legs_whatever_the_code_and_shape_rules",
    ),
    (
        "4c",
        "fno/checks/validity_shapes.py",
        'return "" if strike == expected else',
        'return "" if True else',
        "tests/checks/test_validity_anchor.py::test_a_trade_off_the_atm_anchor_fails_the_shape",
    ),
    (
        "5",
        "fno/checks/validity_money.py",
        "PAD = 1.0  #",
        "PAD = 1.01  #",
        "tests/checks/test_validity_shapes.py::test_a_correct_trade_of_each_one_side_structure_passes_c4",
    ),
    (
        "6",
        "fno/playbook/structure_spec.py",
        "min(values) < 0 if bought_only",
        "min(values) <= 0 if bought_only",
        "tests/playbook/test_one_side_codes.py::test_a_bought_only_code_may_list_width_0_the_atm_strike",
    ),
    (
        "7",
        "fno/composition.py",
        "        VerticalSpread(STRUCTURE_CALL_CREDIT_SPREAD, OPTION_CALL, SOLD),\n",
        "",
        "tests/playbook/test_one_side_codes.py::test_d2_builds_each_new_code_at_the_widest_width_within_the_cap",
    ),
    (
        "8a",
        "fno/nse_margins/job.py",
        "checked = [row for row in found.rows if self.check.covers(row.structure)]",
        "checked = list(found.rows)",
        "tests/nse_margins/test_one_side_rows.py::test_rows_of_uncovered_codes_are_printed_not_written_and_the_job_does_not_fail",
    ),
    (
        "8b",
        "fno/risk/margins.py",
        "if not (margin >= 0 if bought_only else margin > 0):",
        "if not margin > 0:",
        "tests/risk/test_bought_only.py::test_a_paid_up_long_option_needs_no_margin_initial_stressed_or_at_entry",
    ),
    (
        "8c",
        "fno/checks/validity_margin.py",
        "(per_lot == 0 and structure not in STRUCTURES_BOUGHT_ONLY)",
        "per_lot == 0",
        "tests/checks/test_validity_anchor.py::test_a_bought_option_with_a_zero_margin_row_passes_c4_end_to_end",
    ),
    (
        "8d",
        "fno/risk/inputs.py",
        "(self.width == 0 and not self.bought_only)",
        "self.width == 0",
        "tests/risk/test_bought_only.py::test_a_bought_only_structure_may_be_at_width_0",
    ),
    (
        "1b",
        "fno/research_engine/structures.py",
        "return nearest_strike(strikes, spot, tie_higher=False)",
        "return nearest_strike(strikes, spot, tie_higher=True)",
        "tests/research_engine/test_one_side.py tests/research_engine/test_structures.py",
    ),
    (
        "9a",
        "fno/research_engine/structures.py",
        "CONDOR_OFFSET = 0.02 ",
        "CONDOR_OFFSET = 0.03 ",
        "tests/research_engine/test_four_leg_regression.py tests/research_engine/test_structures_match_frozen.py",
    ),
    (
        "9b",
        "fno/research_engine/structures.py",
        "(0.0, *(leg.strike for leg in legs))",
        "(-500.0, *(leg.strike for leg in legs))",
        "tests/research_engine/test_structures_match_frozen.py tests/research_engine/test_one_side.py",
    ),
]
only = set(sys.argv[1:])
for crit, path, old, new, test in M:
    if only and crit not in only:
        continue
    p = pathlib.Path(path)
    text = p.read_text()
    assert text.count(old) == 1, (crit, path, old)
    p.write_text(text.replace(old, new))
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", *test.split()], capture_output=True, text=True)
        last = [line for line in r.stdout.splitlines() if line.strip()][-1]
        verdict = "FAILS (good)" if r.returncode else "PASSES (BAD)"
        print(f"{crit:3} {verdict} | {path}: {old.strip()[:60]!r} -> {new.strip()[:40]!r} | {last}")
    finally:
        p.write_text(text)
