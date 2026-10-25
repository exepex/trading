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
   - A failed sign-in is remembered. No new try is made for 5 minutes, then 10, 20, and at most 30 minutes apart.
   - At most 6 tries are made per process per token day.
   - Between tries, every call raises `GrowwSignInPaused` at once and reaches no network.
   - The first failure of a token day calls the injected `on_sign_in_failure` once, with the exception's class name
     only. `get_provider` wires it to a #fno-desk line. A caller that builds `GrowwProvider` directly gets no alert,
     but its own failure records name `GrowwSignInPaused`.
   - Worst case: about 10 processes sign in each day (A16, pre-open, the 3 pm NIFTY, v4, A4c, E3, A14c, A16b and the
     school probes), each at most 6 times, so at most about 60 against the cap of 150.
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
   never held. Effects: A4c's first call moves from 15:01 to 15:02:00, and E3's capture (config
   `desk.execution_snapshot` 15:15, unchanged) asks from 15:17:00. Its record's `started_at` stays 15:15, when the
   attempt began waiting. The `v4` capture at 14:32 is never held; the rule stays on it as a belt. A NIFTY retry
   still running at 15:00 ends incomplete there, and the next one starts at 15:02:00. Why 120 s: A16's marks took
   48-58 s to record on 20-23 Oct, and 83 s at most (78 committed slot rows, `first_seen_at` minus the mark; strong
   evidence).
6. **A run that could not claim its mark asks slowly (part 6; orchestrator agreed for A16's and A4's absent
   owners).** `IntradayQuoteSource.share_pace(shared)` (no-op by default): the recorder passes `shared` when the claim
   is `unclaimed`, and Groww's source then paces at 1 a second for that mark, its own 4 a second otherwise. Any two
   takers then ask at 5 a second or less together (4 + 1, 1 + 1), seen or unseen. See the section on round 1's head.

## Known limits (said plainly)

- E3's execution capture took 2 min 34 s on 23 Oct (15:15:00 to 15:17:34, its committed record). Starting at
  15:17:00 it ends near 15:19:34. `desk.fills_by` (15:20) limits only a rerun that did not take the snapshot itself.
- No Groww reader outside `get_provider` gets the quiet windows. A new reader (for example the school's capture
  probes, MS-P0b) must be built through `get_provider` or keep out of A16's marks by its own schedule.
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
   function is not called. The back-off doubles to 30 minutes. The 7th try in a token day is never made. A new token
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
7. A16's recorder asks its source for half pace on an `unclaimed` mark and for its own pace on the next one; Groww's
   source then paces at 1 a second, and at its own pacer again after. The two paces sum to at most 5 a second.
8. Each criterion fails when its code is broken on purpose (mutation per criterion). The full suite passes.

## Round 1's head: every taker paces for the worst pair (orchestrator, 25 Oct: a must-fix under the owner's rule)

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
- Gates at this commit (merged with main f1a94bbeb): pytest -n auto 16617 passed, 1 skipped, 13 xfailed; ruff check and format, check_imports and
  check_records clean.
- Mutations, each caught: no back-off check; an alert on every failure; no doubling; no day cap; `api` without the
  allow-list; no 429 translation; no pause check; Groww's text carried on; `get_provider` without the alert; without
  the quiet windows; the mark itself outside its window; no refusal check; no wait before an attempt; no refusal
  raised; a swallowed next-year 429; the alert sent inside the lock; an alert on every failure (second form); the
  recorder not sharing its pace; the source
  not halving it.
- Real output sample (the committed code, a stand-in SDK; no value, no secret):

```
Groww sign-in failed (ConnectionError); this process tries again after 5 minutes, at most 6 tries a day
08:22:00 ConnectionError: (sign-in tried)
08:23:00 GrowwSignInPaused: Groww sign-in paused after 1 failed try this token day; next try at 08:27:00 IST
08:27:00 ConnectionError: (sign-in tried)
08:28:40 GrowwSignInPaused: Groww sign-in paused after 2 failed tries this token day; next try at 08:37:00 IST
2026-10-27 25000 CE #3: GrowwRateLimited (provider message withheld) | GrowwRateLimited:429
2026-10-27 25000 CE #4: GrowwRateLimitPaused (provider message withheld) | GrowwRateLimitPaused
attempt at 15:00:20 waits [100.0] s; another call then: Groww call refused unsent: inside A16's 15:00 mark until 15:02:00 IST
```
