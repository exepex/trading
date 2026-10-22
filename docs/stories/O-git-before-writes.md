# Story: git before writes

Owner session 013xqaNTCbSBytKgqpfaYFqZ, assigned by the orchestrator on 22 Oct 2026. Lane 1, judged by Judge J.
Branch `story/git-before-writes`. It follows git-fails-loud (judge 505), whose caller audit found this.

## The problem

Since git-fails-loud, a failed git command raises `GitFailed` instead of reading as "nothing found". Four commands
wrote a record and only then asked git. A git failure there now stops them half done:

| Command | Write first | Git read after it | What a rerun then did |
|---|---|---|---|
| (a) `factory register` | ledger row (registration.py) | `head`, and the gate log's append-only check | refused: "already in ledger" |
| (b) `factory freeze` | ledger `protocol_commit` | `head`, and the gate log's check (gate_order.py) | refused: "already frozen" |
| (c) `research run` | the results files | `head`, inside `Ledger.mark_run` | wrote both again (no harm) |
| (d) playbook status change | registry row and status line | the whole loader's re-check (`load()`) | refused: the transition was already done; `AutoPauser`'s pause alert was not sent |

Row (e), the desk's `write_no_decision`, is left alone. The desk freeze (story/o1-desk-freeze) changes that path
(orchestrator, 22 Oct).

## The design

- **Every git read happens before the first write.** `AppendOnlyCsv.prepare` and `GateLog.prepare` run the
  append-only check and the row check now. They return the write, which reads nothing. `GateOrder.prepare` does the
  same for a gate row at a given commit, and `log` is now prepare followed by write.
- **(a) and (b)** read HEAD once, before anything is written. They prepare the gate row, then write the ledger, then
  the gate row. The commit they record is unchanged: the HEAD the gate ran at. For a freeze, `protocol_commit` and the
  G4 row are the same commit.
- **(c)** `record_run` in research_cli reads the run's commit before it writes the results. `Ledger.mark_run` now takes
  the commit (the D4/D5 builder agreed).
- **(d)** The status change drops its `load()` after the writes. Before writing, it already loads the whole playbook,
  and it checks this version with its new row through the loader's own `check_against_history`. `Registry.append`
  checks the whole registry with the row. So the dropped re-check repeated checks already made.

Recovery from a half-done state: a rerun completes it rather than refusing it. R1's owner set both conditions:
- **Register.** The trial's ledger row exists with this card's `protocol_path`, experiment, description and
  hypothesis, and kind `prospective`. The row is not committed, and the trial has no gate row. The rerun appends the
  `idea` row, dated by the ledger row. A committed half row is refused and sent to `factory backfill`; a row of another
  kind is refused.
- **Freeze.** The row's `protocol_commit` is in HEAD's history, and the card is unchanged since that commit. The rerun
  appends G4 at that commit and never freezes again. Anything else is refused. One behaviour change: a
  `protocol_commit` set by hand used to be refused outright. It now completes, but only under these same conditions.

## Claims

1. **Any failed git call leaves nothing written.** Strong evidence: tested.
   `tests/research_engine/git_failures.py` runs each action once to count its git calls. It then reruns the action on
   a fresh repository once per call, with that one call failing (exit 128), and requires `GitFailed` and every
   working-tree file unchanged. The counts are 4 calls for register, 18 for freeze, 1 for `research run` and 8 for the
   status change. Each action also writes when nothing fails.
2. **Reruns complete a half state; anything else is refused.** Strong evidence: tested in
   `tests/research_engine/test_git_before_writes.py`:
   - a half register is completed, and the trial is never registered twice;
   - a committed half register is sent to backfill;
   - a half register of another kind is refused;
   - a half freeze is completed at its frozen commit;
   - a half freeze whose card changed is refused;
   - a half freeze at a commit outside the history is refused.
3. **Every fix is pinned by a test.** Strong evidence: revert plants, each run alone. Each of these plants fails its
   test:
   - register writing the ledger before its gate check;
   - freeze writing the ledger before its gate check;
   - `research run` reading head after the results;
   - the status change's `load()` restored after the writes;
   - register's completion removed;
   - freeze's completion replaced by the old refusal.
4. **Owners.** R1's owner (01XFXpbkyixX7SuXeQCp5EnX) agreed, and their two conditions are built. Their parked
   story/r1-book3-trial-ids changes the next-trial line, which is now in `_require_next`; whoever merges second
   resolves it, and the `isdigit` filter stays. The D4/D5 builder (01SFDjjZx7JYziM3jqJytG2z) agreed to the
   `mark_run` change. B4 and D1 have no live owner.
5. **What is not covered.**
   - A write that fails for a reason other than git, such as a full disk between the two writes, can still leave a
     half state. That state is the same one the reruns above complete, for (a) and (b).
   - (e) is out of scope, as said above.
6. **Gates:** in the message to the judge.

## Round 2 (judge 513)

- **Should-fix: R1's field condition is now pinned.**
  - The new test, `test_a_half_registration_that_no_longer_matches_its_card_is_refused_naming_the_field`, runs once
    with the description and once with the hypothesis. In each case it changes the card after a half register.
  - It checks that the rerun is refused, naming the field, and that no gate row is written.
  - Plant: removing `_require_same` from `_stopped_half_done` now fails both cases.
- **Minor: the gate log's whole-log check is now pinned.**
  - `test_a_malformed_earlier_row_refuses_a_new_append` (tests/factory/test_gate_log.py) commits a malformed row (gate
    G9). The history stays append-only, and the next append is refused with the file unchanged.
  - Plant: dropping `self.rows()` from `GateLog.prepare` now fails it.
