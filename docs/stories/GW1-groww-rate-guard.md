# Story GW1: Groww's rate limits are never exceeded, for any reason, in any situation

Owner: builder session_01GsPm29fZzfH3DiErKAdBVk, from orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH (25 Oct 2026).
Lane 1 (an outside service). Owner, 25 Oct: "make sure it does not make Groww API go over rate limit in any reason or
in any situation". Deadline: part 1 before Mon 26 Oct 08:22 IST (A16's first fire); the rest before 14:00 IST Monday
where possible.

## Groww's limits (strong evidence: research/school/probes/2026-10-22-p0-1-groww-chain.md:100-112)

- Live Data (quote, LTP, OHLC): 10 a second and 300 a minute. Sign-in (`/v1/token/api/access`): 5 a second, 30 a
  minute **and 150 per 24 hours**. The probe does not say whether the limits are per key or per user, so this story
  treats every session on the owner's account as sharing one budget.
- Before GW1, A16 alone paced at 5 a second, which is 300 a minute: the whole Live Data cap. GW1 paces it at 4
  (`fno/intraday/groww_source.py:30`).
  During an A16 mark (about 85 s from each :00, :15, :30 and :45) any other Groww read goes over the cap.

## What is wrong today (strong evidence: the code at a54f1016)

- **No limiter shared across sessions.** Each scheduled routine runs in its own container. `RatePacer`
   (`fno/intraday/pacing.py`) is per process, so nothing stops two processes at full speed in the same minute. Known
   overlaps with an A16 mark: 14:30 (the `v4` capture), 15:00-15:01:30 (a NIFTY retry and A4c at 15:01) and 15:15
   (E3's execution capture). On 22 Oct, 4 quotes failed at 15:15.
- The sign-in storm, the hidden 429, the raw SDK client and the missing 429 stop: [GW1a](GW1a-groww-guard-core.md).
- **A16's claim.** A run whose claim push fails takes the mark anyway (`fno/intraday/claims.py:5`), so two blind
   runs can take one mark at 10 a second.

## Frozen files (protocol v4's freeze, FREEZE_v4.md on story/v4-freeze)

The fix changes no byte-checked file. The frozen files include `fno/quotes/recorder.py`, `book_fetch.py`,
`future_quotes.py`, `fno/composition.py`, `fno/intraday/wiring.py`, `pacing.py`, `backfill_wiring.py`,
`fno/providers/base.py` and `fno/config.py`. Every change sits in Groww's adapter instead: `fno/providers/groww.py`,
new modules beside it, and `get_provider`. This changes how frozen callers behave at run time without changing their
bytes. The orchestrator allowed it (25 Oct, Q1): frozen callers' behaviour changes only in timing (when a call
starts), sign-in back-off, read-only wrapping and error class names, never in a recorded value. The orchestrator tells
judge B. The `v4` capture's start moves to 14:32 inside the freeze itself (the freeze builder,
session_019rZrcu1GSqUC7PScqwQgo2, changes `quotes.windows.v4.start` and the protocol's wording); GW1 does not touch
it.

## The rule

Parts 1-4 (sign-in guard, read-only client, 429 named, 60 s stop) are on main and owned by
[GW1a](GW1a-groww-guard-core.md); this story builds on them unchanged.

5. **Quiet windows for A16's marks (part 5; orchestrator, Q4 and Q5).** For providers built through `get_provider`
   (the 3 pm NIFTY, `v4`, A4c and E3's execution capture) a quiet window runs from each A16 mark to 120 s after it
   (`fno/providers/groww_quiet_windows.py`, A16's own `marks()`). An attempt that starts inside one waits for its end
   before its first call (`GrowwProvider.expiries`, the first Groww call of every A4 attempt). Any other call inside
   one is refused unsent (`GrowwQuietWindow`). A call is never delayed after its caller stamped its send time (A4's
   frozen fetcher stamps before it asks), so every recorded time stays true: a refused call is a recorded failure,
   and its recorder's own retry follows. A16, the pre-open capture and A16b build `GrowwProvider` directly and are
   never held. `groww-check` and the feed probe's REST client are built through `get_provider` too (round 2, judge
   637 m2). Effects: A4c's first call moves from 15:01 to 15:02:00, and E3's capture (config
   `desk.execution_snapshot` 15:15, unchanged) asks from 15:17:00. Its record's `started_at` stays 15:15, when the
   attempt began waiting. The `v4` capture at 14:32 is never held; the rule stays on it as a belt. A NIFTY retry
   still running at 15:00 ends incomplete there, and the next one starts at 15:02:00. Why 120 s: A16's marks took
   48-58 s to record on 20-23 Oct, and 83 s at most (78 committed slot rows, `first_seen_at` minus the mark; strong
   evidence).
6. **One A16 taker per mark, fast only inside its window (part 6, round 2; judge 637 SF1 and SF2).**
   - A run whose claim did not reach GitHub (`unclaimed`) tries once more 15 s later. If that also fails, it does not
     take the mark (`ClaimResult.take` is `won` only) and says so ("claim not pushed ... not taken here").
   - A retry counts only once GitHub has the claim. The first try left the claim committed locally, so the committer
     now answers "nothing new to commit". The claim then pushes what is committed (`GitManifestRecorder.publish`) and
     is `won` only when that push lands, `lost` when the push brings another run's claim. Round 2's own review found
     the first version reading "nothing new to commit" as pushed: a blind taker at full pace.
   - Why not take it slowly (round 1's 1 a second): up to three A16 fires are alive at one mark (each lives to about
     2h45m, one fire an hour). One `won` at 4 plus two `unclaimed` at 1 each is 6 a second. With no blind taker,
     git's first-push-wins leaves exactly one taker, whatever the number of runs.
   - Cost: a mark is lost only when every living run fails to push its claim, which in practice means GitHub is down.
     Before GW1 such a mark was taken, by every run.
   - Groww's source paces every call of a mark at 4 a second, before its send time is taken: the index, the future,
     the chains, the candle and the quotes.
   - It asks nothing at or after the end of the mark's 120 s quiet window (mark + `QUIET_SECONDS`, imported). A call
     whose turn comes later is recorded unasked as `QuietWindowEnded` (round 2, judge 638 finding 2; `_retry_failed`
     goes through the same call).
   - The window runs from the mark, not from the take's start, so a mark taken late (up to `ON_TIME_SECONDS`, 120 s)
     has only what is left of it (judge 637 SF2). A mark taken after it asks nothing.
   - The cost is a slow day's tail: quotes not asked by mark + 120 s are missing, and the mark is incomplete (its
     realised-variance input, the index, goes first). A16's marks took 48-58 s on 20-23 Oct, 83 s at most at 5 a
     second (about 63 and 101 s at 4).

## Known limits (said plainly)

- **E3 and `desk.fills_by` (judge 638 finding 1).** My round-1 text, "`fills_by` limits only a rerun", was wrong.
  - `fills_by` also ends the capture's window: execution_capture.py:78 reads its record in
    `execution_snapshot`..`fills_by`, and C3's `SnapshotInWindow` (snapshot_checks.py:30) refuses a snapshot that
    finished later, so nothing fills from it and exits are not taken from it.
  - E3's four committed captures took 2m35s-2m57s. Asked from 15:17:00, they would end at 15:19:35-15:19:57, only
    3-25 s before 15:20.
  - **The orchestrator's decision (25 Oct):** `execution_snapshot` stays 15:15 and `fills_by` moves to 15:23
    (config.yaml). That covers the longest capture (2m57s) plus one 60 s 429 pause plus 60 s:
    `test_e3s_capture_ends_before_fills_by_with_a_pause_and_a_minute_to_spare` pins it.
  - Every reader of `fills_by`:
    - execution_capture.py:78 and C3 (above): the window widens by 3 minutes.
    - daily_run.py:256: a rerun that did not take the snapshot may fill until 15:23, not 15:20. This widens the
      owner's 24 Oct rule ("no fills after fills_by") by 3 minutes.
    - runner._finish_parts: only after a stop, waiting for busy 3 pm parts, which end by 15:13.
    - The timetable's order check (`fills_by` after `execution_snapshot`).
    - The tests that pinned 15:20 now read it from the config.
    - Nothing in a normal run waits for `fills_by`: `quotes_done` waits only for the 3 pm parts, and the desk's steps
      run at `execution_snapshot`.
  - **The school** (SCHOOL_STARTS_BY 15:25) starts about 80 s after the snapshot step ends (22-23 Oct run logs), and
    that step ends about 13 s after the capture. Worst single capture with a pause: 15:17:00 + 2m57s + 60 s + 13 s +
    80 s = 15:22:30 (`test_the_school_still_starts_by_its_limit_after_that_capture`).
  - **Not covered: E3's common retry.** On 22 Oct the first attempt (15:15-15:18:10) was incomplete and the retry ran
    15:18:24-15:21:10, already past 15:20 before GW1 (the day's snapshot was invalid). Under GW1 a retry would end
    about 15:23:07, past 15:23, and the school would start about 15:24:30, or past 15:25 with a pause. In short: a day
    needing E3's retry may end past `fills_by`, so no new desk trade that day, as before GW1. The orchestrator kept
    15:23 (25 Oct): 15:25 would push the school to TOO_LATE on more days. The value goes to the owner with the round-3
    request, since it widens the owner's 24 Oct rerun rule.
- No Groww reader outside `get_provider` gets the quiet windows. A new reader must be built through `get_provider`
  (MS-P0b is) or keep out of A16's marks by its own schedule. The pre-open capture (08:40-09:11) and A16b's candles
  (15:33, 2 a second) build `GrowwProvider` directly. Each runs outside A16's windows, where A16 asks nothing.
- A16's `prepare` asks for the session's expiry list once a session (two `get_expiries`, unpaced), before its first
  claim. It is outside every window and beside one other reader at most: 2 calls plus 2.5 a second. It is A16's only
  Groww call outside a mark's window.
- A claim committed locally while GitHub was out is pushed later by the run's own sync. If it lands inside the mark's
  window before any other run claimed, a later fire sees `lost` and the mark is taken by nobody. That costs a mark,
  never the limit.
- **The unpaced readers stay under the limit only because Groww is slow (judge 637 m3).** The 3 pm NIFTY, `v4` and
  E3 captures ask one quote at a time with no pacer: 54-71 a minute measured (12 sidecars, 15-23 Oct). A Groww that
  answered in 0.2 s would make one of them 5 a second. Pacing
  them needs the frozen A4 slot (`fno/quotes/slot.py`, `per_second`): not done here.
- **E8's stand-in fill snapshot moves later (judge 637 SF3).** When A16's 15:15 mark is missing, E8 prices a
  "15:15" exit from E3's capture, whose `started_at` stays 15:15 (`fno/desk/owner_timing/mark_snapshots.py:90-96`).
  Under GW1 every one of its quotes is asked 15:17:00-15:19:34 (it was 15:15:00-15:17:34), so such a fill is priced
  120-274 s after the mark instead of 0-154 s. E8 is not live. The orchestrator tells E8's owner, who either drops
  stand-in quotes asked after mark + 120 s or accepts it.
- There is still no cross-process limiter. Separation is by the clock (rule 5) plus the fast stop (rule 4). Two
  processes started by hand at the same time can still exceed the cap until the first 429 stops them.
- The sign-in cap's limit: see [GW1a's known limits](GW1a-groww-guard-core.md#known-limits).
- Whether Groww's limits are per key or per account is unknown (the probe found no statement). Another app or person
  using the owner's Groww account at the same time would share the budget unseen.
- How Groww counts "a minute" (a fixed clock minute or a sliding 60 s) is unknown. 300 a minute is read as at most 5
  a second averaged over any 60 s, which the paces above keep in either reading.
- **Dependency:** the `v4` capture must never start before the 14:30 mark's quiet window ends (14:32:00 with the
  120 s window). Its first call would wait and the rest be refused. `quotes.windows.v4.start` is "14:32" on main
  (the freeze builder, 25 Oct), and
  `tests/test_groww_quiet_windows.py::test_the_v4_captures_configured_start_is_outside_every_a16_quiet_window` fails if it is
  ever moved earlier (planted: "14:31" is caught).

## Acceptance

Criteria for parts 1-4: [GW1a's acceptance](GW1a-groww-guard-core.md#acceptance).

6. Through `get_provider`, an attempt starting at 14:30:10 asks from 14:32:00, at 15:00:00 from 15:02:00, at
   15:01:59 one second later and at 15:15:00 from 15:17:00. At 15:02:00, 14:32:00, 09:14:59 and 15:32:00 it does not
   wait. Any other call at the waiting times is refused unsent and never delayed. A16's directly built provider is
   never held.
7. A16 takes no `unclaimed` mark: a claim failing twice leaves 09:15 untaken ("missed", "claim not pushed"), and
   09:30, claimed, is taken. A claim landing on its retry is taken. Groww's source paces every call at 4 a second and
   asks none at or after mark + 120 s, recording the rest `QuietWindowEnded`. Cases: an on-time mark (all asked), a
   slow mark, a mark taken 110 s late (the index asked) and a mark taken after its window (nothing asked), in
   `tests/intraday/test_gw1_pacing.py`. Every set of readers that can overlap sums to 5 a second or less
   (`test_no_set_of_readers_that_can_overlap_exceeds_five_a_second`, one case per row of the table below).
8. E3's longest capture asked from 15:17:00, plus one 60 s pause, plus 60 s, ends by `fills_by`. The school then
   still starts by 15:25.
9. Each criterion fails when its code is broken on purpose (mutation per criterion). The full suite passes.

## Every set of readers that can overlap (round 2)

All rates are per second. Groww's Live Data limits are 10 a second and 300 a minute. Over a minute, 300 averages 5
a second, so every row must stay at or under 5 a second (well under the 10 a second cap). Every row is one test case.

| When | Readers | Rate |
|---|---|---|
| Inside an A16 window (mark to mark + 120 s) | A16 alone (one taker; every `get_provider` reader refused) | 4 |
| 14:32-14:40 | the `v4` capture (A16 asks nothing outside its windows) | 1.2 |
| 14:55-15:10 | the 3 pm NIFTY capture | 1.2 |
| 15:02-15:13 | A4c (starts after NIFTY ends) | 2.5 |
| 15:17-15:23 | E3's capture (A4c ended at 15:13) | 1.2 |
| 15:33 | A16b's candles | 2 |

A16's own fires never add up: one `won` run takes a mark, and the others (`lost` or `unclaimed`) take nothing. A16
asks nothing outside its windows, so each reader there is alone. The orderings the table relies on are asserted from
the code (`test_the_orderings_the_table_relies_on_hold_in_the_code`):
- A4c starts after NIFTY's part has ended (`fno/daily/quote_parts.py`, `starts_after`);
- v4's 14:40 end comes before NIFTY's 14:55 start;
- E3's first call at 15:17 comes after A4c's 15:13 and NIFTY's 15:10 ends.

The 1.2 is measured, not a pacer (see the known limits).

## Claims

### Round 2 (judges 637 K and 638 I; the orchestrator accepted every finding)

- Head be5ec337e plus a test: pytest -n auto on the merge with main (795588136) 16824 passed, 1 skipped, 13 xfailed;
  ruff check and format, check_imports, check_records and check_numbers clean.

- Parts 1-4 merge alone as GW1a (`story/gw1a-groww-guard-core`, `docs/stories/GW1a-groww-guard-core.md`; the
  orchestrator's split, 25 Oct). This branch keeps them unchanged.

- Gates: pytest -n auto 16632 passed, 1 skipped, 13 xfailed (fresh bytecode); ruff check and format, check_imports and
  check_records clean.

- **SF1 (limit a), fixed.** One A16 taker per mark: an `unclaimed` run takes nothing (rule 6). Round 1's slow pace
  for it was not enough: up to three A16 fires are alive at one mark, so `won` 4 plus two `unclaimed` at 1 each is 6.
  The table of every set of readers is one test case per row (`tests/intraday/test_gw1_pacing.py`).
- **SF2 (late or long mark) and judge 638 finding 2, fixed.** A16 asks nothing at or after mark + `QUIET_SECONDS`
  and records the rest unasked (rule 6). Tests: a slow mark, a mark taken 110 s late, a mark taken after its window
  (`tests/intraday/test_gw1_pacing.py`). The first round-2 head paced 1 a second after the window instead; judge I and
  the orchestrator chose the stop.
- **Judge 638 finding 1 (E3 and `fills_by`), fixed:** `fills_by` 15:23, every reader listed and the school's start
  checked under Known limits, with the margin pinned by a test. E3's common retry is not covered (stated there).
- **SF3 (E8), stated** under Known limits; the orchestrator tells E8's owner.
- **m1, fixed.** Tries cut to 3 a process and token day. About 38 processes a session day (rule 1's count), so at
  worst 114 tries.
- **m2, fixed.** `groww-check` and the feed probe's REST client are built through `get_provider`.
- **m3, stated** under Known limits; pacing them needs the frozen `slot.py`.
- **Own review of round 2 (an independent agent), both fixed:**
  - HIGH: the claim retry read "nothing new to commit" as pushed. It now pushes and counts only a landed push. Tests
    use real git: GitHub out on both tries stays `unclaimed`; restored, it is `won` and on GitHub; meeting another
    run's pushed claim, it is `lost`.
  - MEDIUM: fast starts booked past the window's end. Fixed then with a 1 s lead; now no request starts after the
    window at all (the check comes after the pacer's wait, right before the send).
  - Its low items, all addressed:
    - A16's unpaced calls are now paced.
    - The table's orderings are asserted from the code.
    - The feed wiring test checks the provider name.
    - A claim pushed late is stated under Known limits.
  - It also found stale bytecode from my round-1 mutation runs, which held a mutant (`TRIES_A_DAY` 4). The cause of
    the one failing test in my first round-2 run. The caches were deleted, and round 2's mutations ran with
    `PYTHONDONTWRITEBYTECODE=1`.
- Round 2 mutations, each caught:
  - Claims:
    - no publish on retry;
    - "nothing new" read as pushed;
    - `take` back to "not lost";
    - no claim retry;
    - the 4th sign-in try.
  - Pacing:
    - no stop at the window's end;
    - the stop at one second past it (`>` for `>=`);
    - an unpaced call;
    - the send time stamped before the pacer's wait (judge 638 addendum 1's survivor J3; now caught by
      `test_a_calls_send_time_is_taken_after_its_pacer_wait`);
    - `fills_by` back at 15:20;
    - A16's fast pace back at 5 a second (judge 637.1's survivor; `test_a16s_pace_leaves_headroom_under_three_hundred_a_minute`);
    - `execution_snapshot` at 15:18 (no room left).
  - Wiring:
    - A4c not after NIFTY;
    - `groww-check` and the feed probe built directly.

### Round 1

- Parts 1-4's claims (code, tests, mutations, gates, output sample) are in [GW1a](GW1a-groww-guard-core.md#claims).
- Round 1's own review found that a wait inside any call would record A4's send times up to 90 s early (its frozen
  fetcher stamps before it asks). It was fixed before review: the quiet window waits only before an attempt's first
  call and refuses the rest.
- Quiet-window output sample (the committed code, a stand-in clock; no value):

```
attempt at 15:00:20 waits [100.0] s; another call then: Groww call refused unsent: inside A16's 15:00 mark until 15:02:00 IST
```
