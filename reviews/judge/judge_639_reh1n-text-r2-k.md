# Judge 639: REH1n story text round 2, `story/reh1n-new-quote-parts` at 5fa97694c (round 2 of 2, judge K, judge 2 of 2)

**FAIL, lane 1** (what `fno/quotes/` takes as a good result; what a rehearsal posts), text only. 1 should-fix, 1 note.
Judged by reading. The change against main is `docs/stories/REH1-rehearsal-mode.md` alone (+91 lines). I did not
coordinate with the 635 session.

**Doc-reading tests** on 5fa97694c, Slack token set:
- Runs 2-5: 932 passed, 13 xfailed.
- Run 1 had 1 failure, under load (109 s against 46-50 s). Its name did not print, and the four reruns did not reproduce it.
- The diff is one Markdown file, so a test reading it would fail every time; this failure is not REH1n's.
- No post in #fno-desk, #fno-forecast or #fno-intraday from 00:11 UTC on.

## Checks

| Asked | Verdict | Own evidence |
|---|---|---|
| SF1: a marker OR a sidecar on or before D | MET | Design 1 states it, with the reason (A4 writes each attempt's sidecar at once and the marker later). N3 adds the case "only one sidecar on D, no marker", which stays "window closed", alerted, exit 1, with the plant "the rule reading markers only" |
| m2: steps with their own live key | MET | the gap list's last row: each is its own `LiveFrom` step, `not_live` before its key's date, and outside REH1n's scope |
| m3: the register row | MET | `WORK_REGISTER.md` on main, line 110: REH1n's row names `fno/quotes/indices.py`, `fno/quotes/cli.py`, `recorded_quotes.py` and `exercised_line.py`, and that the orchestrator is told in place of the gone A4c/A4f owner |
| `recorder.py`, `constants.py`, `window.py` byte-identical | MET | `git diff --quiet origin/main 5fa97694c` is empty for all three; the branch's own diff is the one story file |
| The one wrong case, restated | **PARTLY** (SF1) | see below |

## Findings

1. **Should fix: the wrong case is wider than "a crash before the first attempt's sidecar".**
   - The rule reads `mode.record`: the checkout's committed record (`fno/rehearsal/mode.py:32`). An attempt's sidecar reaches it only when its part ends and the run's one thread commits it (`fno/daily/quote_parts.py:1-8`), not when A4 writes it.
   - So on a capture's first day, the record can also hold nothing for a part that *did* run. Three ways, all in today's code:
     - **a hung part:** `HUNG` = "still running at HH:MM, after its window: stopped, nothing of it committed" (`quote_parts.py:48`);
     - **a part never committed:** "NOT committed" with no hand fix, or "committed, NOT pushed" when no later push carries it (lines 33-35);
     - **a lost container:** the container dies mid-part, and the local sidecars go with it.
   - Each reads as "not a part of the day" on that first day, never a failure. Monday is v4's first live day, so these are its exposures too. A v4 part that hangs past 14:40 is the likeliest of them.
   - **Fix (text):** state the case as "no sidecar or marker of the stem reached the record by D", and name the three paths.
   - Optional closer (reasoning only): for a stem that is a part of its own (the `v4` dataset), the real `journal/runs/<D>.json` already records each part with `started_at` (for example 23 Oct's `quotes_done.result.parts`). A part listed there is a part of D, so its empty record is a failure. A stem inside a part (the weekly in `indices`) has no such witness, so for it the text is the fix.

## Note

- "Never reads a day after D" goes by the file's day, not by when it was committed. A sidecar dated D but committed on D+1 (a hand fix) counts. That makes the stem a part (stricter), never "not a part", so it hides no failure. REH1p's visibility rule is the right place if the dates should also be commit times.

## For round 2's close

This is the last round, so the owner or the orchestrator decides. SF1 needs only the restated wrong case: one paragraph, no code. With it, I would pass the text.
