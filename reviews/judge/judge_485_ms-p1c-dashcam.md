# Judge 485: MS-P1c, the dashcam

**Scope:** story/ms-p1-dashcam at eddd7d3a (builder session_01WeFYCqffRe7et1nfSJyuv5). The diff is 756e6545..eddd7d3a,
`fno/school/dashcam/` and `tests/school/dashcam/` only (a's code is judge 479's). It carries a's PASSed round-2 code
(35458460); a's later commits change story text only. Lane 1 (records). Round 1 of 2, after early findings that I sent
on 4bfbba77. Judge J (session_01Qg4Gxun1NvGRrtS9C68Dc1).

**Verdict: PASS.** No blocking and no should-fix findings; 2 minor.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Write-once; other bytes are `ReplayConflict`, "rule broken" | MET | `store.seal` judges the remote receipt before Drive is touched; a Drive conflict after a failed push is also caught (`test_a_rerun_with_other_records_after_a_failed_push_...`); plants 1, 2, 4 caught |
| 2 | The receipt is pushed before `seal()` returns | MET | `publish` returns only what `published()` finds on the fetched `origin/main`, else `SealNotPushed`; plant "seal without push" caught |
| 3 | Forged or stale seals refused against the remote receipt | MET | `SealChecker` compares commit, SHA-256 and time with the receipt's add commit on the remote; 5 plants (each field, the time, the SHA) caught |
| 4 | Rerun safety | MET | same records: same seal; a fresh checkout makes no second receipt; a failed push is pushed by the rerun; a shallow clone is deepened or refused by name. My own depth-1 probe now names the real add commit, and the original seal checks valid (it was refused on 4bfbba77) |
| 5 | `pushed_at` labelled commit time | MET in c | `PushedReceipt.pushed_at`: "commit time, not push time; the proof is the remote receipt". See minor 2 for a's contract |
| 6 | Single-process counts file | MET as an assumption | stated in Claims and accepted by the orchestrator; j tests it. See minor 1 |
| 7 | Counts file: record scan clean, codes and whole numbers only | MET | the test runs the scan; session and slot filter, slot check and rewrite guard plants caught |
| 8 | Replay reads exactly what was sealed; conformance | MET | `find` per a's contract; tamper and stale-cache tests; read SHA plant caught |
| - | Gates (my clean run) | MET | pytest -n auto: 10,347 passed, 16 xfailed. ruff check and format, `check_imports` and `check_records` are clean. Largest file 87 lines |

## Minor (no round needed)
1. `counts.py` does not say in its docstring that it assumes one writer. The assumption lives only in the story.
   A one-line "why" comment would keep j from relying on an atomicity it does not have.
2. For a's builder, not c's: `fno/school/contracts/seal.py` labels `Seal.pushed_at` "when its receipt reached the
   remote". c fills it with the commit time, as the orchestrator accepted. d's fill port reads `Seal`, so the
   contract's comment should say "commit time; the remote receipt is the proof".

## Plants
22 planted on eddd7d3a, 22 caught:
- 18 from round 1, re-planted on the new code (one of them, "no fetch", rewritten to fit it);
- 4 on the shallow fix (no deepen, not refused, deepen skipped, the checker letting a shallow refusal through).

One malformed plant of mine was redone.

On 4bfbba77, 5 of 18 had survived; all 5 are now caught.

## Notes
- My first full suite on this tip showed 22 failures. That run overlapped my plant run in the same worktree, which
  edits files mid-run. The clean re-run above is the result.
- `_push_unpushed` pulls and pushes once beside A16f's own retrying `_publish`. It is small, and the remote check
  decides the result, so this is not a finding.
