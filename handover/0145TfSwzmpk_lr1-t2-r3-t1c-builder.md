# Handover: builder session 0145TfSwzmpk6MBrH92f5h4G (LR1, T2/T3, M2, R3, T1c)

Written 21 Oct 2026 on `story/t1c-card-weather`. Every commit below is on GitHub; nothing is left only in the
container.

## (a) Identity

- **Session:** session_0145TfSwzmpk6MBrH92f5h4G. Role: builder. Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH.
- **Owned:**
  - LR1 (weekly post-mortem) and `fno/advocate/` (the devil's advocate port);
  - T2 and T3 (rule checks and AI objections on the daily card), and T1c (the card's weather);
  - M2 (the weather DANGER alert);
  - R3 (first forward shadows, including B0).
- **Branches** (head, state):
  - `story/lr1-weekly-postmortem` b715d6ee: merged
  - `story/t2-t3-advocate` 38699fee: merged (T2)
  - `story/m2-weather-alerts` f52207f3: merged (M2 text only)
  - `story/r3-forward-shadows` d10f2e91: merged (R3 text)
  - `story/r3-shadow-accounts` f5cf9b97: merged (R3 code part A)
  - `story/r3-part-b` 7f94dbdf: merged (R3 addendum text: B0 and part B)
  - `story/r3-b0-registration` 89fcbbd5: merged (B0's registration code)
  - `story/t1c-card-weather` **620d060a: NOT merged** (T1c text PASSed; code WIP)

## (b) Done and merged to main

- **LR1:** merged 46b76756, judge 167 addendum 3 PASS. The owner's routine and 2 secrets are still pending
  (`docs/stories/LR1-owner-checklist.md`).
- **T2:** merged 2418ccfc, judge 182 addenda 1-2 PASS.
- **M2 text:** judge 202 PASS. Its code waits for O1's `weather_alert` step.
- **R3 text:** judge 208 addendum 1 PASS.
- **R3 code part A:**
  - merged 0d796a1c, judge 210 addendum 2 PASS; ChatGPT review 132 answered by response 229;
  - shadow accounts are opened before D2, each shadow is valued on its own terms, and Book 1's readers filter by
    mode;
  - `shadow_<id>.json` record names plus `RecordClash`;
  - Test B's path.
- **R3 addendum text** (B0 and part B): judge 226 addendum 1 PASS.
- **B0's registration:**
  - judges 233 addendum 1 (G) and 229 addendum 3 (A, closure exemption) PASS; merged on 16 Oct;
  - `playbook/b0-monthly-sc-v1.yaml`, research by desk on 16 Oct; ledger trial 55; `research/ideas/B0.md`;
  - `fno/playbook/measurement.py`; `fno/scorecard/measurement_alerts.py`.
  - **B0's first decision record is due Mon 16 Nov 2026**, the first session in December's window. Its first time
    exit is 8 Dec.

## (c) Done but not merged

- **T1c story text:** `story/t1c-card-weather`, judge 401 PASS at 2538c8cd (Judge E, session_01HkXMVPDEqVsmJZtghFrGzM).
  Claims are in response 275. The text has not been merged separately. Merge it together with the code.

## (d) In progress: T1c code (WIP commit 620d060a)

- **Built:**
  - `fno/cards/recorded_weather.py` (new): `RecordedWeather` reads M1's committed record through `CommittedRecords`,
    with the path from `WeatherRecords.path`;
  - `fno/cards/wiring.py` `_weather()`;
  - `fno/cards/weather.py` deleted (`PendingWeather`);
  - tests: `tests/cards/test_recorded_weather.py` (12, on the real 14 Oct record); `fakes.py` and `test_card.py`
    updated;
  - O11's strict-xfail marker for T1c turned into a real check (`tests/e2e_acceptance/test_expected_missing.py`).
  - Judge 401's minor is covered: an older record without `v0_status` shows "no reason recorded".
- **Checked:**
  - cards and e2e: 100 passed, 17 xfailed; ruff and format clean;
  - 3 mutations caught (day check, v0 not scored, RED line);
  - the dry run `python -m fno card daily --on 2026-10-14` prints "Weather: GREEN (weather_vix_v1, not yet proven:
    ...) (back-fill, exploratory)" / "Chance of a 2% NIFTY move: next session 2% (base rate 3%); within 5 sessions
    9% (base rate 10%)" / "Checklist v0: AMBER".
- **Not done:**
  1. Merge main in and run the full suite (`-n auto`), plus `check_numbers` on main.
  2. Rule-3 self-review. Both review agents were stopped by the weekly limit (16 Oct) before reporting, so rerun them
     (correctness, silent failures).
  3. The code claims file: claim a number with `tools/claim_number.py claude-response t1c-card-weather-code
     --session <id>`. Include the rule-6 sample above, the mutations and the self-review.
  4. Send it to Judge E, then to the orchestrator for the merge.
- **Uncommitted:** nothing.

## (e) Reviews and judging (as a reviewer)

- **G8 cohort change:** reviewed and agreed with the A16/G8 builder (they changed LR1's `forecast_section.py`).
- **R1b's rewrite of R3's registration step 1** (story/r1b-screens f94a4b92): agreed, with a step 3 clause added
  ("only for a card whose G1 screen passed, or a measurement").

## (f) Agreements and open questions

- **E8 (session 01H1CmuW):**
  - E8 fills pending orders of every account, and R3 writes the shadow orders plus the terms lookup;
  - R3 part B changes `_fills` to `recorded_terms(root, account, BOOK1_RULES if account.startswith(SHADOW_PREFIX)
    else None)`;
  - `book1_orders._stored_action` and `recorded_c4` must take the mode (part B criterion 11); E8 adds no caller.
- **R1 (screens lead, 01XFXpbk):**
  - R1 owns CostWall and the registered-shadow list; R3 owns the shadow records and the closed-trade reader; the
    tracker joins them;
  - R1c's `factory freeze` enforces "G1 passed and G3 row";
  - R1c reads nets through E6's `strategy_records`, and should report the miss share from E6b's counter;
  - measurements are excluded through `is_measurement`.
- **Judge A:** move `fno/playbook/measurement.py` from S1's closure exemption into `frozen_files` in the same change
  that makes Test B count by it (R3 part B, or R1c if R1c's Holm decides a figure first).
- **E6b (0134MoC6):** R3 made both edits to `report.py` and `pauses.py`; E6b changes only the entries line. The
  non-measurement bytes are pinned by tests.
- **LR3 (01SFDjjZ):** drift files in `fno/learning/` with their own `drift_wiring.py`. LR1 adds one
  `drift_alarms(period)` call when LR3 lands.
- **LM1 (01XFXpbk):** a future card line (uptime and alert count) from LM1's public per-mark rows through LM1's
  reader. A day with no rows shows "monitor not run".
- **F2 (01WSMMv5):** imports `number_tokens`, `form_failure` and `number_failure` from `fno/advocate/numbers.py`,
  unchanged. Warn them before any change.
- **M1 (013xqaNT):** T1c reads committed records. They will warn before moving them to Drive (O9).
- **Parked by the orchestrator:** R3 part B until E8 part 1b merges; T3 until a version is approved to paper.

## (g) Risks and gaps a successor must not miss

- R3 part B's merge gate is criterion 10: with/without isolation after real shadow fills, covering C2, C4, E6, S2, S3
  and Book 1's account bytes. Criterion 12: Test B readiness from resolved closed trades after the E2c download,
  never `Path.exists()`.
- A realised B0 loss can pass Rs 10,000 (exit spread wider than the pad). E6 alerts with the measurement wording, and
  escalates from the second loss.
- B0's `expected_range` is a single-trade range, while E6's review compares the mean. Restate it before B0 reaches 20
  positions.
- T1c Known limit: until `weather capture` runs live daily, the card shows "no reading" plus "no new trades".
- M2 code waits for O1. T3 and T2b wait for T1's trade fields.

## (h) First three actions for the successor

1. On `story/t1c-card-weather`: merge `origin/main`, then run `python -m pytest -q -n auto`, `ruff check fno tests
   tools`, `ruff format --check`, `python tools/check_imports.py` and `python tools/check_records.py`.
2. Run the two rule-3 review agents on `git diff origin/main -- fno tests`, fix what they find, claim a response
   number, and write the T1c code claims (sample, mutations, self-review).
3. Send it to Judge E (session_01HkXMVPDEqVsmJZtghFrGzM), copying the orchestrator. Then watch E8 part 1b's merge to
   start R3 part B.
