# Judge 638: GW1, Groww's rate limits never exceeded (story/gw1-groww-rate-guard at 01477b7cf), judge I

**FAIL, lane 1.** Round 1 of 2. Judge I (1 of 2; K is the other, not consulted), own session
(session_01CHtddAzFcEdQh4HFiz3mqU), 25 Oct 2026. Judged: GW1's own commits 9761da9cc, 5d5d054ae, 6ddc597b8 and
01477b7cf; f1a94bbeb only merges main. Owner, 25 Oct: never over Groww's limit "in any reason or in any situation".

## Checks

| Check | Verdict | My evidence |
|---|---|---|
| P1 sign-in back-off | MET | `GrowwSignIn`: failure remembered, 5/10/20/30 min, at most 6 a token day, every call in between refused unsent, one alert (class name only) sent outside the lock. G1, G2, G11, G15 caught |
| P2 read-only | MET | `api` is `ReadOnlyGroww` over the guard (orders refused); raw client only through `feed_client()` for the feed probe. G10/H8 caught |
| P3 one 429 detector | MET | the installed SDK: `GrowwAPIRateLimitException.__init__` passes code `"429"` to `GrowwAPIException`, so `is_rate_limit` (`.code == "429"`) catches both forms; Groww's text dropped. G3, G14 caught |
| P4 60 s pause | MET | `RateLimitPause` shared by the provider's threads; A4's attempt stops at its first 429. G4 caught |
| Frozen v4 files | MET | none of FREEZE_v4.md's 232 paths is in GW1's diff (my script); `v4.start` 14:32 is pinned by the new test (my H5 plant, "14:31", caught) |
| Recorded values | MET, with a note | A wait happens only before an attempt's first call; later calls are refused, never delayed, so send times are true. `started_at` stays the attempt's start (15:15:00 for E3) while its first quote is asked at 15:17:00 (note) |
| Rates, any two takers (question 1) | PARTLY | Limit (a) is closed at 6ddc597b8: 4 + 1 and 1 + 1 a second. Measured paces: NIFTY 3 pm about 1.2/s (180 contracts in 155 s, 23 Oct sidecar); A4c 2.5/s paced (`indices.py:25`), ending by 15:06 (12 sidecars of 19-23 Oct). The guarantee still rests on A16 ending inside 120 s (finding 2) |
| New timings (question 3) | PARTLY | A4c from 15:02:00 still ends well before its 15:13 end. NIFTY retries: a 15:00 attempt ends incomplete and the next starts 15:02:00. E3: finding 1 |
| Readers outside `get_provider` (question 4) | MET | pre-open ends by 09:11, before the first mark at 09:15 (`marks()`); A16b at 15:33 is after 15:32:00; A16 and the feed probe build their own (no quiet window, by design) |

## Findings

1. **Should-fix (money path, strong evidence): E3's capture now ends 3-25 s before C3 refuses it, and the story's
   statement about `fills_by` is wrong.**
   - "`desk.fills_by` (15:20) limits only a rerun" is false. The capture window is `execution_snapshot`..`fills_by`
     (`fno/desk/execution_capture.py:78`), and C3's `SnapshotInWindow` refuses any snapshot whose `finished_at` is
     after its end (`fno/checks/snapshot_checks.py:30`).
   - The four committed captures took 2m57s (19 Oct), 2m48s (21 Oct), 2m46s (22 Oct) and 2m35s (23 Oct). Asking from
     15:17:00, they end at 15:19:57, 15:19:48, 15:19:46 and 15:19:35. Before GW1 the margin was over 2 minutes.
   - One slow round, one 60 s 429 pause, or the recorder's own retry puts it past 15:20. C3 then marks the prices
     unverified: no new trade that day, and exits not taken from it (`fno/desk/exits.py:12`).
   - Fix expected: correct the text, and restore a margin that holds the longest recorded capture plus one 60 s
     pause. Options: move `desk.fills_by`, or `desk.execution_snapshot`, or end A16's 15:15 mark sooner. These are
     lane-1 config and desk timing, so the orchestrator or the owner decides; a test pins the margin.
2. **Should-fix (the owner's rule): nothing ends a claimed A16 mark at its quiet window's end.**
   - The 4 + 1 sum keeps A16 apart from A4, E3 and v4 only while the claimed run finishes inside 120 s. The builder's
     own estimate is 101 s at worst, from 4 days of rows.
   - `_retry_failed` re-asks every failed quote at the same pace, calls may each take up to the 10 s timeout, and
     there is no deadline in `GrowwIntradaySource.take` or the recorder.
   - A longer mark overlaps E3 (about 1.2/s), A4c (2.5/s) or v4: 5.2-6.5 a second, over 300 a minute.
   - Fix expected: a claimed take stops asking at mark + `QUIET_SECONDS` (imported), its unasked quotes recorded as
     failures; a test with a slow fake source. (An unclaimed run at 1/s may run longer: 1 + 2.5 stays under 5.)

## Plants

24, each restored and caught, tree clean after each: G1-G16 on 5d5d054ae (back-off, day cap, 429 translation, pause,
quiet check, wait, window, paces, read-only, alert text, next-year 429, wiring); H1-H8 on 01477b7cf (window 90 s,
unclaimed 2/s, claimed 5/s, no sharing, v4 at 14:31, no quiet check, day cap 60, raw client).

## Gates

- 5d5d054ae merged with main c709f11c3 (FNO_SLACK_BOT_TOKEN kept): pytest -n auto 16616 passed, 0 failed; ruff,
  format, `check_imports` and `check_records` clean. Slack in that window: only labelled rehearsal posts.
- 01477b7cf merged with main cbd3937a4 as 897f93842: ruff clean, 2640 files formatted, `check_imports` clean. The
  focused suites passed; pytest -n auto (token kept) 16634 passed, 13 xfailed, 0 failed (581 s). No Slack post in that
  window on any of the three channels.

## Notes (not findings)

- "Any situation" needs a limiter shared across processes: a hand-run Groww command, or another app on the account,
  shares the budget unseen. For the owner: accept, or no hand-run Groww command 09:15-15:35 IST.
- Nothing found in parts 1-4. If part 1 must be on `main` before Mon 08:22 IST, a head of parts 1-4 alone is quick.
