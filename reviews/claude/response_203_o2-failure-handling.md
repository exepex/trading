# Response 203: story O2, failure handling end to end (story text, claims for the judge)

Branch `story/o2-failure-handling`. Text: `docs/stories/O2-failure-handling.md`. Lane 1. Code after O1 merges
(owner, 16 Oct; orchestrator).

## Claims

1. Each failure behaviour O2 tests is already built and judged in its own story: C3, C4, E3/E2b, E2c, O1 and O8.
   O2 adds a suite, not new behaviour. **Strong evidence:** the files named in the text's context section.
2. No test today drives the whole day through a real outage. Each part is tested with fakes for the rest.
   **Strong evidence:** `tests/timetable/`, `tests/daily/`.
3. REPLAN's "monitor heartbeat" belongs to LM1, which is not built. O2 builds no second heartbeat (one builder per
   function). The daily routine's own "never started" chain (no log, then O8's "never ran", then the next session's
   entry block) already exists and is proven here. **Strong evidence:** `REPLAN_new_stories.md` LM1, design 4.2 and
   6.5, and `DailyRun._unreviewed` with `NO_LOG`.
4. Design 9's AI rows ("a role fails to report", "judge or AI unavailable") cannot be tested until the AI books trade
   (F5/F6). Broken protection waits for E4c. **Strong evidence:** the work register; no AI order code on `main`.
5. A kill-after-each-step rerun that gives byte-identical records is the right test of "a partial run and its
   rerun": E3's rule is that a rerun repeats nothing. **Reasoning only** until the suite runs.
6. Today's run alerts do not follow design 6.5's first-line rule. I recommend a separate story for that.
   **Strong evidence:** the alert templates in `fno/daily/steps.py` and `fno/desk/daily_run.py`. The recommendation
   itself is reasoning only.

## Open points (sent to the orchestrator)

- The design 6.5 first-line rule, in a separate story (recommended) or inside O2.
