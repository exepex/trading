# Judge 357: O10 part 2, O8's freshness rows, the error line and the go-live trial (story/o10-part2-freshness-trial @ 7966c4f0)

Judge F (independent). Story `docs/stories/O10-capture-health.md` scope 2 and criterion 5 (amended on this branch,
agreed with O8's owner, session_012eM7Ti). Claims `response_254` addendum 3. Part 2's own diff is `0db3f682..7966c4f0`.
Lane 1 (health checks, a new committed ops record, the owner's go-live gate). Labels: **strong**, **some**,
**reasoning only**.

## Verdict: FAIL (1 should fix, 2 minor)

Gates on 7966c4f0: **7421 passed**; ruff, ruff format (1323), `check_imports.py` and the record scan (6617) are
clean; the suite leaves `research/ops/` unchanged.

My planted mutations, all caught (`tests/health`, 150 tests):
- the match window widened to 30 days;
- `_recovered` rows counted as records;
- an `unknown` no longer waiting for the session's last run;
- a session with no row not breaking the streak;
- a dry run appending to the ledger (3 failed);
- the date key fixed to the first column (2 failed).

What is right:
- margins are checked by the `as_of` column, by name;
- the market-archive deadline is moved to 15:00 from two measured pushes, with no deadline typed unmeasured;
- the trial is append-only, never written by a dry run, and judges each session once when final;
- a session no check covers is never judged;
- the O8 owner's `unknown` fix is in;
- the test isolation fix stops three old CLI tests writing the real `trial_days.csv`.

## Should fix

**SF1. One capture-error row excuses up to three sessions' problems, so a silent miss can pass the go-live trial
[strong: reproduced].** `_recorded` accepts any row of the check's jobs dated from the session to `MATCH_DAYS` (2)
days later. A single `index-closes` row dated 21 Oct makes `_recorded` true for the sessions of 19, 20 and 21 Oct (I
called it directly: True, True, True).

So if index-closes never starts on 19 and 20 Oct (silent, which GitHub's scheduler does here) and fails loudly on
21 Oct, all three sessions count as recorded and the trial stays clean. The trial is the owner's gate (10 sessions,
zero silent failures), so a false clean decides go-live.

Fix expected: one row can excuse one session's problem. Either consume each row once (nearest session first), or
excuse only a session for which no earlier session in the same span also needs that row. Add a test with that
three-session case, where 19 and 20 Oct must stay silent.

## Minor

1. Scope 2 changed from "each new `missed` or `unknown` result is appended to `capture_errors.csv` once" to "O8
   writes no error row of its own". A job GitHub never starts now leaves only `trial_days.csv`
   (`session, silent_count, silent_checks`) plus the evening Slack summary. That is a record, but it has no status.
   Add the status to each silent check, for example `NSE margins:missed`, so the committed record says what failed,
   as the owner's "error case captured properly" asks.
2. The trial's own clock is `health-check.yml`, a GitHub cron. Its first slot is today, 12:21 UTC. If GitHub drops
   it, sessions go "not proven". That is the right outcome, but say in the known limits that the trial depends on that
   one cron running.

Criterion 7 (live run logs) is still pending, as the claims say.
