# Judge 177: protocol v4 freeze checklist (plan only): `freeze/v4-checklist` c84d3554 (lane 1)

Judge B. Plan: `reviews/claude/response_157_v4-freeze-checklist.md` (A16/G8 builder, who now owns the freeze), merged
with `main` 55726493. The commit adds only the response and its README row: no protocol text, code or record changes.
I checked it against PROTOCOL_v4.md sections 4, 6, 10 and 11, G7, G8, M1 and A16's code at c84d3554, and
`docs/WORK_REGISTER.md`.

## (1) Does the byte-check list miss a file that decides a v4 baseline, outcome or score?
I listed every `fno` import of the planned byte-checked set myself: `fno/forecast_v4/`, `fno/forecast_v4_rules/`,
`fno/forecast_scoring/v4/`, `tools/v4_*.py` and M1's six `METHOD_FILES`. Outside the set they reach `fno.constants`,
`fno.models`, `fno.config`, `fno.storage.*` (plumbing), `fno.desk.settlement` and `fno.research_data.calendar`
(recorded, as section 10 says), `fno.global_cues.*` (the US flag, free by the owner), `fno.weather.model` (an abstract
interface only), `fno.weather.drivers` and `fno.weather.records` (the card's drivers, not the probability), and two
real gaps:

**Should-fix 1: V1's outcome and its HAR baseline depend on A16's RV method, which is neither byte-checked nor pinned.**
- V1's outcome is intraday `RV_s`, and its trailing and HAR baselines are built from the same rows. The figure and its
  void status come from A16's code: `fno/intraday/realised_vol.py` (the arithmetic), `session_rv.py`, `status.py`
  (`index_check`, the void rule) and `slots.py`.
- `fno/intraday/rv_table.py` stores the rows written once, with a `method` column. Checked:
  `forecast_v4_rules/series.live_intraday_rv` reads `status` and `rv_session` and ignores `method`.
- **The normal-running path:** A16's design 5.2 and protocol 1.x plan for it. Above 5% void sessions in a quarter, "a
  new version is proposed", and `realised_vol.py` says "a new sampling rule is a new class with its own method name".
  After the freeze, such a version's rows would feed V1's outcomes and baselines silently, against the protocol's
  "series never pooled".
- **Fix (either is enough):**
  - (a) byte-check `fno/intraday/realised_vol.py`, `session_rv.py`, `status.py` and `slots.py`; or
  - (b) record A16's current `method` value in FREEZE_v4 and make V1 count only rows of that method, as a G7 change
    before the freeze, with a test.

  (b) leaves A16 free to add versions. `rv_table.py` stays recorded as planned.

**Should-fix 2: `fno/forecast_scoring/scores.py` (G4) decides v4's log score and calibration table but is in no
list.**
- `fno/forecast_scoring/v4/scores.py` imports `log_score`, `calibration_table` and `CalibrationBin` from it: the
  clipping 0.01-0.99 and the 10 bins.
- No FREEZE_v1 to v3 lists it (checked), so nothing stops an edit for another protocol from changing v4's reported
  scores.
- Section 10 asks for "every G7 and G8 file that decides a v4 ... score". The verdicts use `forecast_v4/loss.py`
  (byte-checked), so this affects reported scores only.
- Fix: add it to the byte-checked list (one line).

Not gaps: the committed data (NIFTY closes, VIX history, `rv/` rows) is data, not code, and the rows are written once.
M1's `METHOD_FILES` already includes G7's `series.py` and `baselines.py` and v4's `terms.py` and `sessions.py`, all
byte-checked anyway.

## (2) Does any protocol text edit change a rule rather than state the code?
| Edit | Code checked | Result |
|---|---|---|
| 11 E decided, option 2 | `confirmatory.crash_dominated`: `event_days > CRASH_SHARE * n` (strict). At n = 125, 12 days pass and 13 fail; 13 passes first at n = 130 | states the code |
| V6b scored, no edit | only V7 is in `DESCRIPTIVE_ONLY` | correct |
| HAR (intraday) skips void sessions | `forecast_v4_rules/capture.py:79-86`: `usable` drops `value is None` before `Har(...)`; `Har`'s docstring says the same | states the code |
| Freeze start, "not started" | `scoring._miss_start` (judge 156) | states the code |
| Back-fills disclosed | `f891d9b` "G7 back-fill ... V6 (2017-01-03 to 2026-10-14)" and `6b7eaba` "M1 weather back-fill, labelled backfill_exploratory", both exist | correct |
| Long line | cosmetic | none |

The G10 edits are judged with G10's build, not here.

## Coordination (owner's rule of 15 Oct)
**Should-fix 3: `docs/WORK_REGISTER.md` still gives the freeze to the G6 session.**
- Row 27, "G6 freeze", names `01MgTu3L1T3y6R18ATTwbFub` and "waits for the G6 session". The plan says the A16/G8
  builder owns it now (orchestrator, 15 Oct).
- CLAUDE.md: "add or update your own row in your first commit". Update the row's owner and status in this branch.
- G10's row is the same builder's, and the plan orders G10 first, so there is no overlap.

## Notes (one line each, not blocking)
1. **Later registrations.** V1's `rules` ("once V1 starts") and the AI slots (G11) are registered after the freeze.
   Protocol section 6 allows a registration made before a slot's first counted forecast. Say that each such
   registration is an appended ledger row, and that G8's adapter reads every row, not only the freeze's.
2. **Golden fixture.** The plan names `tests/fixtures/forecast_v4/v4_golden.json`; keep its hash in the freeze test,
   as v2 does.
3. **The owner's confirmations.** Each quote needs its source row and date in `DESK_DECISIONS.md`, as judge 149 M4
   asked for both 10% caps.

## Gates
Docs only; no gate applies beyond `git diff --check`, which is clean. Nothing here is frozen, so the freeze commit
gets its own lane-1 verdict (and rule 9).

**Verdict: FAIL for c84d3554 on should-fixes 1-3.** Each is a plan edit of one or two lines, plus, if option (b) is
chosen, one G7 change before the freeze. A re-check needs only the revised response 157 and the register row.

## Addendum 1 (15 Oct 2026): revision 1 at 3e3fd302

The revision changes `response_157_v4-freeze-checklist.md` (adding a "Revision 1" section) and the
`docs/WORK_REGISTER.md` row. The rest of the branch diff is the `main` merge.

| Finding | Status | Evidence |
|---|---|---|
| Should-fix 1: V1's RV method | MET | Both options are taken. (b): the record pins `rv-quote-15m-v1` (checked: `fno/intraday/realised_vol.py:49`), and G7's `series.live_intraday_rv` will read only that method's rows, with a test, before the freeze. (a): `realised_vol.py`, `session_rv.py`, `status.py` and `slots.py` are byte-checked. The builder's reason for taking both is right (reasoning): (b) stops a new class, and (a) stops an edit in place |
| Should-fix 2: `fno/forecast_scoring/scores.py` | MET | Added to the byte-checked list, with what it decides |
| Should-fix 3: register row | MET | "G6 freeze" names the A16/G8 builder, its branch, the freeze test and the status |
| Notes 1-3 | MET | Later registrations are appended ledger rows that G8 reads in full. The golden fixture's hash is in the freeze test. Each owner quote carries its `DESK_DECISIONS.md` line and the row's text. I checked lines 121, 123, 157, 177, 181, 182, 184, 185, 186 and 194 on 3e3fd302: each is the row named |

**Verdict: PASS for 3e3fd302** (plan only). Next, in order: ChatGPT, the owner, G10's build, then the protocol-edit
commit and the freeze commit, each with its own lane-1 verdict. The G7 method filter must land, judged with its test,
before the freeze commit.
