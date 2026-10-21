# Judge 417: O1 fix text, a rerun resumes the 3 pm parts (story/o1-part-lock at d68e46aa)

**Verdict: FAIL, 1 should-fix (small). The rest matches judge 412 addenda 2-3.**

| Point | Result | Evidence |
|---|---|---|
| An OS lock per part and day, never a pid | MET | an exclusive `fcntl.flock` on git-ignored `journal/runs/.parts/<date>_<part>.lock` |
| Adopt a live part, never a second recorder | MET (but see should-fix 1) | "lock held: adopted" |
| A part an earlier run recorded is `ok`, never `NOT_IN_THIS_RUN`, and its uncommitted files are committed | MET | "every canonical marker present: recorded by an earlier run, ok. Any of its files still uncommitted are committed" |
| Restart only while the window is open, from A4's constants | MET | `WINDOW_END` 15:10, `INDEX_WINDOW_END` 15:13; the part's own `not_before` and `starts_after` |
| `NOT_IN_THIS_RUN` only after the window, with one alert | MET | |
| `how` and the start time logged per part; the "from 14:38" wording | MET | closes judge 178 addendum 19's note |
| The four tests, and F1's strict xfail made real | MET | |

**The builder's choice, which I accept:** the run takes the lock and hands the open file to the child (`pass_fds`), then
closes its own copy. The lock belongs to the open file, so the child holds it for its whole life and the kernel frees it
on death. A4's commands are untouched while A4's builder works on `cmd_quotes`. Python's `subprocess` defaults to
`close_fds=True`, so the recorder's own subprocesses do not inherit it.

## Should-fix 1: the adopt wait has no bound
"The run waits for the lock to free, then commits." A crashed run's part can be the very thing that hung (a Groww call
that never answers is why O1 has a 600 s command limit). A live but hung recorder holds the lock indefinitely, so an
unbounded wait holds the day, the 15:15 exits included. This is a concrete path in normal running.

**The text must say:**
- the adopt wait runs inside the parts' existing `finish` bound (`FINISH_LIMIT`, and not before `fills_by`) and is
  serviced like any other wait, so the desk's steps go on meanwhile;
- past the bound, the adopted part is `failed`, "still running after …", with one alert, and its files are not
  committed (they may be half-written), exactly as for the run's own part past the limit;
- the run cannot kill a process it did not start. Say so, and name the hand fix in the alert ("a 3 pm recorder of an
  earlier run still holds <lock>: stop it, then rerun"). Optionally, the holder can be found through `/proc/*/fd` for
  the message.

## Clarification to add (not a should-fix)
An adopted part's stdout and exit code are gone with the crashed run. Say that its status comes from its files: `ok`
when its canonical marker exists after the lock frees, otherwise `failed` "adopted part ended without a canonical",
with one alert. Also say that NIFTY-first still holds: no other part commits before NIFTY's commit is made or tried,
whatever `how` NIFTY's part has.
