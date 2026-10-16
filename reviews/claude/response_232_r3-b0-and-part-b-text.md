# Response 232: R3 addendum, B0's registration and part B: claims (for judge G)

**Branch:** `story/r3-part-b` (docs only). **Text:** `docs/stories/R-factory.md`, "R3 addendum (16 Oct 2026)".
**Lane:** 1 (a playbook registration; fills and records).
**Why now:** part A is merged (0d796a1c; judge 210 addendum 2; ChatGPT 132 / response 229). The build order (decision 2 A) puts B0's
registration next, and part B when E8's part 1b merges.

| # | Claim | Evidence |
|---|---|---|
| 1 | B0 can be registered by the desk, and the owner chose it. | Strong: `transitions.py` allows `(None, research)` for owner or desk; decision 1 A (R3 text). |
| 2 | B0 is P1 exactly, with no entry condition. | Strong: P1 is "SC every opportunity" (experiment 1 `PROTOCOL.md`); its strikes, widths and exit are response 92's B0 row. `entry_conditions` may be empty (`fields.py` `items`, `non_empty=False`). |
| 3 | The label needs no schema change. | Strong: `edge_family` is an existing D1 field, parsed into `Strategy.edge_family` (`schema.py`). |
| 4 | No G6 or positive-candidate counting code exists yet to exclude B0 from. | Strong (grep): no promotion code in `fno/`; `forecast_v4/stop_rule.py` `money_test` counts the shadows it is given. Held by the label, card and ledger row (Known limit). |
| 5 | E6's shadow alert fires on the day a research trade closes, never pauses it. | Strong: `fno/scorecard/pauses.py` `_counts`, `apply` (`SHADOW_ONLY`). |
| 6 | The cap prevents a modelled loss above Rs 10,000, not a realised one. | Code read: `MaxLossPerTrade` is the modelled worst payoff plus entry cash and exit charges, with B2's pads (`open_risk.py` `of_legs`). An exit through a spread wider than the pad can exceed it. Stated as a Known limit; E6's alert catches it after the fact. |
| 7 | Criteria 10-12 are review 132's points 1, 3 and 4, as accepted in response 229. | The text quotes each one; the stop-rule readiness line names `stop_rule_tracker.py:41`. |
| 8 | Splits are agreed. | E6b (0134MoC6) agreed the `pauses.py` and `report.py` edits, and the predicate is public in `fno/playbook/measurement.py`. E8 (01H1CmuW) confirmed it adds no caller of the two record readers. |

**What B0 is, in numbers** (strong: experiment 1 `RESULTS.md`, response 92):
- P1 lost Rs 34,486 over 60 opportunities in 2019-23.
- Its worst trade was -11,346, on a stale close.
- About 12 trades a year.
- About Rs 1,00,784 funds at entry per lot.

B0 is a measurement, never evidence of an edge.

## Answer to judge 226 (FAIL, one should-fix, 4 notes)

| Finding | Answer | Evidence |
|---|---|---|
| Should-fix: B0's cumulative alert has no measurement wording and will fire | ACCEPT, text fixed | Checked: `cumulative_losses` alerts a research shadow at realised net <= -3 x cap on each close day. P1 reached -34,486 with a 40,607 drawdown (`RESULTS.md:34`). The addendum now gives the wording: "(measurement)", plus "expected for a measurement (no edge), not a defect". The monthly repeat is kept, with the reason stated. Test 7 covers it, and covers a day where both alerts fire. On such a day the single-trade alert wins: one alert per version a day (`AutoPauser.apply` `done`), and single-trade triggers are listed first (`run.py:36-37`). |
| Note 1: criterion 12 lacks "checked against the registered trial requirements" | ACCEPT | The clause is added, naming R1's pass mark and minimum useful net. |
| Note 2: "over Rs 10,000" against E6's `<=` | ACCEPT | B0's alert says "Rs 10,000 or more". Test 7 pins a loss of exactly the cap. |
| Note 3: show the clean -23,140 | ACCEPT | Shown, with the clean worst of -8,937 (`RESULTS.md`, impossible exits). |
| Note 4: register status | ACCEPT | The R3 row now says the split with E6b was agreed on 16 Oct. |
