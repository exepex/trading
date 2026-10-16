# Response 236: R3, B0's registration code (criterion 8): claims (for judge G)

**Branch:** `story/r3-b0-registration` (code at `496e74fd`). **Text:** `docs/stories/R-factory.md`, "R3 addendum
(16 Oct 2026)" (judge 226 addendum 1 PASS, merged). **Lane:** 1.

| # | Claim | Evidence |
|---|---|---|
| 1 | B0 is experiment 1's P1 exactly, a measurement. | `playbook/b0-monthly-sc-v1.yaml`: SC, x1.02 / x0.98, widths 300-100 within Rs 10,000, monthly 30-45 days, exit at 21+ days, `entry_conditions: []`, `edge_family: measurement`. `python -m fno playbook check` parses it. |
| 2 | Its plan numbers are measured, not invented (strong). | `expected_range` -5,084 to +4,156: P1's 10th and 90th percentile trade net over 58 traded cycles (`results_challenge.json`). `expected_net_per_opportunity` -386: the clean -23,140 over 60 (`RESULTS.md`, impossible exits). `margin_per_lot` 67,595: SC 300 scan plus exposure, 14 Oct (`research/data/margins/margins.csv`). |
| 3 | B0 is registered by the desk, as allowed, and is never approved. | `playbook/registry.csv`: one row, `research`, `desk`, 2026-10-16 (written by `playbook set-status`). `tests/playbook/test_measurement.py`: B0 is not in `approved_on`. |
| 4 | **B0 is shadowed from Mon 19 Oct, but its first decision record is Mon 16 Nov 2026** (corrected, judge 233). | `status_on(day)` counts only rows dated before the day (`loader.py:50`), so the 16 Oct row first counts on 17 Oct. 17 and 18 Oct are a weekend, so from 19 Oct each Book 1 run opens B0's account. D2 records a shadow only on an opportunity (`evaluate.py:52-58`), and an opportunity is the first session inside the 30-45 day window (`opportunities.py` `_first_day_in_window`). November's expiry (23 Nov; 24 Nov is a holiday) opened its window on 9 Oct, before registration, so B0 misses it. December's (29 Dec) opens on Sat 14 Nov, so the first session in it is **16 Nov**. The first time exit is 8 Dec. Test: `test_b0_s_first_decision_is_on_16_nov_the_first_session_of_december_s_window` runs the real finder from 17 Oct to 30 Nov and finds exactly one opportunity day, 16 Nov (December). The 19 Oct test stays right: it checks `shadow_on` (the account opening), not a record. If the merge slips past 16 Oct, the row (on this unmerged branch) is re-dated to the merge day before merging. |
| 5 | One source for the label. | `fno/playbook/measurement.py` `is_measurement` reads `edge_family`. Only B0 is a measurement in the repository (test). |
| 6 | E6's title and both alerts carry `measurement` for a research version; other versions keep E6's bytes. | `tests/scorecard/test_measurement_alerts.py` covers the first loss, a second loss exactly at the cap (`<=`) with the escalation, the cumulative alert and its repeat on a later close day, and a day with both alerts (single-trade wording sent). The non-measurement alert and title strings are pinned. Mutations: dropping `trigger.text` fails 4 tests; breaking the escalation count fails 1. |
| 7 | Idea card and ledger row. | `research/ideas/B0.md`. Ledger trial 55: prospective, hypothesis `no`, "B0 measurement: never promoted", added through B4's `Ledger.register`. `tests/research/test_ledger_guard.py` pins each trial; it now runs to 55 and pins B0's row, as R2 and FT1 did. |
| 8 | Sizes and design. | New files: `measurement.py` (13 lines) and `measurement_alerts.py` (34 lines). `pauses.py` is at 143 lines. `PauseTrigger` gains `text` with a default `""`, so E6's other triggers are unchanged. |

## Builder self-review (quality rule 3)

Two independent review agents ran on the code diff, one for correctness and one for silent failures. Both found the
same two real issues, both now fixed:

| Finding | Action | Evidence |
|---|---|---|
| The measurement wording ("not paused") also applied if a measurement were ever approved to `paper`. The pause would then be reported as no pause. | FIXED: the measurement wording applies only at `research`. | `test_a_measurement_approved_to_paper_is_paused_with_e6_s_own_wording`. Mutation (status gate removed) fails it. |
| Two cap losses closing the same day: E6 sends one alert per version a day (`AutoPauser.apply`), and the first trigger had count 1, so the escalation was dropped. That is exactly the duplicate-fill case it exists for. | FIXED: the count is the number of cap losses closed on or before this trade's close day, so it no longer depends on position. That also fixes the order (by close day, not trade ID). | `test_two_cap_losses_closing_the_same_day_keep_the_escalation`. Mutation (position count) fails it. |
| `{cap:,.0f}` rounds a cap that is not a whole number. | KEPT | Every version's cap is a whole number of rupees; the text names B0's Rs 10,000. |
| `is_measurement` is an exact, case-sensitive match. | KEPT | `edge_family` is part of the rule fingerprint, so a registered version cannot change it silently. A future measurement is registered by hand with the documented value. |
| Nothing in code stops a measurement being approved to paper. | KEPT, as the text decided | Only the owner can make that change (`transitions.py:17`), and R3 says the label does not grant it. The wording fix above makes such a pause report correctly. |
| Trial 55 has no `protocol_commit`, so `require_registered` would refuse it if a research run named it. | KEPT | A measurement has no frozen protocol run (judge 233 note 4). Nothing calls the guard for a shadow. |
| `playbook check` prints no measurement label. | KEPT | That command lists statuses only; criterion 8 names E6's outputs, the tracker and the post-mortem. |

## Real output sample (quality rule 6)

Made by the committed code through E6's own scorecard run, in a pytest fixture (temporary account, fixture prices, no
live post). Fixture version `cand-c` was made a measurement. Its second loss closes on the same day that its
cumulative loss passes 3 x cap, so the single-trade wording is sent, with the escalation:

```
TITLE: cand-c-v1 (measurement) in shadow:cand-c-v1 (research)
ALERT: F&O paper desk: cand-c-v1 (measurement) shadow test, not paused: realised loss of Rs 10,000 or more (trade s1 in shadow:cand-c-v1 lost Rs 10,511.41, cap Rs 10,000.00); owner review or retirement required; no further promotion. It stays eligible for further hypothetical entries until the owner acts
ALERT: F&O paper desk: cand-c-v1 (measurement) shadow test, not paused: realised loss of Rs 10,000 or more (trade s2 in shadow:cand-c-v1 lost Rs 10,511.41, cap Rs 10,000.00); owner review or retirement required; no further promotion. It stays eligible for further hypothetical entries until the owner acts; loss 2 at or beyond the cap: possible simulator defect (fill or settlement path), check it before any strategy relies on that path
```

## Answer to judge 233 (FAIL on claims; code correct, 13/13 mutations caught)

| Finding | Answer | Evidence |
|---|---|---|
| Should-fix 1: first decision is 16 Nov, not 19 Oct | ACCEPT | Rechecked with the real finder (claim 4). Claim 4 and the owner effect are fixed, and a test pins 16 Nov. |
| Should-fix 2: rule-3 self-review missing | ACCEPT | Section above; its two real findings are fixed in code. |
| Note 1: "forward" should be "spot" in the R3 text | ACCEPT | Fixed in `R-factory.md` (P1 and D2 centre on spot). |
| Note 2: `expected_range` is a single-trade range, while E6 compares the mean | ACCEPT, documented | A comment in the version file says to restate it before B0 reaches 20 positions. Comments do not change the rule fingerprint (`playbook check` still gives 039a6e0733b1). |
| Note 3: 67,595 is initial margin, not C2's stressed margin | ACCEPT, documented | A comment in the version file. The `source` field is unchanged, since changing it would change the registered rule. |
| Note 4: empty `protocol_commit` | AGREE | No change. |

**Gates:** `pytest -q -n auto`: 6,936 passed; ruff, format, `check_imports` and `check_records` are clean. ruff, format, `check_imports` and `check_records` are clean.

**Owner effect (corrected):**
- From 19 Oct, each Book 1 run opens `shadow:b0-monthly-sc-v1` in Drive (once) and evaluates B0. No B0 record exists
  until **16 Nov**, its first opportunity. After that there is about one a month: one record on each cycle's first
  window session.
- Nothing fills it until part B (E8 part 1b).

**Known limits:** those in the R3 addendum (no G6 code yet; LR1 shows no strategy lines; a realised loss can pass the
cap).
