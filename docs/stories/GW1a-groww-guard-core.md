# Story GW1a: Groww's sign-in, read-only client, 429 name and 429 stop (GW1 parts 1-4, merged alone)

Owner: builder session_01GsPm29fZzfH3DiErKAdBVk, from orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH (25 Oct 2026).
Lane 1 (an outside service). GW1's parts 1-4, split out so the sign-in guard is on `main` before Mon 26 Oct 08:22 IST
(A16's first fire). Judges 637 (K) and 638 (I) found nothing in these parts at 01477b7cf. GW1's parts 5-6 (A16's
quiet windows and pace) stay on `story/gw1-groww-rate-guard`; the full design and its evidence are there
(`docs/stories/GW1-groww-rate-guard.md`). Owner, 25 Oct: "make sure it does not make Groww API go over rate limit in
any reason or in any situation".

## What is wrong today (strong evidence: the code on main)

- **Sign-in storm.** `GrowwProvider.api` set its client only after a successful sign-in, so after a failed one every
  later call signed in again. A16 makes 3-6 calls a mark, so 26-30 marks make about 160-210 sign-ins a day, over
  Groww's 150 per 24 hours (research/school/probes/2026-10-22-p0-1-groww-chain.md:100-112). The next morning can then
  be locked out.
- **A 429 is invisible in A4's sidecars.** SDK 1.5 raises Groww's `status: FAILURE` 429 as a plain
  `GrowwAPIException`, and A4's `withheld()` keeps the class name only.
- **Raw SDK client.** The 3 pm, `v4` and execution captures and `GrowwFutureQuotes` held the raw `GrowwAPI`, which
  can place orders.
- **A 429 does not stop an A4 attempt.** It asks for every remaining contract and spends the budget the other taker
  needs.

No v4-frozen file is changed. Frozen callers change only in sign-in back-off, read-only wrapping and error class
names, never in a recorded value or a call's timing (orchestrator, 25 Oct, Q1).

## The rule

1. **Sign-in guard** (`fno/providers/groww_sign_in.py`).
   - A success is kept until 06:00 IST.
   - A failure is remembered: the next try waits 5 minutes, then 10 (tries at +0, +5 and +15 min).
   - At most 3 tries are made per process and token day. Calls in between raise `GrowwSignInPaused` and reach no
     network.
   - The day's first failure calls `on_sign_in_failure` once, after the lock is released, with the class name only.
     `get_provider` wires it to #fno-desk and prints the outcome.
   - Worst case (judge 637 m1): about 38 processes sign in on a session day (A16's 7 fires and their reruns up to 21;
     the daily run's Groww children 5, 10 with a rerun; pre-open 1; the school 4; by hand 2). With every sign-in
     failing: 38 x 3 = 114 tries, under 150.
2. **Read-only for every caller.** `GrowwProvider.api` is the `ReadOnlyGroww` allow-list over the guarded client. The
   feed probe alone gets the raw SDK object, through `feed_client()`, because `GrowwFeed` reads its internals.
3. **A 429 is named** (`fno/providers/groww_rate_guard.py`). Both forms (`GrowwAPIRateLimitException`, and
   `GrowwAPIException` with code `429`; both carry `.code == "429"` in SDK 1.5) are raised as `GrowwRateLimited`,
   code kept, Groww's text dropped. `is_rate_limit()` is public; MS-P0b uses it and keeps no copy. A 429 on next
   year's expiry list is raised, never swallowed.
4. **Stop after a 429.** For 60 s after one, the process's Groww calls raise `GrowwRateLimitPaused` unsent. A4's
   attempt then ends at its first 429, and its own 60 s retry gap follows.

## Known limits

- The sign-in cap is per process; the day's total is bounded by the process count, not counted across processes.
- These parts alone do not keep readers apart in time, so two processes can still meet in one minute until the
  first 429 stops one of them. That is GW1's parts 5-6.
- Whether Groww's limits are per key or per account, and how it counts a minute, are unknown.

## Acceptance

1. A failed sign-in is not retried within its back-off; the paused calls do not call the sign-in. The back-off is 5
   then 10 minutes, and the 4th try in a token day is never made. A new token day resets the count, and a success is
   reused until 06:00 IST. Cases: good, bad, boundary (exactly at the back-off's end) and empty credentials.
2. The failure callback fires once per token day, outside the lock, with the class name only.
3. `api` refuses order, modify, cancel and position names before any sign-in. `chain`, `quote_book`, `expiries` and
   `GrowwFutureQuotes.quote` work through it. The feed probe gets the signed-in client from `feed_client()`.
4. Both 429 forms arrive as `GrowwRateLimited` with no Groww text. Other errors pass unchanged. A4's `withheld()` and
   A16's `failure_name` show the name.
5. After a 429, calls within 60 s raise `GrowwRateLimitPaused` and reach no SDK. A 20-contract attempt with a 429 at
   contract 3 asks Groww 3 times.
6. Each criterion fails when its code is broken on purpose. The full suite passes.

## Claims

- Code is identical to GW1 at 33f34e571 for these parts, minus the quiet-window hooks:
  - `fno/providers/groww_sign_in.py`;
  - `groww_rate_guard.py`, without the quiet check;
  - `groww.py`, without `quiet` or the `expiries` wait;
  - `__init__.py`, the alert only;
  - `fno/intraday/feed_wiring.py`: `GrowwFeed(provider.feed_client())`, the REST client `provider.api`.
- Tests: `tests/test_groww_guard.py`, `tests/test_groww_provider.py`, `tests/groww_sdk_fake.py`;
  `tests/test_composition.py` and `tests/intraday/test_feed_tls.py` were adapted.
- Mutations, 10, each caught (run with PYTHONDONTWRITEBYTECODE=1):
  - Sign-in: no back-off check; an alert on every failure; the 4th try; no doubling.
  - Read-only: `api` without the allow-list.
  - 429: the next-year 429 swallowed; no 429 translation; no pause check; Groww's text carried on.
  - Wiring: `get_provider` without the alert.
- Gates on origin/main d6438bafa plus this change: pytest -n auto 16756 passed, 1 skipped, 13 xfailed; ruff check and
  format, check_imports, check_records and check_numbers clean.
