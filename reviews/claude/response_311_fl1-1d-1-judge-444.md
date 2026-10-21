# Response 311: FL1-1d-1, judge 444 answered

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd) to Judge E, 22 Oct 2026. Branch `story/fl1-1d-two-editions`
at `dd6f4f5b` (main merged).

**Should-fix: a failure before the post sent no alert. Accepted.**
- **Checked:** your probe holds. `build_edition` raises when Drive refuses the sync, and a composer can raise too.
  Neither was caught, and outside O1's `Alerted` nothing else alerts.
- **Fix:** `edition_run.guarded(edition, day, build, desk)` wraps both the build and the run.
  - On any exception it sends one #fno-desk alert: "the <edition> report was not made (<error type>); nothing was
    posted". Only the type is sent, never the message, so no path or setting leaks.
  - It prints that line, plus the alert's text when the alert was not sent, so the routine can post it by hand.
  - It exits 1. `cli._edition` uses it.
- **Tests:** a raising composer, and a raising build with no token (the unsent alert is printed with its text).
- **Mutations:** 3 of 3 caught (alert not sent, unsent line not printed, the cutoff recheck removed).

**Minors: all accepted.**
1. **CLAUDE.md's F&O output line** now names the morning (08:50) and evening (20:05) editions.
2. **The 09:15 cutoff is checked again just before the post,** after making the report. Test: a making that runs
   from 09:14 past 09:15 posts nothing and alerts once.
3. **Making-and-posting time is noted for the first live mornings,** against the 08:38 start and the 08:50 slot. I
   will report the measured times. Until then, honestly, I have no measurement: making the report means syncing
   G13b's records, A17's tables and NSE's files, plus drawing the picture, and none of it has been timed live.

**Gates** (one run, on the branch merged with `main`):
- 9,176 passed, 16 xfailed;
- `ruff check` clean; `ruff format --check` clean;
- imports clean; record scan clean (7,433 files).
