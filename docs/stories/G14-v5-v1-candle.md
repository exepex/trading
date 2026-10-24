# G14. v5 side by side: V1's forecasters started now on the stored candle RV history

**Repository:** trading. **Owner:** session_011SsKz428ekYzMEeFMRphfA (orchestrator, 24 Oct; earlier the R2/G7 builder
0185gR5DmoDh2zBAvgRU4CEB, out of reach). **Lane 1** (forecast records),
one judge: Judge J (session_01Qg4Gxun1NvGRrtS9C68Dc1); judge D for the O1 parts. **Status:** text PASS (judge
497.1, round 2); amendment 1 (v4 signed off, the v4 freeze, W8) round 2 to Judge J (judge 596 FAIL
round 1); code after its PASS and `FREEZE_v4.md` on `main`.

**Description:** As the quantitative modeller, I want v4's five V1 forecasters (trailing, EWMA, HAR daily, HAR
intraday and the close blend) run every session from now on, on the candle-based intraday RV history A16b already
stored (2020-2026), so that V1 gets a live, scored record about four weeks before v4's own V1 can start.

**Context and why:**
- The owner's decision (orchestrator, 23 Oct 2026). v4's V1 starts only after 20 usable live A16 sessions (protocol
  v4 line 57; `fno/forecast_v4_rules/capture.py`, `V1_START_SESSIONS = 20`).
- At 22 Oct's 14:11 run, A16 had 3 live rows, one of them void (16 Oct), so 2 were usable. After 22 Oct's own row
  (15:31) it has 4 rows, 3 usable. That is about 17 more sessions: v4's V1 starts around 18 November.
- The candle history is `exposed` in `research/DATA_SPEND.md` (row "NIFTY intraday realised variance (A16b
  candles)"). Fitting on it spends no fresh data. Every score here comes from live sessions after the start date.

**Said plainly:**
- V1 is not provable in useful time under v4's rules: judge 128's measured noise makes it effectively unreachable.
  This candidate gives an earlier, honest, scored track record. It does not give proof.
- It adds one candidate to the trial count that the Innovation Lab's luck correction must pay for.

## Scope

- **In:**
  - The five V1 forecasters on a spliced intraday RV history (below).
  - Their daily live records in their own folder, with every record labelled with its input measure.
  - A measure-gap table: candle against live RV on every session that has both.
  - A scoring report against the same live A16 target as v4's V1, with v4's QLIKE.
  - One O1 daily step, `forecasts_v5_v1`, live from its own `daily.live_from` date.
  - An R1 measurement card and its ledger trial.
- **Out:**
  - Any change to a v4 file or a v4 output. G7's pure baselines are imported, never edited or copied.
  - Membership of v4's family. This candidate is never a v4 member and never enters a v4 look.
  - Any claim. It is a measurement: never screened, never promoted (R1 `measurement: yes`).
  - A back-fill of forecasts. History is used only as model input; the first scored forecast is the first live day.

## Design

### The input history

The question is what the forecast for day `d` may read, point in time, at `d`'s 14:30 cutoff.

- **Measured, 23 Oct:** a candle RV row for session `d-1` is first seen on `d` at about 15:33 IST (A16b's catch-up,
  for example 21 Oct's row was first seen at 2026-10-22T10:03:11Z). That is after `d`'s 14:30 cutoff.
- A live A16 row for `d-1` is first seen on `d-1` at about 15:31 IST.
- So a candle-only history always lacks the latest session, and V1's trailing forecaster ("the previous session's RV")
  would become "the RV of two sessions ago".
- **The rule: one spliced series, candle first, point in time** (orchestrator's ruling, 23 Oct; judge 497
  should-fix 3). For each session `s` before `d`:
  - the candle row for `s`, when it is `ok` and was first seen before `d`'s cutoff;
  - otherwise the live A16 row for `s`, when it is `ok` and was first seen before `d`'s cutoff;
  - otherwise `s` is missing.
- A void live row does not block a later candle row. A candle measurement is a measurement of the same session, not a
  fill. "Void stays missing" applies to a live A16 row only when no candle row has been seen yet.
- **Worked example: 16 Oct.** Its live row is void. Its candle row is `ok` (5.82224e-5), first seen 19 Oct 15:33 IST.
  - For `d` = 19 Oct (cutoff 14:30), 16 Oct is missing.
  - 20 Oct was a holiday.
  - For every `d` from 21 Oct on, 16 Oct is 5.82224e-5, source `candle`.
- Every value keeps its source (`candle` or `live`). The record states how many of the inputs each source gave, so a
  measure mix is never hidden.
- Rejected alternative: candle only, with a one-session lag. It is a different forecaster from v4's, and it is weaker
  for a next-session question. The judge may require it instead; the code keeps the source as one strategy.

### The measure gap (said in every record and report)

- **Label:** "candle RV (15m bars) vs live quote RV".
- The candle RV (`rv-candle-15m-v1`) uses 15-minute index candles: the first bar's open and 25 bar closes.
- The live A16 RV (`rv-quote-15m-v1`) uses quote snapshots at the 15-minute marks, filled from one-minute candle
  closes for 25 of its 26 slots (`basis_counts candle_1m_close:25;candle_1m_open:1` on 21 Oct).
- **Measured on the two sessions with both (some evidence, n = 2):**
  - 19 Oct: live 1.5336e-4 against candle 1.4760e-4, live 3.9% higher;
  - 21 Oct: live 1.1426e-4 against candle 1.1392e-4, live 0.3% higher.
- The report prints this table, growing by one row a day.

### The forecasters (imported from G7, unchanged)

| Forecaster | Formula (G7, `fno/forecast_v4_rules/`) | Input it uses here |
|---|---|---|
| `v5c_trailing` | previous scored session's RV | always the live A16 row of `d-1` (a candle row for `d-1` is never seen before `d`'s cutoff), so it equals v4's trailing on the same row: a labelled control |
| `v5c_ewma_094` | EWMA lambda 0.94 of close-proxy RV | closes, as v4 |
| `v5c_har_daily` | HAR on close-proxy RV, monthly refit | closes, as v4 |
| `v5c_har_intraday` | HAR on intraday RV, at least 250 sessions, up to 750 | the spliced series (eligible from day 1: 1,665 usable of 1,684 candle sessions, 2020-2026) |
| `v5c_close_blend` | mean of HAR daily and EWMA | closes, as v4 |

- Three of the five use closes only. They are v4's own formulas without v4's 20-session start gate, so their values
  will equal what v4's V1 rows will show once V1 starts.
- They are kept because the owner asked for the five, and they are the like-for-like baselines for the two that use
  intraday RV. With `v5c_trailing` (above), four of the five are controls. Only `v5c_har_intraday` reads the candle
  history, so it alone tests the candle input.

### Records, step, report

- `fno/forecast_v5_v1/` (new package, every file under 350 lines):
  - `history.py`: the splice;
  - `capture.py`: one day's five values;
  - `records.py`: G7's record format plus `input_measure`, `input_sources` and `platform` columns (`platform`:
    Python, numpy and libc versions of the capture; judge 508's glibc finding, orchestrator 23 Oct);
  - `gap.py`: the measure-gap table;
  - `report.py`: QLIKE per forecaster against the live A16 target, the gap table and void counts;
  - `wiring.py` and `cli.py`: `python -m fno forecast-v5-v1 capture`, `report`.
- Records go to `research/forecasts/v5/v1_candle/<forecaster>/v1_rv_next_session.csv`, live rows only, write-once,
  each with the method hash of this package's files.
- O1 step `forecasts_v5_v1`: right after `forecasts_v4`, the same 14:30 cutoff. It is only a `LiveFrom` row in
  `fno/daily/wiring.py` and `DAILY_RUN_STEPS`, agreed with the O1 builder first.
- **Two merges** (superseded by amendment 1, section 3: the order of merges; judge 497 should-fix 2; the
  orchestrator's ruling, 23 Oct; the decision row "its daily step merged
  only after the v4 sign-off"):
  - The package, its records format, its card and its freeze record merge once judged.
  - The O1 step (`DAILY_RUN_STEPS`, `fno/daily/wiring.py`, `config.yaml`, the step-list tests) is a separate commit,
    merged only after the owner signs v4, with its `daily.live_from` date. A `not_live` row before then is not
    enough.
- **Agreed with the O1 builder (session_014zYLf18PgCzR7YoHs1X5Dp, 23 Oct).** I add the step on its own branch,
  `story/g14-o1-step`, cut from `main` after the package has merged (judge 497.1 minor), so a package merge can never
  carry it early. It changes `fno/daily/wiring.py`, `fno/constants_operations.py`, `config.yaml` and
  `tests/daily/test_steps.py`. Terms:
  - Wiring: copy `forecasts_v4`'s pattern exactly, with the command and pathspecs as named constants beside
    `FORECASTS_V4`, and the name added to `LIVE_STEPS`. Any `receipts/` folder the capture writes goes in the
    pathspecs too.
  - The 14:30 refusal exits non-zero, so the run records it as refused and alerts.
  - These tests change with the step list: `tests/daily/test_day_run.py`, `tests/daily/test_steps.py`,
    `tests/health/test_desk_and_data_checks.py` and O11's `tests/e2e_acceptance/replay.py`. The whole e2e folder is
    run.
  - The committed run log holds status only (`command:ok`); values live in this story's own records.
  - Judge D judges the O1 parts. The branch is never merged between 14:00 and 16:15 IST.
  - Timing: v4 ran 14:11:25-14:11:27 on 22 Oct, so this step starts at about 14:12.
- Freeze: before its first live day, a short `FREEZE_v5_v1.md` hashes every file on G14's input path, with a
  `Frozen on:` line, the same rule as v4 (amended in round 2, judge 596 S2; amendment 1, section 3b).

### Registration (R1)

- A measurement card, `research/ideas/CARD_V5V1.md` (ledger trial 100), with a `factory` block (`measurement: yes`,
  `hypothesis: no`, question `v1-next-session-rv`). Moved from `research/forecasts/v5/` when built: `factory register`
  finds a card not yet in the ledger only in `research/ideas/` (`fno/factory/card_paths.py`, `card_path`), and a
  factory change is out of this story's scope.
- `python -m fno factory register` writes its ledger trial and gate-log row in the same commit as the card, before
  any code runs.

## Amendment 1 (24 Oct 2026): v4 signed off, the v4 freeze, W8

For Judge J. Text only; no code exists. What changes and why, each with its source.

**1. The gates tied to "after v4 sign-off" are lifted.** The owner signed off protocol v4 on 24 Oct (DESK_DECISIONS
"The owner signs off protocol v4 ...": "Consider v4 sign off. So activate all the features which were waiting for v4
sign off"), and that row names "G14's v5 side-by-side step (built and judged first)" among the held items to switch
on. The earlier row "Merge everything to main; nothing waits for the v4 sign-off" (24 Oct) removes the other
"after sign-off" gates. "Code after v4's piece 4" is replaced by section 3 below.

**2. Criterion 2 still holds, against `FREEZE_v4.md`.** The freeze is being written now (story/v4-freeze, another
builder), lands once G7b's live V2 baseline code is on `main` (target Sun 25 Oct), `Frozen on:` 25 Oct, counted from
Mon 26 Oct. G14 adds only new paths: `fno/forecast_v5_v1/` and `research/forecasts/v5/` match none of
`BYTE_CHECKED_GLOBS` (`fno/forecast_v4/*.py`, `fno/forecast_v4_rules/*.py`, `fno/forecast_scoring/v4/*.py`,
`research/forecasts/v4_*`, ...) nor M1's method files, so a correct G14 diff can never touch a v4-hashed file. The
check is the same one list; once `FREEZE_v4.md` is on `main`, v4's own freeze test must also pass on G14's merged
tree (criterion 2, amended below). The O1 step's files (`fno/daily/wiring.py`, `fno/constants_operations.py`,
`config.yaml`) are outside the byte-checked list: v4's freeze does not hash the daily run's step list.

**3. The order of merges (replaces "Two merges" in Design).** G14's own freeze hashes the G7 files it imports
(`FREEZE_v5_v1.md`, Design). Written before `FREEZE_v4.md`, every later G7b merge would change those bytes and make
G14's capture refuse (criterion 9). So:
1. `FREEZE_v4.md` on `main` first (not G14's work; G14 waits for it).
2. The package, card, ledger trial and records format: Judge J's PASS, then merged.
3. `FREEZE_v5_v1.md`: every imported G7 file's hash equals its row in `FREEZE_v4.md` (new criterion 12), then
   merged under the same PASS or its addendum.
4. The O1 step, on its own branch cut from `main` after step 3 (as agreed with the O1 builder, 23 Oct): judge D's
   PASS, merged outside 14:00-16:15 IST on a session day. Its gate is now steps 1-3 plus judge D; the owner's
   sign-off is given, so it is no longer a gate.

**3b. What `FREEZE_v5_v1.md` hashes (judge 596 S2).** Every file on G14's input path: this package's files and every
`fno` module they import, directly or through others, found by walking the imports (not a hand list). Today that path
includes G7's imported files, G7b's candle reader and A16b's `fno/intraday/candle_rv_table.py`, which imports
`fno/intraday/rv_table.py`, which imports `fno/intraday/row_files.py`. None of those three intraday files has a row in
`FREEZE_v4.md` (`rv_table.py` is only "recorded, not checked"; the other two are in neither list), so without this an
edit to them would change G14's input mid-measurement with nothing refusing it. Where `FREEZE_v4.md` has a row, the
hash must be equal (criterion 12); where it has none, `FREEZE_v5_v1.md` alone holds it and the capture's freeze check
(criterion 9) refuses on any change. W8's v4 baseline reads the same unhashed files: that is the v4 freeze builder's
call, raised to the orchestrator, not G14's.

**3c. Freeze coverage as ruled (judge 596 addendum 2, the builder's proposal accepted with four conditions).**
- Fail closed: the shared modules left unchecked are one named list in code (`fno/forecast_v5_v1/method.py`,
  `SHARED`: `fno/__init__.py`, `fno/constants.py`, `fno/constants_channels.py`, `fno/constants_operations.py`,
  `fno/models.py`; they changed in 125 commits in the 10 days to 24 Oct). A test checks byte-checked = walk minus
  `SHARED`; any newly walked file is byte-checked unless a judged change adds it to `SHARED`.
- `FREEZE_v5_v1.md` records each `SHARED` file with its SHA-256, marked "recorded, not checked".
- `fno/intraday/rv_table.py` stays byte-checked though v4 only records it; the freeze record says so.
- Every file of `fno/forecast_v5_v1/` is hashed, `wiring.py` and `cli.py` included; the walk's start set
  (`FREEZE_STARTS`) only decides which imports outside the package are followed (`method.freeze_files`).

**4. Live date.** `daily.live_from.forecasts_v5_v1` is set in the O1 step's commit to the first NSE session after the
day that commit merges (never the merge day itself; DESK_DECISIONS 24 Oct "Merge and turn on everything completed
now": a finished, judged switch goes live from the next session). Mon 26 Oct is possible only if steps 1-4 all pass
by Sunday; with no code yet, the honest expectation is Tue 27 or Wed 28 Oct (reasoning only). The O1 step is never
merged with a date already past or the same day. Fact for the first day: on Mon 26 Oct, `d-1` = 23 Oct has a void
live row and no candle row before the cutoff (A16b's catch-up for 23 Oct runs at 15:33 on 26 Oct), so
`v5c_trailing` would be missing that day.

**5. W8 and G14: one reader of the candle history, no overlap** (owner, 24 Oct: "W8 - yes"; DESK_DECISIONS "W8:
A16b's candle back-fill fills option A's ratio window"; G7b completion text, W8).
- Different uses, said plainly. W8 puts A16b's rows only in a v4 baseline's ratio window (`backfill_window`), never a
  forecast input, outcome or base rate (decision 56 as the owner read it, 24 Oct). G14 uses A16b's rows as a forecast
  input. **Decision 56** (response 113, row 56: "rows with provenance backfilled never count as live forecast
  inputs") **is general: as written it covers v5 too, so it forbids G14's input.** The authority for G14 is the
  owner's own row of 23 Oct (DESK_DECISIONS "v5 trial: V1 next-session forecasts from stored candle history": "same
  V1 forecasters fed by rv-candle 2020-2026"; owner: "Yes, start it"), which makes this one measurement an exception
  to decision 56; it is not a general change of the rule. Decision 56's reason is hindsight inflating a forecast's
  measured skill. The safeguards that keep that reason answered here: each row is read point in time by its
  `first_seen_at` before `d`'s cutoff (criterion 1); every score is a live forecast against a live A16 outcome, never
  a candle outcome (criterion 6); every row is labelled with its input measure and sources (criterion 4); G14 is an
  R1 measurement, never a v4 member, never in a v4 look, never promoted.
- One reader. G7b's builder (session_017GCFK7JLcsYeFKESyXtCyf) builds the reader of A16b's `rv-candle/` rows for
  W8, on top of A16b's own `CandleRvTable` (`fno/intraday/candle_rv_table.py`). G14's `history.py` imports that
  reader unchanged and adds only the splice; it never reads `rv-candle/` files itself. The reader must return each
  session's `status`, `rv_session`, `method`, `provenance` and `first_seen_at` (all columns of the table today); the
  splice's point-in-time filter uses `first_seen_at` against `d`'s cutoff. If G7b's reader is not on `main` when G14's
  code starts, G14 waits; it never writes a second one. If the reader lands in `fno/forecast_v4_rules/` (byte-checked
  by v4's freeze), it must land before `FREEZE_v4.md`; G7b's builder has not named its module yet (open item for the
  orchestrator, sent to G7b's builder on 24 Oct).
- One pairing. W8's drift line (back-fill / live `RV_s` over every live day with both rows) and G14's measure-gap
  table are the same pairs. G14's `gap.py` prints the per-session rows of G7b's pairing; it computes no second
  ratio. W8's review alert (median of the latest 20 outside [0.95, 1.05]) is G7b's; G14 raises none.
- The gap now has three days (from the committed rows, `rv/` and `rv-candle/` 2026; 16 and 23 Oct void live, 23 Oct
  no candle row yet), candle / live `rv_session`:

  | Session | Live (`rv-quote-15m-v1`) | Candle (`rv-candle-15m-v1`) | Candle / live |
  |---|---|---|---|
  | 19 Oct | 1.533569e-4 | 1.476017e-4 | 0.962 |
  | 21 Oct | 1.142562e-4 | 1.139157e-4 | 0.997 |
  | 22 Oct | 1.210651e-4 | 1.221083e-4 | 1.009 |

  The same three values as W8's text (0.962, 0.997, 1.009). Some evidence only (n = 3).

**6. "No partial v5" (owner, 24 Oct), settled.** The owner wrote "close v4 full first and then we'll work on v5 and
no partial implementation". The orchestrator checked the owner's later words the same day: "Consider v4 sign off. So
activate all the features which were waiting for v4 sign off" (DESK_DECISIONS 24 Oct, "The owner signs off protocol
v4", which names "G14's v5 side-by-side step (built and judged first)" among the held items), and later: "I want to run
v5 dry run tests on weekend. So I want to make sure that we have all the necessary and required features developed so
that we could run multiple dry runs on weekend" (`conversations/2026-10-24.md`, line 290, commit cd9b555f3). So G14
goes ahead; no further owner question (orchestrator, 24 Oct; judge 596 m2).

**Round 2 (judge 596).** S1: accepted; response 113 row 56 reads general, so section 5 now cites the owner's 23 Oct
row as the authority and calls this an exception. S2: accepted and widened: the import walk also finds
`fno/intraday/row_files.py` (imported by `rv_table.py`), which the finding did not name. m1: accepted; section 5 is
conditional on the reader's module.

## Acceptance criteria and tests

1. The splice is point in time and candle first. Tests use the real 16-22 Oct rows:
   - a candle row first seen after `d`'s cutoff is never read for `d`;
   - a session with neither an `ok` candle row nor an `ok` live row seen before the cutoff is missing;
   - 16 Oct is missing for `d` = 19 Oct and equals 5.82224e-5 (source `candle`) for `d` = 21 Oct;
   - `d-1` always comes from the live row;
   - each record's `input_sources` counts match its inputs.
2. No v4 file changes: none of the paths in `freeze_check.byte_checked(root)` (the one list, `BYTE_CHECKED_GLOBS`
   plus M1's method files) differs from the merge base, and no file under `research/forecasts/v4/` is in the diff.
   Amended 24 Oct: with `FREEZE_v4.md` on `main`, v4's own freeze test passes on G14's merged tree too.
3. Each forecaster equals G7's own function on the same input series (an equality test, no copy).
4. Every record row carries `input_measure` = "candle RV (15m bars) vs live quote RV" and its method hash.
5. The gap table matches the 19, 21 and 22 Oct figures (amendment 1, section 5) and is built from G7b's W8 pairing,
   not a second calculation (a test that G14's rows equal that pairing's on the same input).
6. The report scores only live forecasts against live A16 outcomes, never a candle outcome. It prints the label
   "candle RV (15m bars) vs live quote RV" and the gap table.
7. The O1 step (its own later commit, merged in amendment 1's order) is `not_live` before its date, and refuses
   after 14:30 with a non-zero exit, so
   the run records it as refused.
8. Registration first: the commit adding `CARD_V5V1.md` with its ledger and gate-log rows is a strict ancestor of the
   first commit touching `fno/forecast_v5_v1/`. Tested on the real git history, as judge 480 required for D6.
9. The freeze: the capture refuses a live day while `FREEZE_v5_v1.md` is missing, has no `Frozen on: YYYY-MM-DD` line,
   or lists a hashed file whose bytes differ.
10. Code size, ruff and the full suite pass.
11. One reader (amendment 1): no file under `fno/forecast_v5_v1/` names `rv-candle` or `CandleRvTable`; candle rows
   reach the splice only through G7b's reader (a test on the package's source and an import test).
12. Freeze coverage and order (amendment 1, round 2): `FREEZE_v5_v1.md` lists exactly the files of the import walk
   (section 3b; a test computes the walk and compares the two lists, and names each file with "v4 row" or "v5 only");
   each file with a row in `FREEZE_v4.md` has the same SHA-256 there; each without one is hashed in `FREEZE_v5_v1.md`
   and an edit to it makes the capture refuse (planted on `candle_rv_table.py`); the commit adding `FREEZE_v5_v1.md`
   has `FREEZE_v4.md` in its history.

## Claims

### Part 1 (24 Oct 2026, session 011SsKz4): NOT complete, not for merge

Built: registration (`research/ideas/CARD_V5V1.md`, trial 100, commit 5868f95d7), `fno/forecast_v5_v1/` (history,
capture, records, method, report, gap) and 45 tests in `tests/forecast_v5_v1/`. **Not built, waiting:** G7b's candle
reader and W8 pairing (interface sent through the orchestrator, 24 Oct), so no `wiring.py`, `cli.py`, freeze record
or freeze check yet; criteria 5 (the gap from G7b's pairing), 9, 11's import half and 12's record are open.

| Criterion | Status | Code | Test (plant caught) |
|---|---|---|---|
| 1 splice | MET | `history.splice` | `test_v5v1_history.py` on real 16-23 Oct rows (`<` to `<=` at the cutoff; candle priority dropped) |
| 2 no v4 change | MET | diff touches no byte-checked path | `git diff --name-only` vs main; full suite |
| 3 equals G7 | MET | `capture.V5Day` runs v4's `DayForecasts` and `capture_day` | `test_each_value_equals_g7s_own_function_on_the_same_series` (G7's `Ewma`, `Har`, `trailing_previous_session`, `close_blend`) |
| 4 label, hash | MET | `records.V5Record` | `test_every_row_carries_...` |
| 5 gap | PARTLY | `gap.gap_table` prints given pairs | real 19/21/22 Oct = 0.962/0.997/1.009 with test-built pairs; G7b's pairing not on main |
| 6 live outcomes | MET | `report.score` | target agrees with v4's `SeriesOutcomes` V1 rule (`s > d` to `s >= d` caught) |
| 7 O1 step | later | branch `story/g14-o1-step` after step 3 | - |
| 8 registration first | MET | - | `test_v5v1_registration_first.py` on real history plus two bad repositories |
| 9 freeze refusal | open | - | - |
| 10 size, ruff, suite | MET | largest file 82 lines | ruff, full suite |
| 11 one reader | PARTLY | package names neither candle files nor their table | `test_the_package_never_names_...`; the import half needs G7b's reader |
| 12 freeze coverage | PARTLY | `method.freeze_files`, `SHARED` (fail closed) | walk = checked plus `SHARED` (dropping a `SHARED` entry caught); record not written |

Self-review (independent agent): no blocking finding. Fixed: the target now tested against v4's own V1 outcome
rule (its finding 2), a misnamed test (3), a dead `SHARED` entry (7), Monday 26 Oct's missing trailing (8), the
`not_started` pin (9), the source-count wording (6). Waiting for wiring: the reader and `wiring.py` in the method
hash (1; the freeze already lists every package file). Stated, unchanged as v4: special sessions in the candle
history enter HAR intraday as v4's live rows would (5); a past session with no A16 row stays pending (10).
Deviation: the card lives in `research/ideas/` (Registration, above).
