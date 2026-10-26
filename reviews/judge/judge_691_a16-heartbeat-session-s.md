# Judge 691: A16 heartbeat fix, judge S (2 of 2)

Branch `story/a16-heartbeat-session` at `34e8093f4`. **FAIL, lane 1** (1 blocking, 1 minor). Full clone; gates run.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Root cause: two runs' pushes merged hunk by hunk under `-X theirs` | MET | `fa33262e3` (taker: mark, session, times) and `b21b2c146` (non-taker: times) merge in `b32ffcbc6` to mark 09:30 plus session 2026-10-23. The first mix was earlier, `f5bc66797` at 09:15 (not named in the story) |
| 2 | One-line JSON makes every clash a whole-file clash | MET | `heartbeat.py:38-40`; the indent plant fails the new test |
| 3 | The published beat is a correct beat (the problem the story states) | NOT MET | finding 1 |
| 4 | The silence check reads only `run_finished_at` | MET | `heartbeat.py` `_finished`, `heartbeat_state`; `test_clock_and_heartbeat.py` passes |
| 5 | Overlapping runs never take one mark twice or double Groww quote reads | MET | one claim per mark on main (`dfcaebbea`, `765c598ef`, `8c3f00615`, `27da4d867`) from 2-3 tries each; one slot CSV per mark (`25ec993aa`, `fa33262e3`, `e19673e1c`, `385bf70ff`); `recorder.py:107-110` stops a loser before `take` |
| 6 | Slot or RV files cannot mix the same way | MET | one slot file per mark, written by the claim's winner; `RvTable.write_once` (`rv_table.py:48`) raises `RvConflict` |
| 7 | Gates | MET | 18062 passed, 1 skipped, 13 xfailed; ruff, format and `check_imports` clean |

## Findings

1. **Blocking: after the fix, the heartbeat keeps the stale session all day.**
   - What happens: `-X theirs` keeps the copy already on GitHub. The run that loses the claim always pushes first: it
     ends at once, while the winner spends about 1 minute taking the mark. On 26 Oct the loser pushed first at every
     mark: 09:15 (`869ba011f` before `25ec993aa`), 09:30, 09:45 and 10:00.
   - So every winner's beat would be thrown away. The heartbeat would show session 2026-10-23, mark 15:30 all day,
     and a finish time up to a run's length old. That is the symptom the story sets out to fix, minus the mix.
   - The builder's own test shows it: I printed the published beat, and it was `2026-10-23 15:30
     2026-10-26T03:59:21`. `assert published in (new, only_times)` accepts it.
   - Root cause: two writers of one file, merged by "remote wins", not by which beat is newer.
   - Fix expected (any one):
     - (a) split the file: run times in `heartbeat.json` (any run), the last mark's fields in their own file written
       only by the claim's winner (one writer per mark);
     - (b) re-apply this run's beat after the pull, taking each field from the newer beat: the mark fields from the
       later session and mark, the times from the later `run_finished_at`.
   - Test expected: the 26 Oct order (non-taker first) publishes session 2026-10-26, mark 09:30.
2. **Minor:** the story names only the 09:30 merge. The first mix was `f5bc66797` at 09:15.

## Plants

- 1 planted, 1 caught: the indented writer fails `test_heartbeat_merge.py`.
- What the tests miss: the stale-but-whole outcome passes them (finding 1).

## Notes

- Pre-existing, not this story's: a run that loses the claim still runs `source.prepare` (sign-in and expiry listing,
  `recorder.py:106`, `groww_source.py:55-61`) about 45 s before the mark. That is outside the quiet window and reads
  no quotes.
- No Groww command was run.

## Addendum 1

Round 2 at `a7aecaf04`. **PASS, lane 1** (1 minor, not blocking). Full clone; gates run.

| # | Verdict | Evidence |
|---|---|---|
| 1 | Fixed | Two one-line files. `heartbeat.json` (run times) is written by every run (`heartbeat.py` `write_run`). `last_mark.json` is written only when `took` (`recorder.py` `_beat`), so the claim loser never rewrites it. `read()` merges the two; the silence check still reads only `run_finished_at` from GitHub's `heartbeat.json` (`wiring.py:96`). The merge test has two clones and runs both push orders; both publish session 2026-10-26, mark 09:30 |
| 2 | Fixed | The story names `f5bc66797` |
| - | Checked | `last_mark.json` is in `OWNED_PATHS`, so both the slot committer and the claims committer push it (`_ledger_paths`). No other reader of the old mark fields under `fno/`, `tools/` or `.github/`. File sizes 103, 248 and 145 lines |

- Gates: 18063 passed, 1 skipped, 13 xfailed; ruff, format and `check_imports` clean.
- Plants: 3 planted, 2 caught.
  - Caught: the loser writes `last_mark.json`; `last_mark.json` dropped from `OWNED_PATHS`.
  - Survived: `write_run` keeping an old file's mark fields together with `read()` letting them win. This needs two
    edits and a file in the old format. Low risk, as the builder says: the first `write_run` drops the legacy fields.
- **Minor (carry in the next A16 doc change):** A16's design (`A16-intraday-quote-recorder.md:233-234`) and
  `fno/storage/README.md:134` still list the owned paths without `last_mark.json`. LM1's planned `MonitorHeartbeat`
  reuses `heartbeat_state` only, so the removed `write` does not affect it.
- Merge only outside 09:15-15:35 IST, after judge R's PASS too. No Groww command was run.
- Tip `5cef9bcc2` (after a7aecaf04): only Markdown changed, with no code or test diff; the minor is fixed there
  (`A16-intraday-quote-recorder.md:231-235`, `fno/storage/README.md:134` now name `last_mark.json`). PASS stands at
  this tip.
