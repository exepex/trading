# Judge 525: MS-INS part e follow-up, a stopped run's stored file is recovered

**Scope:** story/ms-ins-adopt at 1ef37ba6 (builder session_01LH7m9r5TCAKgZbeHVYkiTD), one commit on `main`. Story
"INS-e follow-up: a stopped run's stored file is recovered". The orchestrator's conditions: verify before adopting,
alert instead of adopting a bad file, record the adoption, and weigh a fixed input cut-off. Lane 1, one judge. Round 1
of 2. Judge K (session_019ZApRwkUiNMKDsf1k4W44z).

**Verdict: FAIL.** 2 should-fix. The defect is real and the tests reproduce it. None of the orchestrator's three
adoption conditions is met, and the cleaner design is not discussed.

## Orchestrator's conditions
| Condition | Result | Evidence |
|---|---|---|
| Before receipting, verify a well-formed instructor record for that exact key, read back with a matching hash | NOT MET | `store.py` `recover` publishes the receipt for `data.drive.get(...)`'s bytes, then calls `read`. The decode and the hash check run only after the receipt is published, and nothing checks that the records belong to that session and kind |
| A file failing that check is an alert, never adopted | NOT MET | My probe (the branch's `FakeData`/`FakePublisher`): gzip bytes holding `{"not":"an instructor record"}` stored at the causes path with no receipt. `recover` published 1 receipt, then raised `KeyError`. On the real store that receipt is committed and pushed to `main`, and every rerun crashes |
| The adoption is recorded | NOT MET | it uses the normal `RECEIPT_MESSAGE`; no line or record says a stored file was adopted |
| The fixed per-day input cut-off was considered | NOT MET | the Claims do not mention it |

## Findings
1. **Should-fix: adoption receipts unverified bytes.**
   - Expected, before any receipt:
     - read the stored bytes;
     - decode them as instructor records of that kind;
     - check each record's `closed_on` or session matches the key, and its `rules_sha256` is this card's.
   - Only then put, publish, and read back with the hash check.
   - On any failure, send one alert naming the path and the class, and do not adopt.
   - Record the adoption: a distinct receipt message ("adopted") or a line in the run's output.
   - Test it with a malformed file, a file of another session, and a file of another kind.
2. **Should-fix: the root cause is non-determinism, and the design choice is not argued.**
   - A rerun computes other records because the session run reads "today": the correction scan up to the clock,
     settlements and control closings known later.
   - A run cut at a fixed point for the session would make the file a pure function of its inputs:
     - corrections sealed up to that session's slot;
     - settlements and control results known by then;
     - re-checks stay on later sessions, as now.
   - A rerun then writes the same bytes (a no-op), and no unreceipted file ever needs to be trusted. That is the
     "no patches, root cause" rule. [reasoning only]
   - Adoption is defensible if the cut-off is too intrusive for v1. But the story must say why, and finding 1 must
     hold.
   - Expected: either the cut-off (with a test that a rerun after a later settlement gives byte-identical files), or
     the Claims argue for adoption against it and finding 1 is met.

## Checked
- `read` never publishes, so the readers (review, why line) are unchanged.
- `instructor` tests: 268 passed (my run). ruff and check_imports are clean. No plants run: findings 1 and 2 change
  the code.

## Note for MS-P1j
The deferred store (story/ms-p1j-ins-wiring, judge 523.1) will need whatever `recover` becomes. Its `prepare` and
`flush` must not adopt on the step's thread: adoption writes (a put and a publish), so it belongs in the run's
thread like every other write.
