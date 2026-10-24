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
bytes. The orchestrator and G10's owner decide whether that is allowed (question Q1 to the orchestrator, 25 Oct).

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
   `GrowwAPIException` with code `429`, is raised as `GrowwRateLimited`, a subclass that keeps `.code`. A4's sidecar
   then reads "GrowwRateLimited (provider message withheld)", and A16's `failure_name` reads "GrowwRateLimited:429".
   No message, URL or value is ever kept.
4. **Stop at the first 429 (part 4).** After a 429, the process's Groww read calls raise `GrowwRateLimitPause` without
   reaching the network for 60 s, Groww's per-minute window. A4's attempt then ends incomplete at once, and its own
   60 s retry gap follows. (Pending Q3: A16 gets the same pause; on a clash it loses the rest of that mark.)
5. **Quiet windows for A16's marks (part 5, pending Q4 and Q5).** Providers built through `get_provider` (the 3 pm
   NIFTY, `v4`, A4c and E3) wait before any Groww call that would start in an A16 mark window, from the mark to 90 s
   after it. A16, the pre-open capture and A16b build `GrowwProvider` directly and do not wait. Effects: the `v4`
   capture's first call moves to 14:31:30 (G10's named fallback), A4c to 15:01:30 and E3's to 15:16:30. A NIFTY
   attempt running at 15:00 pauses up to 90 s. Every request keeps its real send time.
6. **Claim failure (part 6): report only.** A safe fix exists: a run whose claim is `unclaimed` takes the mark at
   half pace (2.5 a second), so two blind takers stay at 5 a second. It needs A16's owner; it is not built here
   unless the orchestrator says so.

## Known limits (said plainly)

- There is still no cross-process limiter. Separation is by the clock (rule 5) plus the fast stop (rule 4). Two
  processes started by hand at the same time can still exceed the cap until the first 429 stops them.
- The sign-in cap is per process. The day's total is bounded by the number of processes, not counted across them.
- Whether Groww's limits are per key or per account is unknown (the probe found no statement).

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
6. (If Q4 and Q5 say yes.) A call through `get_provider` at 14:30:10 starts at 14:31:30, and one at 14:32:00 does not
   wait. A16's directly built provider never waits.
7. Each criterion fails when its code is broken on purpose (mutation per criterion). The full suite passes.

## Claims

(Builder fills this in with each round.)
