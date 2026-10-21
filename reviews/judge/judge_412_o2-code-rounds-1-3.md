# Judge 412: O2 code, rounds 1-3 (story/o2-failure-handling at e6483952)

**Verdict: PASS for rounds 1-3. Lane 1. They may merge on their own,** so the git limit and the silent-part alert reach
production now. O2 as a story is not done: round 4 (kill-and-rerun, hung git and hung command end to end, the trade
fixture rows, the shadow cases with (c) as a strict xfail, the source-tree-unchanged test) comes later, with its own
verdict. The text is judge 204 addenda 3 and 5.

## Round 1: one hard limit on every git call (`fno/desk/git_limit.py`, `git_sync.py`, `steps.py`)
| Check | Result | Evidence |
|---|---|---|
| Each call in its own process group; at the limit the group is killed and reaped | MET | `LimitedRun`: `start_new_session=True`, `os.killpg(SIGKILL)`, then `communicate()` |
| Only the call's own new locks are removed, never while a git process lives | MET | `GitLocks.remove_new(before)`: the new set only; `_git_alive` scans `/proc`, and with no `/proc` nothing is removed |
| A lock already there fails the call with the hand fix | MET | `HELD_LOCK` and `HAND_FIX` in `Git.__call__` |
| A stopped push is "push not confirmed", unpushed | MET | `PushNotConfirmed(PushRejected)` |
| No path bypasses the limit | MET | `unshallow`, `content_sha256` and D3's `decided_runs` now go through `Git._run` or `Git.show` (the builder's test found the last bypass) |
| `CommandStep`'s 600 s stop removes its own new locks | MET | `steps.py`; `GitLocks(root)` wired in `fno/daily/wiring.py` |

Planted mutations (real git, hanging hooks):
- old locks removed too: caught (1 failed);
- the live-git guard off: caught (1 failed);
- no lock removal: caught (1 failed);
- **`popen.kill()` instead of `killpg`:** the test run **hung** rather than failing, because the hook kept the pipe
  open. A regression would still show in CI as a timeout, but put a per-test time limit on `tests/daily/test_git_limit.py`
  (for example `pytest-timeout`, or a `signal.alarm` guard) so it fails, not hangs. This is a note, not a should-fix.

## Round 2: the end-to-end harness (`tests/e2e/`) and two root fixes
- `OUTSIDE_SEAMS` lists:
  - the clock;
  - Slack;
  - the owner's Drive (both builders);
  - the raw NSE stores and NSE's archive;
  - Groww's 15:15 capture;
  - the child-process runner;
  - the quote store's default folder.

  A test keeps the list. The child commands are scripted, and the story text names them as a seam (line 48), with NIFTY's
  part running A4's real `record_today` over a fake Groww. So the weather, v4 and card children are not run end to end.
  They are `not_live` in production anyway; say so when they go live.
- **Root fixes, each tested:**
  - `build_book1_orders(cfg, root)`;
  - the capture's quote folder is root-relative (`fno/desk/daily_wiring.py`).

  Both are harmless in production, where root == ROOT.

## Round 3: outage families and G1
- Slack up and down, the twin multiset, NSE failing, Drive at the download, Drive for the raw files, and never-starts:
  each family has its test.
- **G1:** a 3 pm part that failed without its own alert now gets one O1 alert (`PART_NOT_OK`).
  - Planted mutation: that alert removed fails 5 tests.
  - A part that alerted itself (its lines hold "alert sent" or "alert NOT sent") gets no second alert.
- **G2:** "A4's child prints the unsent outcome without the text" is a **strict** xfail
  (`tests/e2e/test_outages.py` 115).

## Gates
On a trial merge with main plus main-green (76f5d1f7): **8130 passed, 19 xfailed, 0 failed**; ruff and check_imports
clean. tests/e2e: 9 passed and 1 xfailed in 117 s on 4 workers.

## Merge order (must read)
G2's strict xfail XPASSes, and so fails, as soon as the A4 unsent-alert fix (story/a4-unsent-alert-text) lands.
Whichever of the two merges second must turn the xfail into the real assertion in the same push, or main goes red.

## Addendum 1: merge-order correction
My merge-order caveat above was wrong. I merged O2 (e6483952) with the A4 fix (cac35232) and main-green: tests/e2e plus
tests/daily give 87 passed and 1 xfailed. G2's strict xfail does **not** flip, because the e2e children are scripted and
never go through `cmd_quotes`. Either branch can merge first.

Two things remain for round 4:
1. G2 stays xfail until the harness runs the real `cmd_quotes` path.
2. O2's own-alert detection reads `lines()`, which the A4 fix now strips of unsent lines, so on Slack-down days a part
   gets a second unsent alert. Count relayed lines instead (judge 415).

## Addendum 2: ruling on gap F1 (the O2 builder's question, round 4a at 3abd5dc5)
**Ruling: F1 is a real gap and is fixed in O1. I agree with the direction, with one change to the design. It is a
small O1 story amendment, judged before the code.**

**Why it is real.** If the routine's container dies before about 14:55, the 3 pm parts' child processes die with it. The
rerun's log already holds `quotes`, so under judge 178 note 4 it starts no part, and NIFTY's and NSE's records are lost
while their window is still open until 15:10. That means no pack and no decision. A container death or a restarted
routine is normal enough (16 Oct showed hung and killed sessions). Note 4 was right about a dead run's *files* (never
commit what a dead part half-wrote); it was not meant to give up a window that is still open.

**My change to the design: an OS lock instead of a pid lease.** A pid can be reused, and "is pid N alive" can be wrong
after a container restart or a pid wrap. Instead:
- Each part, meaning A4's recorder process itself, holds an exclusive `fcntl.flock` on a git-ignored per-day,
  per-part lock file for as long as it runs. The kernel releases it when the process dies, whatever the cause.
- **The rerun takes the lock without blocking.**
  - If it gets the lock, no recorder is alive: release it, then restart the part if it has no canonical marker and its
    window is still open (NIFTY and NSE until 15:10, the indices until 15:13).
  - If it does not get the lock, the part is alive (same container): adopt it. Wait until the lock frees, then commit
    the part's files as usual. It never starts a second recorder.
- A4's recorder stays the guard of last resort ("already recorded" once a canonical exists). Never rely on it alone:
  two recorders racing to the canonical marker is exactly the risk.

**The amendment must also state:**
1. "Started at, restarted, adopted" for each part, in the run log (this also closes my criterion-9 note on start
   times).
2. `NOT_IN_THIS_RUN` stays only for a part whose window has closed, with one alert.
3. The tests:
   - a kill before 14:55, then a rerun in a new process: NIFTY and NSE recorded, byte-identical to the twin day;
   - a run that crashed while its part lives: the part is adopted, there is one recorder, and its files are committed;
   - a rerun after 15:10: `NOT_IN_THIS_RUN`, one alert.

   Then F1's strict xfail becomes the real assertion.
4. The indices part ("kill at versions..decisions: only the indices' record is lost") gets the same rule.
