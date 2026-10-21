# Judge 418: O1 fix, a part's own alert read from its whole output (story/o1-part-alerted at 30237369)

**Verdict: PASS. Lane 1. Merge soon: the regression is live on main since 1f005e5a** (the A4 fix that strips unsent
lines from `lines()`, as judge 412 addendum 1 note 2 and judge 415 predicted).

| Check | Result | Evidence |
|---|---|---|
| The root cause | MET | `QuoteParts._finish` decided "the part alerted itself" from `lines()`, which no longer holds "alert NOT sent", so on a Slack-down day a part whose own alert went unsent also got `PART_NOT_OK`: two unsent lines for one failure |
| The fix sits on the interface, not in a patch | MET | `Process.alerted()` (abstract), `ChildProcess.alerted()` reads the whole output via `alerted_in`, `ALERT_OUTCOMES = (SENT, UNSENT)`; `_finish` takes it |
| Privacy is kept | MET | `lines()` still drops unsent lines; the test checks the folder ID never appears in the kept lines |
| A test with the real `ChildProcess` | MET | `tests/daily/test_part_alerted.py`: unsent, sent and silent, exactly one alert each |
| Planted mutation | caught | `alerted()` reading `lines()` instead of the whole output: 1 failed |
| Gates on a trial merge with main | MET | 8660 passed, 17 xfailed, 0 failed; ruff and check_imports clean |

**Note (not should-fix):** `alerted()` is true for *any* own-alert line, so a part that posted an unrelated alert (for
example "no same-day trades") and then failed for another reason gets no `PART_NOT_OK`. The old rule behaved the same,
and the part's own alert still names it; worth a test when A4's alerts change.
