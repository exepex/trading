# A16 429 recovery: wait out GW1a's pause, keep the first 429

**Branch:** `story/a16-429-recovery` · **Lane:** 1 (a Groww caller and the slot records) · **Owner:** builder
session_01KCcL6PhbgFzwxZfVyCRzoG; orchestrator go 29 Oct 2026 for items (a) and (b) only (diagnosis in the orchestrator
thread). Apart from `story/a16-heartbeat-session`. **Judges:** R and S.

## Problem
Since GW1a (25 Oct) one Groww 429 stops every call of the process for 60 s (`fno/providers/groww_rate_guard.py`).
A16 asks 4 quotes a second, so its first pass always lasts about 60 s whether or not calls are sent, and the single
retry pass (`_retry_failed`) starts inside the pause: every quote it asks before the pause ends is refused unsent
(`GrowwRateLimitPaused`) and stays lost. 21 of 104 marks on 26-29 Oct were incomplete, 19 of them this way (23-117
quotes lost; 29 Oct 10:15: 112 of 220). The retry also overwrote the first pass's record, so the raw file never showed
which call got the 429 or when.

## Fix
(a) The mark's notes keep the first 429: `first_429: <call> sent <time> answered <time> <class:code>` (never Groww's text).
(b) `_retry_failed` first waits out the pause: the latest 429's answer time + `PAUSE_SECONDS` (the guard's own
constant) + 0.5 s. It sleeps (never calls) for the rest of it, then retries at the same pace as before (4 a second,
4 workers, the same pacer). When the pause would end at or after the mark's quiet window (120 s) nothing could be asked,
so the retry is skipped and the note `quotes_retry_skipped` says why. A failure that is not a 429 is retried at once,
as before. No other change: no new call, no faster pace, the window check in `_call` is untouched.

## What it can and cannot recover
The work of a 429 mark is about 5 s of chain calls + 55 s of quotes + 60 s of pause = 120 s, exactly the quiet window.
So a 429 costs nothing but time when the first pass ends by about 59 s, and the last 0-4 quotes (the tail of the sorted
contract list, far strikes of the second chain) stay unasked when it ends later (observed 58-60.6 s). Those are named
`QuietWindowEnded`, the mark is still `incomplete`, but by a handful of quotes instead of up to 117. Raising the window
or the pace is GW1's decision (not built here).

## Claims
1. `tests/intraday/test_429_recovery.py` runs the real guard (`RateGuardedGroww`, `RateLimitPause`) under the real source
   on one simulated timeline. A 429 after 91 quotes (the 29 Oct 10:15 shape): the old behaviour lost 103 of 228 (checked by
   disabling the wait), now 0 are lost.
2. No call is sent inside the pause (checked from the call times) and none at or after 120 s, for 429s at the first
   quote, the 5th, 30th, 50th, 150th and 226th.
3. Worst case, a 429 on the first quote after 5 s of chain calls: the retry fits as many quotes as the window allows
   (computed from the pause end), the rest are `QuietWindowEnded`.
4. The pace never exceeds 4 a second; a mark without a 429 and a non-429 failure are unchanged (no waits).
5. A late 429 whose pause ends after the window skips the retry and says so.
6. Several 429s (judge 693 should-fix 1): with 4 workers, calls in flight together meet the limit too, and each 429
   restarts the guard's pause. The test makes three calls in flight, answered 0.3 s apart under the real guard: the
   note names the first answered (not the last), nothing is sent between the first answer and the last pause's end
   (the source keeps the latest pause end), no refused quote is left, and the loss equals what the window allows after
   the last pause. Plants caught: overwriting `_first_429` on every 429, and keeping only the first pause end.
7. What reaches the repository (judge 693 minor 2): `doc.notes` go into the slot row's `failures` field in
   `research/data/intraday/slots/` as well as the raw file (this is how `quotes_retried:N` already travels). The two new
   notes add, once per mark with a 429, one contract symbol (a public instrument name, as in the 3 pm sidecars) with
   two timestamps and the code `GrowwRateLimited:429`; no Groww text, no value of a quote, no credential. Quotes are
   still counted, not listed, in the row. The record scan stays on.
8. Gates: ruff check, ruff format --check, `tools/check_imports.py`, full pytest (results in the commit message).
