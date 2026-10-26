# A16 heartbeat fix: one run's whole beat, never a mix

**Branch:** `story/a16-heartbeat-session` · **Lane:** 1 (a record the silence check reads) · **Owner:** builder
session_01KCcL6PhbgFzwxZfVyCRzoG; reported by the GW1 builder (session_01GsPm29fZzfH3DiErKAdBVk), 26 Oct 2026.

## Problem
On 26 Oct, `research/data/intraday/heartbeat.json` on main said session "2026-10-23", mark "09:30", while the slot rows
were of 2026-10-26, and its run times (09:15-09:29 IST) ended before the 09:30 mark.

## Root cause
Two overlapping recorder runs push the file. A run that took no mark copies the old file and changes only the run
times (A16 design 4.2); a run that took a mark changes mark, session and times. The pull settles a clash with `-X
theirs`, which decides **per hunk**, and the pretty-printed file had one line per field: the `mark` line (changed only by
one side) merged cleanly, the `session` and time lines (changed by both, adjacent) took the other side. Commits fa33262,
b21b2c1 and merge b32ffcb on main show it: mark 09:30 from one run, session 2026-10-23 and times from the other. The
next run (0df866f) then carried the mixed file on. No code path wrote a wrong session by itself.

## Fix
`Heartbeat.write` writes one line of JSON. Any clash is then a whole-file clash and `-X theirs` keeps one run's own
beat. Readers parse JSON, so nothing else changes.

## Impact on readers (checked in code)
- Silence check (`heartbeat_state`, `intraday heartbeat-check`) reads only `run_finished_at`, always a real run's
  finish; the mix never made it silent or ok wrongly, beyond a finish up to one run's length older than the newest.
  No false or missed silence alert is traceable to it.
- LM1 and every other module under `fno/` never read the heartbeat (grep: only `fno/intraday/`); the slot ledger,
  not the heartbeat, decides the day. `session` and `mark` are for people and carry the last mark taken.
- Not changed: a run that took no mark still shows the last taken mark's session (by design); the clash can still pick
  an older finish time; both are cosmetic for the silence check.

## Claims
1. `tests/intraday/test_heartbeat_merge.py` reproduces the mix with two clones (fails on the old indented writer,
   passes now): the published beat equals one run's whole beat.
2. The silence check and `run_finished_at` semantics are unchanged (`tests/intraday/test_clock_and_heartbeat.py`).
3. Gates: ruff check, ruff format --check, `tools/check_imports.py`, full pytest (results in the commit message).
