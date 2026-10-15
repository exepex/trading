"""Story STR1b-1 broken-code proof (JUDGE.md quality rule 4): plant one mutation per criterion, run its test, expect a
failure, restore the file. From the repo root: python research/2026-10-15-str1b-samples/mutate.py [ids]."""

import pathlib
import subprocess
import sys

M = [
    (
        "1a",
        "fno/risk/margins.py",
        "return span if self.span_cap is None else max(broker, min(span, self.span_cap))",
        "return span",
        "tests/risk/test_capital.py::test_a_bought_option_or_debit_spread_carries_no_stress_reserve",
    ),
    (
        "1b",
        "fno/risk/margins.py",
        "else max(broker, min(span, self.span_cap))",
        "else min(span, self.span_cap)",
        "tests/risk/test_capital.py::test_the_ccs_100_split_by_hand",
    ),
    (
        "1c",
        "fno/risk/capital.py",
        "    if structure not in STRUCTURES_ONE_SIDE:\n        return None\n",
        "",
        "tests/risk/test_capital.py::test_four_leg_margins_are_unchanged_on_every_real_row",
    ),
    (
        "1d",
        "fno/checks/validity_margin.py",
        "capped = span if cap is None else max(max(0.0, scan - nov), min(span, cap))",
        "capped = span",
        "tests/checks/test_validity_capital.py::test_c4_s_stressed_margin_equals_c2_s_on_every_real_row",
    ),
    (
        "2",
        "fno/risk/rules.py",
        '"capital_tied": broker_margin + premium_paid,',
        '"capital_tied": broker_margin + premium_paid + reserve,',
        "tests/risk/test_capital.py::test_capital_tied_is_broker_margin_plus_premium_and_the_reserve_is_apart",
    ),
    (
        "2b",
        "fno/scoreboard/entry_facts.py",
        'capital.get("capital_tied"), capital.get("stress_reserve")',
        'capital.get("total_funds"), capital.get("stress_reserve")',
        "tests/scoreboard/test_capital_figure.py",
    ),
    (
        "3",
        "fno/nse_margins/broker_approvals.py",
        "return approval is not None and approval.passed_on <= day",
        "return approval is not None and approval.passed_on < day",
        "tests/nse_margins/test_broker_approvals.py::test_a_code_is_written_from_its_own_day_on_and_printed_the_day_before",
    ),
    (
        "3b",
        "fno/nse_margins/broker_approvals.py",
        "    if not source or not isinstance(passed_on, date):",
        "    if False:",
        "tests/nse_margins/test_broker_approvals.py::test_anything_but_the_code_map_is_refused",
    ),
    (
        "4",
        "fno/checks/validity_margin.py",
        '"margin_row": margin_row(rows, _terms(proposal), day, settings)',
        '"margin_row": {}',
        "tests/checks/test_validity_capital.py::test_c4_names_the_margin_row_it_used",
    ),
    (
        "5a",
        "fno/playbook/activation.py",
        "USE_SHADOW if registered else None",
        "None",
        "tests/playbook/test_activation_gate.py",
    ),
    (
        "5b",
        "fno/playbook/loader.py",
        "        if blocked:\n",
        "        if False:\n",
        "tests/playbook/test_activation_gate.py",
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
