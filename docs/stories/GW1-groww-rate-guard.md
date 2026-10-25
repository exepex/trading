# Story GW1: Groww's rate limits are never exceeded, for any reason, in any situation

Owner: builder session_01GsPm29fZzfH3DiErKAdBVk, from orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH (25 Oct 2026).
Lane 1 (an outside service). Owner, 25 Oct: "make sure it does not make Groww API go over rate limit in any reason or
in any situation". Deadline: part 1 before Mon 26 Oct 08:22 IST (A16's first fire); the rest before 14:00 IST Monday
where possible.

## Groww's limits (strong evidence: research/school/probes/2026-10-22-p0-1-groww-chain.md:100-112)

- Live Data (quote, LTP, OHLC): 10 a second and 300 a minute. Sign-in (`/v1/token/api/access`): 5 a second, 30 a
  minute **and 150 per 24 hours**. The probe does not say whether the limits are per key or per user, so this story
  treats every session on the owner's account as sharing one budget.
- A16 alone paces at 5 a second (`fno/intraday/groww_source.py:26`), which is 300 a minute, the whole Live Data cap.
  During an A16 mark (about 85 s from each :00, :15, :30 and :45) any other Groww read goes over the cap.

## What is wrong today (strong evidence: the code at a54f1016)

1. **Sign-in storm.** `GrowwProvider.api` (`fno/providers/groww.py:139-145`) sets `_api` only after a successful
   sign-in, so after a failed one every later call signs in again. An A16 mark makes 3-6 calls before it gives up
   (prepare, index, candle, expiry plan), so 26-30 marks make about 160-210 sign-ins a day. That is over the cap of
   150 per 24 hours, and the lock-out can last into the next morning.
2. **No limiter shared across sessions.** Each scheduled routine runs in its own container. `RatePacer`
   (`fno/intraday/pacing.py`) is per process, so nothing stops two processes at full speed in the same minute. Known
   overlaps with an A16 mark: 14:30 (the `v4` capture), 15:00-15:01:30 (a NIFTY retry and A4c at 15:01) and 15:15
   (E3's execution capture). On 22 Oct, 4 quotes failed at 15:15.
3. **A 429 is invisible in A4's sidecars.** With SDK 1.5, Groww's rate-limit answer arrives as `status: FAILURE` with
   code `429`, and the SDK raises it as a plain `GrowwAPIException`. A4's `withheld()` keeps only the class name, so
   the sidecars on file read "GrowwAPIException (provider message withheld)" (4 of them).
4. **Raw SDK client.** The 3 pm, `v4` and execution captures and `GrowwFutureQuotes` (`fno/quotes/future_quotes.py:31`)
   call the raw `GrowwAPI`, which can place, modify and cancel orders. Only A16, the pre-open capture and A16b use the
   `ReadOnlyGroww` allow-list (`fno/intraday/read_only.py`).
5. **A 429 does not stop an A4 attempt.** The attempt asks for every remaining contract anyway, so it burns the budget
   the other taker needs, and it is incomplete either way.
6. **A16's claim.** A run whose claim push fails takes the mark anyway (`fno/intraday/claims.py:5`), so two blind
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

1. **Sign-in guard (part 1).** `GrowwSignIn` (new `fno/providers/groww_sign_in.py`) owns the client of one process.
   - A successful sign-in is kept until the 06:00 IST token day ends, as today.
   - A failed sign-in is remembered. No new try is made for 5 minutes, then for 10 (tries at +0, +5 and +15 min).
   - At most 3 tries are made per process per token day (round 2, judge 637 m1: was 6).
   - Between tries, every call raises `GrowwSignInPaused` at once and reaches no network.
   - The first failure of a token day calls the injected `on_sign_in_failure` once, with the exception's class name
     only. `get_provider` wires it to a #fno-desk line. A caller that builds `GrowwProvider` directly gets no alert,
     but its own failure records name `GrowwSignInPaused`.
   - Worst case (judge 637 m1), about 38 processes on a session day:
     - A16's 7 fires each run up to 2h45m and are rerun at the tool's 2-hour limit, so up to 21 processes.
     - The daily run's Groww children (NIFTY, A4c, v4, E3, A16b) make 5, and 10 with a rerun.
     - The pre-open capture makes 1, the school's slots 4 and readers run by hand 2.
     - With every sign-in failing all day: 38 x 3 = 114 tries, under 150. A normal day: about 38 sign-ins.
2. **One read-only client for every caller (part 2).** `GrowwProvider.api` returns the `ReadOnlyGroww` allow-list over
   the guarded client, never the raw SDK. The feed probe alone needs the raw object (`GrowwFeed(groww_api)` reads its
   internals) and gets it through `feed_client()`, which the feed wiring alone calls.
3. **A 429 is named (part 3).** Groww's rate-limit answer, whether `GrowwAPIRateLimitException` or a
   `GrowwAPIException` with code `429`, is raised as `GrowwRateLimited`, a class of its own with `.code` `429` and
   none of Groww's text (`fno/providers/groww_rate_guard.py`; the SDK is an optional install). A4's sidecar
   then reads "GrowwRateLimited (provider message withheld)", and A16's `failure_name` reads "GrowwRateLimited:429".
   No message, URL or value is ever kept.
4. **Stop at the first 429 (part 4).** After a 429, the process's Groww read calls raise `GrowwRateLimitPause` without
   reaching the network for 60 s, Groww's per-minute window. A4's attempt then ends incomplete at once, and its own
   60 s retry gap follows. A16 gets the same pause (orchestrator, Q3): on a clash it loses the rest of that mark, the
   honest cost of not spending the budget the other taker needs.
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
    about 15:23:07, past 15:23, and the school would start about 15:24:30, or past 15:25 with a pause. Covering it
    needs a later `fills_by` and school start: the orchestrator's or the owner's call.
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
- The sign-in cap is per process. The day's total is bounded by the number of processes, not counted across them.
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

1. A failed sign-in is not retried within its back-off. Calls in between raise `GrowwSignInPaused` and the sign-in
   function is not called. The back-off doubles (5, then 10 minutes). The 4th try in a token day is never made. A new token
   day resets the count. A success is reused until 06:00 IST. Cases: good, bad, boundary (exactly at the back-off's
   end) and empty credentials.
2. The failure callback fires once per token day, with the class name only (a planted secret in the message never
   reaches it).
3. `GrowwProvider.api` refuses `place_order`, `modify_order` and `cancel_order` (`ReadOnlyViolation`, and the SDK
   stub is never touched). `chain`, `quote_book`, `expiries` and `GrowwFutureQuotes.quote` still work through it.
   `groww-check` works through it.
4. A `GrowwAPIException` with code `429`, and `GrowwAPIRateLimitException`, both arrive as `GrowwRateLimited`. A4's
   `withheld()` shows the name. Other errors pass through unchanged.
5. After a 429, the next call within 60 s raises `GrowwRateLimitPause` and the stub is not called. At 60 s it is called
   again. A4's attempt with a 429 at contract 3 of 20 asks Groww 3 times, not 20.
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

All rates are per second; Groww's limit is 5 a second, which is 300 a minute. Every row is one test case.

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

## Round 1's head: every taker paces for the worst pair (orchestrator, 25 Oct: a must-fix under the owner's rule; replaced in round 2 by one taker a mark)

The first version's pair (5 a second claimed, 2.5 unclaimed: 7.5 a second for one rare mark) broke the owner's "in any situation". A run cannot know it is alone, so every
taker paces for the worst pair: a claimed mark at 4 a second, an unclaimed one at 1 (4 + 1 = 5 and 1 + 1 = 2, both
within 300 a minute and 10 a second). Cost, estimated from 78 slot rows of 20-23 Oct at 5 a second (overhead about 9 s,
216-220 quotes): a mark takes about 63 s instead of 52 (median), and about 101 s instead of 83 at worst. The quiet
window grows from 90 to 120 s: A4c then asks from 15:02:00, E3 from 15:17:00 (ends near 15:19:34 at 23 Oct's 2 min 34
s), and the v4 capture at 14:32:00 sits exactly at the 14:30 window's end. An unclaimed mark at 1 a second spreads its
contract quotes over about 3.8 minutes (the index still goes first, so the realised variance is on time). It also
leaves A16 at 240 a minute, so its few unpaced calls (index, future, chains, candle) can never push a long mark over
300.

## Claims

### Round 2 (judges 637 K and 638 I; the orchestrator accepted every finding)

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
    - `fills_by` back at 15:20;
    - `execution_snapshot` at 15:18 (no room left).
  - Wiring:
    - A4c not after NIFTY;
    - `groww-check` and the feed probe built directly.

### Round 1

Round 1, parts 1-6:

- Code: `fno/providers/groww_sign_in.py` (rule 1), `fno/providers/groww_rate_guard.py` (rules 3-4),
  `fno/providers/groww_quiet_windows.py` (rule 5), `fno/providers/groww.py` (`api` is `ReadOnlyGroww` over
  `RateGuardedGroww` over `GrowwSignIn`; `feed_client()`), `fno/providers/__init__.py` (`get_provider` builds Groww
  with the sign-in alert and the quiet windows), `fno/intraday/feed_wiring.py` (`GrowwFeed(provider.feed_client())`),
  `fno/intraday/source.py`, `recorder.py` and `groww_source.py` (rule 6). No v4-frozen file changed.
- Round 1's own review found that a wait inside any call would record A4's send times up to 90 s early (its frozen
  fetcher stamps before it asks): fixed before review by waiting only before an attempt's first call and refusing the
  rest.
- An independent review agent on the diff found that same send-time error (it read the earlier version) and two
  low items, both fixed: a 429 on the next-year expiry call was swallowed by `listed_expiries`, hiding the cause
  (now re-raised); the sign-in alert was sent while the sign-in lock was held (now sent after its release). It found
  no order path, no caller broken by the wrapper and no leak of Groww's text.
- Tests: `tests/test_groww_guard.py` and `tests/test_groww_quiet_windows.py` (acceptance 1-6: good, bad, boundary and empty cases),
  `tests/intraday/test_o9_one_taker.py` (acceptance 7), `tests/test_groww_provider.py` (the 06:00 renewal and the
  expiry list through the new client), `tests/groww_sdk_fake.py` (a stand-in SDK that records sign-ins and calls).
- Gates at round 1's head (01477b7cf): pytest -n auto 16617 passed, 1 skipped, 13 xfailed; ruff check and format, check_imports and
  check_records clean.
- Mutations, each caught: no back-off check; an alert on every failure; no doubling; no day cap; `api` without the
  allow-list; no 429 translation; no pause check; Groww's text carried on; `get_provider` without the alert; without
  the quiet windows; the mark itself outside its window; no refusal check; no wait before an attempt; no refusal
  raised; a swallowed next-year 429; the alert sent inside the lock; an alert on every failure (second form); the
  recorder not sharing its pace; the source
  not halving it.
- Real output sample (the committed code, a stand-in SDK; no value, no secret):

```
Groww sign-in failed (ConnectionError); this process tries again after 5 minutes, at most 3 tries a day
08:22:00 ConnectionError: (sign-in tried)
08:23:00 GrowwSignInPaused: Groww sign-in paused after 1 failed try this token day; next try at 08:27:00 IST
08:27:00 ConnectionError: (sign-in tried)
08:28:40 GrowwSignInPaused: Groww sign-in paused after 2 failed tries this token day; next try at 08:37:00 IST
2026-10-27 25000 CE #3: GrowwRateLimited (provider message withheld) | GrowwRateLimited:429
2026-10-27 25000 CE #4: GrowwRateLimitPaused (provider message withheld) | GrowwRateLimitPaused
attempt at 15:00:20 waits [100.0] s; another call then: Groww call refused unsent: inside A16's 15:00 mark until 15:02:00 IST
```
