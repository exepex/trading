# Response 238: A14c code claims (the stress factor recomputed from NSE SPAN files), for judge D

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, 16 Oct 2026. Branch `story/a14c-stress-recompute`; the head is the commit
that adds this file. Lane 1. Research only: it writes one row a week to `research/data/margins/stress_factor.csv`, which
C2 and C4 read (C2d). Nothing places an order or writes `config.yaml`'s factor.

## What changed since the story text PASS (judge 173 addenda)

- **The measure (owner, 16 Oct 2026, DESK_DECISIONS 07f62385, response 235):** per held position, the smallest k with
  `max(0, k x scan - NOV) + min(0, NOV) + k x exposure` of the entry's parts covering what C2 counts (`initial()`) on
  every later day held. `needed_factor` (`fno/nse_margins/held_rise.py:33`) bisects on `MarginParts.stressed`
  itself, so C2c's formula is not copied. It returns the upper end, so the k always covers. The plain ratio of
  counted margins, as first built, gave 3.55 for the BF 200 of 8 Apr 2020 (a debit whose bought legs nearly cancel the
  scan at entry); the needed factor is 1.7483. For credits the two are the same number.
- **Read-ahead** (`fno/nse_margins/prefetch.py`): 8 downloads ahead (`risk.stressed_margin.recompute_workers`), each
  thread with its own Drive session, fed strictly in day order. One Drive stream gave 0.41 MB/s here, so a full run
  would take about 14 h one at a time, past the workflow's 330 minutes.
- **Self-review fixes** (below): every stop sends one line; a dropped holding keeps what it needed; the workflow
  commits only a run that succeeded.

## Criteria: code, test and broken-code proof

| # | Code | Test | Proof the test catches a break (run by the builder) |
|---|---|---|---|
| 1 | reproduction (response 235) | anchors reproduced on real files: 1.2650, 1.4073, 1.1272 to 0.001 (gross measure, to window end); needed factor 1.7483 / 1.3872 / 1.0589 | n/a (data check, scripts in the builder's scratchpad) |
| 2 | `held_rise.py:33` `needed_factor`; `:96` its use | `test_needed_factor.py` (BF 200 1.7483, 1.75 covers 83,970, 1.70 does not; credits equal the ratio; smallest covering k on 500 random parts; tracker-level debit); `test_held_rise.py` (hand SF) | plain ratio in `_mark`: 1 fails; returning the lower end: 1 fails |
| 3 | `stress_run.py:104-113` (SHA-256, 09:00) | `test_stress_run.py` not-first-copy, written-at-09:00 | as merged before (judge 188 round) |
| 4 | `calculator.py:86-89` 2020 minimum; `span_file.py` history read | `test_history_minimum.py`, `test_span_file.py` | as before |
| 5 | `stress_evidence.py` | byte-identical evidence; files CSV names every SHA-256 | as before |
| 6 | DESK_DECISIONS d68b1a9c, da0f769d, 07f62385 | n/a | n/a |
| 7 | `stress_log.py` `decide`; `stress_run.py:83` | rise applied, fall held, approved fall applied and named, below 1 refused; `test_stress_alerts.py` approval named only on a real fall | as before; removing the fall condition fails |
| 8 | `stress_coverage.py:36` | coverage by date (swapped date, latest missing) | as before |
| 9 | `stress_run.py` incremental | incremental equals full (2 peaks), the seed is not a floor, a hand row forces full | as before |
| 10 | `stress_run.py:93` line | one line per run; a dropped holding counted; a download error, an expired Drive consent and a missing calendar year each give one line and no row | catch-all narrowed to one type: 2 fail; drop-keeps removed: 2 fail |
| 11 | gates | ruff, check_imports, full suite on the merged tree: **7,020 passed** (-n auto, 182 s) | n/a |

**Read-ahead proof:** `test_prefetch.py` (order with reversed finish times, at most `workers` in flight, error at its
day, early stop leaves nothing running, one reader per thread, config value and refusal of 0) and the run-level test
(Mondays finish last at 8 workers: the same feed order, row and byte-identical evidence). A completion-order mutation
fails both.

**Not in this head: criterion 10's broker check** (the Groww comparison of an applied row). The orchestrator ruled on
16 Oct: "Build it after A14c". The design is accepted (market hours only, SPAN within Rs 1 a lot, exposure rebased to
Groww's index within 0.1%). It is informational: a mismatch never holds the factor. A judge may count this as an open
criterion; I propose it as A14c part 2, judged on its own.

## Real output sample (committed code, NSE's real files, a dry run)

Made by `StressFactorRun` with real wiring (`build_row_builder`, A7's calendar), on local copies of Drive's
first-archived i1 files for 1 Sep-16 Oct 2026 (32 sessions, each SHA-256 checked), a scratch factor file holding the
owner's seed, run day 17 Oct, and an alert sender that prints instead of posting:

```
(not sent) Omenix F&O stress factor 2026-10-17: held 1.45 (computed 1.25, was 1.45); peak PCS 250 entered 2026-09-01 peak 2026-09-03 needed 1.2047; a lower value waits for the owner: approve it with a DESK_DECISIONS row, then rerun with --approve-fall
2026-10-17,1.45,1.25,1.204684,held,PCS 250 entered 2026-09-01 peak 2026-09-03 needed 1.2047,2026-10-16,2300c9e0...
Holdings completed in this run: 630; dropped (named below): 0
| Sep-Oct 2026 calm | 1.127 | 1.059 | SC 300 entered 2026-09-09, peak 2026-09-24 |
```

Two runs gave the same evidence SHA-256. This is a window only, not the real first run (that is `--full` in Actions
after the merge).

## Builder self-review (quality rule 3): two independent agents, correctness and silent failures

| Finding | Verdict | What was done |
|---|---|---|
| Errors other than the named refusals (Drive consent `DriveSignInRefused`, settings missing, A7's `CalendarError`, a bad manifest row) crash with no line | **Accepted, must-fix** (checked: A7's calendar ends 25 Dec 2026, so from about 30 Nov a January-2027 exit raises) | catch-all at `stress_run.py:59`: traceback to the log, one line naming the error, no row; tests for consent and calendar |
| The desk hears "applied" before the row reaches `main` (commit or push can fail) | **Accepted** | the workflow posts a line when the result was computed but not committed |
| A refused run's evidence could be committed; a missing `stress/` folder aborts `git add` and loses the manifest rows | **Accepted** | stress paths are added only when the factor step succeeded; manifests always |
| A dropped holding lowers the maximum silently; entry skips by the model are unnamed | **Accepted, and the root cause fixed** (a planted hole on 9 Oct turned an `applied 1.7` into `held`) | a dropped holding keeps the factor it needed so far (`held_rise.py:94`); entries the model cannot price are named; the line gives the count |
| Rounding: the bisection's upper end can add a 0.05 step on an exact hit | **Accepted** (cheap, safe) | `rounded_up` rounds to 6 digits, like the stored `unrounded` |
| "fall approved" was written on a rise when the flag was given | **Accepted** | named only when the factor fell |
| The evidence path differs from the story text | **Accepted** | the story text now names `research/data/margins/stress/` |
| Two lines when the librarian fails and then the factor step refuses | **Rejected**: two different failures, each with its own line; the rule is one line per run of the factor step | none |
| An incremental run with no newly completed holding writes a carried row | **Rejected**: intended. The weekly row keeps the factor inside C2's 30-day age (workflow header); the first-run case writes nothing (test) | none |
| Incremental runs miss later edits to A7's calendar for past dates | **Note, accepted as a known limit**: a calendar edit for the past is rare; any such edit is followed by `--full` | none in code |
| A same-day rerun appends a second row and overwrites the evidence files | **Note**: the later same-date row wins (C2d, judge 188); the earlier evidence stays in git history once committed | none |
| `--approve-fall` is not checked against DESK_DECISIONS | **Note, accepted**: the owner runs it by hand and the line names the row; checking the file is possible later | none |

## Open points for the judge (each marked)

- **STR1 codes and the SPAN cap** (reasoning): A14c builds the held parts without C2's STR1 `span_cap`, as the owner's
  formula states. For CCS/PCS, C2 caps the stressed SPAN part, so k from the uncapped formula could under-cover a
  capped code on its own. Today the binding k comes from BF (1.75), above every CCS/PCS figure seen (largest 1.2047),
  so there is no effect on the windows measured. Measuring capped codes with their cap is a small change if the judge
  wants it.
- **Coverage** (strong evidence that it is partial): Jan 2024-Aug 2026 outside May-Jun 2024 has not been measured; the
  first full run may set k above 1.75. The story's known-limit paragraph says so.
- The full run still needs to happen in Actions after the merge, with the first seconds-per-file measurement.

## Addendum 1: judge 237's three should-fixes

1. **One-step fall:** `tests/nse_margins/test_stress_boundaries.py` adds a planted 1.45 → 1.40 run and a hand factor of
   1.41 in force with 1.40 computed (both `held`), plus unit cases of `decide` (1.449 rounds to 1.45: applied, not a
   fall). The judge's mutation `computed >= last.factor - 0.05` now fails 4 tests (checked).
2. **Incremental boundary:** run 1 on 7 Dec covers to Fri 4 Dec; the 20 Nov peak's holdings exit Mon 7 Dec, the first
   session after it; the incremental run equals full (1.686747). The judge's mutation
   `h.exit >= last.coverage_through + 7 days` now fails it (checked).
3. **Broker-check split:** the story's scope bullet is now "A14c part 2" (built after part 1 merges, own judge),
   criterion 10 is split into part 1 (the line) and part 2 (the broker check), and Depends/Status say so; the
   WORK_REGISTER row matches.
