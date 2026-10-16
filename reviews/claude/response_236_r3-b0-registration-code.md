# Response 236: R3, B0's registration code (criterion 8): claims (for judge G)

**Branch:** `story/r3-b0-registration` (code at `496e74fd`). **Text:** `docs/stories/R-factory.md`, "R3 addendum
(16 Oct 2026)" (judge 226 addendum 1 PASS, merged). **Lane:** 1.

| # | Claim | Evidence |
|---|---|---|
| 1 | B0 is experiment 1's P1 exactly, a measurement. | `playbook/b0-monthly-sc-v1.yaml`: SC, x1.02 / x0.98, widths 300-100 within Rs 10,000, monthly 30-45 days, exit at 21+ days, `entry_conditions: []`, `edge_family: measurement`. `python -m fno playbook check` parses it. |
| 2 | Its plan numbers are measured, not invented (strong). | `expected_range` -5,084 to +4,156: P1's 10th and 90th percentile trade net over 58 traded cycles (`results_challenge.json`). `expected_net_per_opportunity` -386: the clean -23,140 over 60 (`RESULTS.md`, impossible exits). `margin_per_lot` 67,595: SC 300 scan plus exposure, 14 Oct (`research/data/margins/margins.csv`). |
| 3 | B0 is registered by the desk, as allowed, and is never approved. | `playbook/registry.csv`: one row, `research`, `desk`, 2026-10-16 (written by `playbook set-status`). `tests/playbook/test_measurement.py`: B0 is not in `approved_on`. |
| 4 | **The first shadow decision is recorded on Mon 19 Oct 2026**, if this merges before that day's 15:12 decision. | `status_on(day)` counts rows dated **before** the day (`loader.py:50`), so the 16 Oct row first counts on 17 Oct. 17 and 18 Oct are not sessions (NSE calendar: Sat, Sun). 19 Oct is the next session; 20 Oct is a holiday. The test checks that B0 is not shadowed on 16 Oct and is on 19 Oct. If the merge slips past 16 Oct, the row (on this unmerged branch) is re-dated to the merge day before merging, so the registry never claims a registration earlier than its commit. |
| 5 | One source for the label. | `fno/playbook/measurement.py` `is_measurement` reads `edge_family`. Only B0 is a measurement in the repository (test). |
| 6 | E6's title and both alerts carry `measurement`; other versions keep E6's bytes. | `tests/scorecard/test_measurement_alerts.py` covers the first loss, a second loss exactly at the cap (`<=`) with the escalation, the cumulative alert and its repeat on a later close day, and a day with both alerts (single-trade wording sent). The non-measurement alert and title strings are pinned. Mutations: dropping `trigger.text` fails 4 tests; breaking the escalation count fails 1. |
| 7 | Idea card and ledger row. | `research/ideas/B0.md`. Ledger trial 55: prospective, hypothesis `no`, "B0 measurement: never promoted", added through B4's `Ledger.register`. `tests/research/test_ledger_guard.py` pins each trial; it now runs to 55 and pins B0's row, as R2 and FT1 did. |
| 8 | Sizes and design. | New files: `measurement.py` (13 lines) and `measurement_alerts.py` (34 lines). `pauses.py` is at 139 lines. `PauseTrigger` gains `text` with a default `""`, so E6's other triggers are unchanged. |

**Gates:** `pytest -q -n auto`: 6,933 passed. ruff, format, `check_imports` and `check_records` are clean.

**Owner effect:** from its first shadow session, Book 1's run opens `shadow:b0-monthly-sc-v1` in Drive and records B0's
decision daily. Nothing fills it until part B (E8 part 1b).

**Known limits:** those in the R3 addendum (no G6 code yet; LR1 shows no strategy lines; a realised loss can pass the
cap).
