# Judge 471: A9c, a second NSE archive host, story text (story/oss1-second-host @ 5d6d852e)

Judge F. Round 1 of 2 (owner, row 294). Lane 1 (NSE downloads). Labels: **strong**, **some**, **reasoning only**.

## Verdict: FAIL (1 blocking, 2 minor). A small text fix.

The design is right where it matters:
- the fallback happens only on `RawSourceUnavailable`;
- a refusal or a cooling-off never reaches the second host, which keeps rule 281 item 2 (no getting around a block);
- a 404 stays "not published" and never becomes the second host's answer;
- write times, A11's revision sweep and the in-place snapshot files stay primary-only, each with its reason;
- the evidence is labelled honestly: 8 of 8 datasets byte-identical on one day, and different Akamai edges.

## Blocking

**B1. No gap list (quality rule 2, `docs/JUDGE.md` line 110; still required after row 294).** Map each rule to a
criterion or to Out:
- the owner's rule 281 items 2 and 3 (no getting around a block; paced downloads: the second host gets its own pacer);
- O9 and A10's write-once store with its receipt;
- A8's and A11's point-in-time evidence (Out, with the reason);
- A9b's retry policy (the doubled worst case);
- the morning librarian's 08:50 deadline (FL1-1d step 1b);
- O10's failure row and alert when both hosts fail;
- quality rules 5, 6 and 8.

## Minor

1. **Different bytes from the second host [reasoning only].**
   - Criterion 5 covers "a later primary fetch of the same bytes". It should also say what happens when the bytes
     differ: a stale or newer edge copy kept write-once, then a different primary copy.
   - Name the path: the store's conflict, or A11's revision record, and whether it alerts. Test it.
   - One identical day is some evidence. NSE's 23:20 rewrites (A11) show that the bytes can change.
2. **The morning deadline in numbers.** "The worst case to be stated with the measured number in the claims": put the
   computed worst case in the text now (primary plus secondary retries, from `RETRY_WAITS`, against FL1-1d's 08:50).
   If it can pass 08:50, say what the morning edition does.

Plants: none (text round).
