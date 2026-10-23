# Judge 543: DR1-1 staging, certification and the as-seen record (A4h closes, shadow)

Judge B, 23 Oct 2026. Story/dr1-1-closes-records at c7ba8850a; lane 1 (evaluation records, Drive). Story:
`docs/stories/DR1-design-staging.md` section 7, Claims 1-6.

**Verdict: FAIL, round 1 of 2: two should-fixes.** The package is small and well cut: the version source, rules,
certifier and record folder each sit behind their own interface, and the composition root is `wiring.py`. No writer or
reader outside the new package changes, and the reason text follows A4h's judged "differs by X" rule.

## Claims vs reality

| Claim | Reality |
|---|---|
| 1. A record is a pointer plus check results, never a level; same choice, same bytes; rerun a no-op | True (`Record.to_document` has no clock; the test checks no level appears). But see SF1: a rerun is "already recorded" even when the record never reached main |
| 2. Quality-only choice; a later differing read supersedes; certified = the read closest to the official file, whichever read it is; VIX positive, not banded | Mostly true. **The certified half is untested** (SF2) |
| 3. A record already published by another certifier is never overwritten; a different choice prints a conflict | True only for a record already in the local checkout. A record published by another certifier while this one runs reaches it only through the push, and the push outcome is ignored (SF1). The `CONFLICT` line has no test: my plant making `write` always overwrite survives |
| 4. `RecordReader`: exact bytes or a named refusal; certified serves provisional, never the reverse; the as-seen pointer | True. Plants caught: provisional serving a certified need; no SHA check |
| 5. Two writers in the same second get two names | True by construction (`<fetched_at>_<run_id>`) |
| 6. Gates | Reproduced on c7ba8850a: 14,638 passed, 1 skipped, 16 xfailed; ruff, format and check_imports clean. It merges cleanly with current main |

**Plants on `tests/record_store`:**

| Plant | Result |
|---|---|
| provisional keeps the first read | caught |
| VIX banded | caught |
| no band at all | caught |
| integrity skipped | caught |
| tolerance check skipped | caught |
| zero allowed | caught |
| provisional serving a certified need | caught |
| reader without SHA check | caught |
| **certified always the first read** | **survives (22 passed)** |
| **`write` always overwrites** | **survives (22 passed)** |

## SF1 (should-fix): a refused push of the record is reported as recorded, and a rerun never pushes it

- **Path:** `RecordFolder.write` calls `committer.commit(...)` and drops the outcome line.
  - `Certifier._written` then prints `recorded ...`, and `cmd_certify` exits 0.
  - On a rerun, `certify` returns `already recorded` from the local file before reaching the committer, so the
    record is never pushed from that checkout.
  - The same drop hides Claim 3's race: another certifier's record arriving through `pull` makes the pull or push fail,
    and this run still prints "recorded".
  - `--commit` is the shadow routine's command (the routine lines are proposed next), so this is the normal running
    path. It is the same class of defect as judge 507.13's SF1.
- **Reproduced** (scratch test on c7ba8850a, committer returning "records NOT committed: push failed"): the first run
  printed `recorded 172665b4852e ...` with `recorded=True`; the rerun printed `already recorded`; the committer was
  called once.
- **Test it must pass:** with a committer whose outcome is not committed, `certify --commit` prints that line and exits
  1, with no "recorded" line; a rerun still tries to push the unpushed record (it is not "already recorded" until it is
  on main). A record that main already holds with another version prints the conflict and exits 1.
- **Fix (reasoning only):** carry the committer's outcome into `Outcome`, and treat "already" as true only when the
  record file is on main.

## SF2 (should-fix, test only): the certified choice "closest to the official file" is untested

- **The gap:** `test_when_both_reads_agree_with_the_official_file_the_closest_is_certified` has the first read exact
  and the recheck 0.01 off, so a rule that always takes the first read passes it. My plant `best = 0` survives.
- **Why it matters:** the certified record decides which close every score and back-test reads, so under the standing
  rule an uncaught plant there is a should-fix.
- **Test it must pass:** with the recheck closer to the official file than the first read (both within 0.01), the
  certified record names the recheck. The plant must fail it.

## Notes (not findings)

- A provisional run before A4h's 16:00 recheck would record the 15:40 read write-once, and a differing recheck could
  then never supersede it. The proposed evening routine runs at 19:53, so this does not happen; keep it so in the
  routine branch.
- `choose` compares each index's whole entry but names the change by `last` only: a change in `open` alone would read
  "NIFTY 50 same". This is cosmetic.
- A certified run before the official file exists exits 1 ("no official index-close file in Drive yet"). The routine
  branch must decide whether that exit alerts, because the story says this gap is not alerted.
