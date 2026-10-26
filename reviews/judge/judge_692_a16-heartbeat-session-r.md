# Judge 692: A16 heartbeat fix, Judge R

Branch `story/a16-heartbeat-session`, SHA 34e8093f4d6f90039740750ab12fc3db49bdc367. Judge R
(session_01KR5SiKNBq2bYMHtd8GbdN6), judge 1 of 2; Judge S's verdict not read. **FAIL** (1 should fix, 1 minor). Lane 1.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Root cause matches the history | MET | fa33262 (taker: 09:30, 2026-10-26) and b21b2c1 (no-mark run: times only) merged in b32ffcb into mark 09:30 beside session 2026-10-23 and the no-mark times; `-X theirs` from `manifest_commit.py:48` (`keep_remote_on_conflict`, `intraday/wiring.py:128`); no-mark runs copy the old beat (`recorder.py:231`) |
| 2 | One-line writer stops the mix | MET | test fails with `indent=1` planted back (1 failed), passes as built |
| 3 | The published beat is right afterwards | NOT MET | finding 1 |
| 4 | No reader acted wrongly | MET | only `heartbeat_state` reads it, `run_finished_at` only (`heartbeat.py`, `intraday/cli.py:98`, `recorder-watch.yml:42`); a mix held a real run's finish |
| 5 | Two overlapping runs: no double take, no double Groww read | MET | one claim per mark on main (09:15, 09:30, 09:45 run 032331Z; 10:00 run 042327Z) though 2-3 runs claimed each; all four 26 Oct slot rows `good`, 216 of 216 two-sided, no failures |
| 6 | Other shared files (slots, rv) open to the same mix | MET (not open) | one header and one row per file, write-once (`row_files.py:1-4`, `write_row` raises on an existing file); a clash is one row line, kept whole; claims are one-line JSON |
| 7 | Gates (unshallowed clone) | MET | ruff check and format clean, `check_imports` clean, `check_records` clean, pytest 18,062 passed, 1 skipped, 13 xfailed |

## Findings

1. **Should fix: after the fix, the stale beat wins every time.** With one line, a clash keeps the copy already
   pushed (`-X theirs`). On 26 Oct the no-mark run pushed first at every mark, because it reads no Groww (09:15 03:44:21
   vs 03:46:05 UTC; 09:30 03:59:22 vs 04:01:02; 09:45 04:14:21 vs 04:16:01; 10:00 04:29:21 vs 04:31:04). I replayed
   that order with the builder's own helpers (`push_beat`, two clones). It published mark 15:30, session 2026-10-23:
   the taker's beat was dropped. So all day the file would show the previous session's last mark beside today's
   slots. That is the reported symptom, made more likely, not fixed. The test passes because it accepts either run's
   beat (`published in (new, only_times)`), and the story calls this "cosmetic". Fix expected, at the root: the
   published beat must say what really happened. For example, a no-mark run writes no mark fields (the ledger is the
   record of marks; the heartbeat only says a run finished), or on a clash the newest beat wins. Test: replay the real
   push order (no-mark first) and assert today's session and the latest taken mark, or no mark fields at all.
2. **Minor: the story names one mixed merge; there were four.** f5bc66797 (09:15), b32ffcb (09:30), b0cf5a38a
   (09:45) and 46a19b2df (10:00) all mixed. The 23 Oct session first came from 869ba011f, which copied 23 Oct's last
   beat at 09:14 IST. Correct the evidence line.

## Plants

2 planted: `indent=1` restored (the new test fails: caught); a compact-separators writer (36 heartbeat tests
pass: correct, both are one line). Survivor: none. My replay test (finding 1) is not in the suite; it should be.

## Notes

- Merge only outside 09:15-15:35 IST, as the story says. No Groww command was run for this verdict.

## Addendum 1

Round 2 at cff78174f8a0906d2a8c2db61ff4f7b716e22ccd (code at a7aecaf04). **FAIL, documents only** (1 should fix);
the code passes. Lane 1.

| # | Finding | Result | Evidence |
|---|---|---|---|
| 1 | Stale beat wins | Accepted | `heartbeat.json` now holds run times only; `last_mark.json` is written only when `took` (`recorder.py` `_beat`); the merge test replays both push orders with two clones and asserts 2026-10-26 / 09:30 |
| 2 | Four mixed merges | Accepted | story names f5bc66797, b32ffcb, b0cf5a38a, 46a19b2df and 869ba011f |

Plants: 3. (a) `write_mark` called on every run: `test_failures.py::...keeps_the_last_marks_fields` fails (caught).
(b) Mark fields copied back into `heartbeat.json`: 2 tests fail (caught). (c) A no-mark run rewriting `last_mark.json`
with its own copy: passes, but it is an equivalent mutation (the copy equals its base, so git sees no change).
Gates (unshallowed): ruff check and format, `check_imports`, `check_records` clean; pytest 18,063 passed, 1 skipped,
13 xfailed. The silence check still reads only `heartbeat.json`'s `run_finished_at` (`PublishedHeartbeat`).

New finding:
3. **Should fix: the owning documents still describe the old heartbeat.** `A16-intraday-quote-recorder.md` item 9
   (line 322) says `heartbeat.json` holds the last slot's fields, and lines 233-234 and 524 list the owned paths as
   `slots/`, `rv/`, `heartbeat.json`. The hand-commit command at line 446, and the same command in
   `A16-owner-checklist.md:50-55` (the routine's stored prompt), add `heartbeat.json` but not `last_mark.json`. A hand
   fix after "NOT committed" then leaves the mark file behind in a container that is about to end. Fix: update those
   lines in place, and tell the owner the stored prompt needs the new `git add` line (the owner edits routines, not a
   session).

Note: this is my second round. The rest is a text fix, so I ask the orchestrator to put a short reading check to
the owner (as was granted for O14 on 25 Oct), or the owner decides.
