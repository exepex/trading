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
Quotes after a 429 are paced even when refused, so the first pass always ends at F (the chain calls plus the quotes at
4 a second), wherever the 429 falls. The pause ends 60.5 s after the 429 and the retries need the quotes refused since
(F minus the 429's moment) at 4 a second, so the retry ends at F + 60.5 s whatever the moment, and the quotes that
cannot start before 120 s stay unasked:

**lost = 4 x (F + 60.5 - 120) quotes, when positive.** The test sweeps it: the same loss for a 429 at the 10th, 60th and
120th quote, and 0, 1, 9, 17 lost for 0, 2, 4, 6 s of chain calls in the harness (228 quotes).

The case judge S measured: 5 s of chain calls and 228 quotes lose 12 (0 at 2 s, 8 at 4 s, 16 at 6 s); the real marks ask
216-220 quotes, a few fewer than the harness.

On real marks (54 good marks of 27-29 Oct, raw files in Drive; first quote sent 3.6-6.6 s after the mark, median 4.3 s;
216-220 quotes): the last quote was sent 59.5 s after the mark at the median (57.9 to 74.2 s), so a 429 would have
lost a median of about 1 quote, at most 7 for 9 marks in 10, and 41% would lose none. A slow mark (one mark ran
74 s) loses many. This is an estimate from the good marks' timings; no real 429 mark can be replayed. Those quotes are
named `QuietWindowEnded`; the mark stays `incomplete` by that handful instead of by up to 117. Lowering the 0.5 s
margin, a shorter chain prelude, a longer quiet window or a lower pace would change F or the 120 s; they are GW1's and
the orchestrator's decisions, not built here.

## Claims
1. `tests/intraday/test_429_recovery.py` runs the real guard (`RateGuardedGroww`, `RateLimitPause`) under the real source
   on one simulated timeline. A 429 after 91 quotes (the 29 Oct 10:15 shape, no chain delay): the old behaviour lost 103
   of 228 (checked by disabling the wait), now 0 are lost. With a realistic chain prelude the loss follows the formula
   above (claim 3b).
2. No call is sent inside the pause (checked from the call times) and none at or after 120 s, for 429s at the first
   quote, the 5th, 30th, 50th, 150th and 226th.
3. Worst case, a 429 on the first quote after 5 s of chain calls: the retry fits as many quotes as the window allows
   (computed from the pause end), the rest are `QuietWindowEnded`.
3b. `test_the_loss_is_set_by_when_the_first_pass_ends_wherever_the_429_falls`: at 0, 2, 4 and 6 s of chain calls, a 429
   at the 10th, 60th and 120th quote loses the formula's number (within 2) and the same number for all three.
3c. `test_a_429_inside_the_retry_pass_keeps_the_first_in_the_notes_and_refuses_the_rest`: a second 429 in the retry pass
   leaves the note on the first and costs the quotes behind it (the retry pass is not repeated).
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
8. Harness (judge 693 addendum 2, orchestrator 29 Oct): the tests run on `tests/intraday/sim_429.py`. Every pool thread
   keeps its own simulated time (its pacer slot, its own answer times) and a call's number is its pacer slot, so thread
   scheduling cannot move a send time or a count. Real time only gates when a thread checks the guard: every call
   numbered before the first 429 is inside Groww before it is answered, later calls wait until the source has noted it
   (the guard has then started its pause). The earlier harness read one shared clock from several threads and drifted
   (3, 1 and 6 failures in 48 loaded runs). Now 1,120 loaded runs of the whole file (12 and 16 processes at once on 4
   CPUs) have no failure; the plants (no wait, margin -2 s, no skip, overwriting the first 429, keeping the first pause
   end) are each caught.
8b. The race is in the test, not in production. In `_call` the time that is checked against the window is the very
   `sent` value stored in the record (`request_sent_at`); the fake API had read the shared clock a second time. The new
   state (`_pause_ends`, `_first_429`) is written under a lock by pool threads and read by the taking thread only after
   `pool.map` has returned, i.e. after every future finished, and `take` runs one mark at a time. The unchanged GW1
   gap remains: a call is stamped just before it is sent, so a call stamped at 119.99 s can reach Groww after 120 s by
   microseconds to milliseconds.
9. Gates: ruff check, ruff format --check, `tools/check_imports.py`, full pytest (results in the commit message).
