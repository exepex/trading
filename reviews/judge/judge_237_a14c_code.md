# Judge 237: A14c code, the stress factor recomputed from NSE's archived SPAN files

Head `story/a14c-stress-recompute` at 769f97e2 (A14c builder 01Vm1WnH8i9waM8EJG8zwWqg; claims: response 238). Story
`docs/stories/A-data-foundation.md` "## A14c" on that head: text PASS in judge 173, since changed by the owner's
measure decision 07f62385 (the smallest k needed), the read-ahead and the fail-closed paragraph. Lane 1: money and
risk (C2's margin stress), a schedule and a workflow, Drive and Slack. Judge D, 16 Oct 2026.

Read-only checks used: Google Drive (two archived SPAN files downloaded with the job's own reader, nothing written)
and NSE's archive URL (one GET of a 2020 file, body discarded, status read).

**FAIL: three should-fixes.** The code is right: every number I recomputed by hand matches. Two money rules lack a
test that catches their natural break, and the story still promises a part this head does not build.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Reproduction of response 77's three windows | MET (data) | Response 235's reproduction to 0.001 with the gross measure (1.2650, 1.4073, 1.1272). Its scripts are the builder's, not in the repository; I did not re-run the three windows. My own hand check is in criterion 2. |
| 2 | Hand computation; the needed factor | MET | **My hand check on two real files from Drive** (both SHA-256 equal the manifest's; `nsccl.20200408.i1.zip`, created 7 Apr 20:28 IST, and `nsccl.20200504.i1.zip`, created 1 May 01:35 IST). BF 200 on the 28 May 2020 expiry: legs +8800 CE, +8800 PE, -9000 CE, -8600 PE. Entry scan 57,720.00, which is SPAN's short-option minimum (Rs 444 × 2 short units × 65), NOV 56,910.75, exposure 22,859.72 (2% of 8,792.2 per short unit). Peak on 4 May: scan 63,960 (Rs 492 × 2 × 65), NOV 12,034.75, exposure 32,044.675 (the 8600 PE is now beyond 10% out of the money at 9,859.9, so 3%). C2 counts 83,969.925. k = (83,969.925 + 56,910.75) / (57,720 + 22,859.72) = **1.748339**, equal to the claim's 1.7483. `needed_factor` bisects on `MarginParts.stressed` itself, so there is no second copy of C2c's formula, and it returns the upper end. My mutation, recording only the first rise, fails `test_the_largest_needed_factor_over_the_holding_by_hand`. |
| 3 | Point in time | MET | `_span` refuses a file whose SHA-256 differs from the manifest, and one created at or after 09:00 IST on its day (tests). A missing day stops the run before any computation (criterion 8). |
| 4 | 2020 method | MET | Only one GROSS minimum rate is read, and only with `allow_short_option_minimum` (A14's daily job still refuses it). The minimum is applied as `max(0, minimum × short units, losses)`, which my hand check confirms on real files. Other methods are refused by name (tests). |
| 5 | Output | MET | The evidence names every file's SHA-256, the rule, the windows and the run day; it is byte-identical on a rerun (test). Nothing writes `config.yaml`; `recompute_workers` is a new key, written by hand in this commit. |
| 6 | Owner decisions recorded | MET | d68b1a9c, da0f769d and 07f62385 (DESK_DECISIONS). |
| 7 | Guardrails | **PARTLY** | `decide`: below 1 is refused, a rise is applied, a fall is held, and an approved fall is applied and named. **Should-fix 1:** my mutation `computed >= last.factor - 0.05` (apply a one-step fall) **passes all 125 `tests/nse_margins` tests**. The fall tests use 1.45 to 1.3 only. This is exactly the tolerance the orchestrator proposed and the story rejected ("Falls of 0.05 or less are therefore held too"; criterion 7: "any fall, 0.01 included"). |
| 8 | Coverage by date | MET | Swapped date and latest-missing tests. **On the real data:** with A7's calendar and the branch's manifest (1,687 rows, 2 Jan 2020 to 16 Oct 2026), `check_coverage` passes for run day 18 Oct (1,681 sessions through 16 Oct). The 6 muhurat-only days in the manifest are not required. |
| 9 | Incremental equals full | **PARTLY** | The window logic is right (a counted holding enters after `coverage_through - 44 days`, inside the 60-day lookback, and holdings are counted once, by exit). **Should-fix 2:** my mutation, counting only holdings that exit 7 days or more after the last `coverage_through`, **passes every test**. `test_incremental_equals_full` and `test_an_incremental_run_counts_only…` have their exits far from the boundary (2 Nov, 7 Dec), so a holding ending in the first sessions after the last row, the weekly case every Sunday, is never pinned. Seed-not-a-floor and hand-row-forces-full are tested. |
| 10 | Alerts; the broker check | **NOT MET (part)** | One line per run, every stop with one line, and a dropped holding counted (tests; the catch-all prints the traceback and sends the error's type and text). **Should-fix 3:** the broker check (`margins stress-broker-check`, `stress_broker_check.csv`, the "nothing to check" idempotence test) is in the story's scope and criterion 10 but not in this head. The orchestrator ruled "build it after A14c". The story text must say so: move it to a named part 2 (scope, criterion 10 split, own judge) and update the WORK_REGISTER row, or the criterion stays unmet. |
| 11 | Gates | MET | On 769f97e2: `pytest -n auto` 7020 passed (Slack token unset), ruff check and format clean, check_imports clean. Trial merge with main: the only conflict is reviews/claude/README.md (both rows kept), and then 7021 passed. |

**Workflow (lane 1, schedules):**
- Sunday `30 4 * * 0` UTC is 10:00 IST, plus a manual `full` run.
- `continue-on-error` steps are read by `outcome`, which is correct: the factor row and evidence are added only on
  success, and the manifests always.
- There is a line for "computed but not committed" and a line for a failed librarian, and the run fails when the
  factor step wrote nothing.
- No broker key or Groww SDK. `concurrency` avoids two runs at once.

**Read-ahead:** `in_order` hands files back in request order and keeps at most `workers` in flight. An error is raised
at its own day and pending downloads are cancelled. Each thread has its own Drive session. Tests include reversed
finish times and a run-level byte-identical check.

## Should-fixes (all three are small)

1. **A one-step fall test.** Add a planted run whose computed factor is exactly one 0.05 step below the factor in
   force (for example 1.45 to 1.40), and one with a hand factor in force of 1.41 and computed 1.40, so the smallest
   possible fall is held. The mutation above must then fail.
2. **An incremental boundary test.** Make the largest needed factor belong to a holding that exits in the first
   session after the previous row's `coverage_through`. The incremental run must give `full`'s `unrounded`. The
   7-day mutation (or `>` changed to `>=`, or a lookback of 30) must then fail.
3. **Story text for the broker check.** Record the split in A14c's text (scope bullet, criterion 10, the O1 line),
   name part 2 with its own judge, and update the WORK_REGISTER row.

## Notes (not blocking)

- **What the first full run will do (risk manager, strong evidence):** the measured k is about 1.75 or more, against
  1.45 in force. A rise applies at once, so from the first full run C2 sizes with k of at least 1.75 on the whole
  margin (C2c). That is fewer lots for the same capital than the 31% cut judge 173 noted at 1.45. That follows the
  owner's rules; the #fno-desk line will show it. The binding case is a 2020 debit butterfly whose bought legs lost
  value while SPAN's short-option minimum and the 3% far-strike exposure rose. It is a real crash-time path, not an
  artefact.
- **STR1 cap (reasoning):** C2 caps the stressed SPAN part of STR1 codes at `span_cap` (`max(broker, min(span,
  span_cap))`). No k can protect a capped code beyond its cap, so measuring them uncapped, as the owner's formula
  states, is the right choice. The limit belongs to STR1's cap, not to A14c.
- Jan 2024 to Aug 2026, outside May-Jun 2024, is not yet measured. The first full Actions run covers it and may raise
  k. Its seconds per file decide whether 330 minutes are enough (8 workers at about 30 s a file is about 1.8 hours).
- `--approve-fall` is not checked against DESK_DECISIONS (accepted as a note in the self-review). Reading the cited
  commit's row before applying would be cheap later.

## Addendum 1: head c73fd5f5 (the three should-fixes)

**PASS.** The claims are now `reviews/claude/response_240_a14c-code.md`, the same file renumbered because O9 holds 238
on main. Since 769f97e2 the branch adds `tests/nse_margins/test_stress_boundaries.py`, the story's part-2 split and the
WORK_REGISTER row, plus merges of main. A14c's own `fno/` code is unchanged.
1. **One-step fall:** `decide` cases cover 1.45 to 1.40 (held), 1.41 to 1.40 (held) and 1.449 to 1.45 (applied, not a
   fall), and there are planted runs at scale 11.7 (1.386747, computed 1.4) against both 1.45 and a hand 1.41. **My
   mutation** `computed >= last.factor - 0.05` now fails 4 tests.
2. **Incremental boundary:** run 1 on 7 Dec covers to Fri 4 Dec. The 20 Nov peak's holdings exit Mon 7 Dec, the first
   session after that, and the incremental run equals full (1.686747). **My mutation** `exit >= coverage_through + 7
   days` now fails 1 test.
3. **Split:** the scope bullet is "A14c part 2 (… built after part 1 merges, with its own judge)", with the market-hours
   evidence. Criterion 10 is split into part 1 (the line) and part 2 (the broker check). Depends and Status are
   updated, and the WORK_REGISTER row matches.
- **Gates on c73fd5f5:** 7028 passed (`-n auto`, Slack token unset), ruff check and format clean, check_imports clean.
  A trial merge with current main is clean (WORK_REGISTER and README auto-merged), and then 7042 passed.

Part 1 may merge. The notes in the main verdict stand (k of 1.75 or more on the first full run; the STR1 cap;
`--approve-fall` not checked against DESK_DECISIONS).
