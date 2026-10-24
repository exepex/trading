# Judge 621: F1t revision 2 story text, `story/f1t-runner-v2` at 2bc4005d4 (round 1 of 2, judge K, judge 2 of 2)

**FAIL, lane 1** (books' paper trades), text only. 1 should-fix, 2 minor. Judged by reading, against the passed text
c2d2b922 (judge 301 addendum 1). The diff c2d2b922..2bc4005d4 touches only `docs/stories/F1t-ai-trading-runner.md` and
`F1t-owner-checklist.md`, so this is a text-only change. Doc-reading tests on 2bc4005d4, Slack token set: 922 passed,
14 xfailed. I did not read judge E's verdict.

## Checks (the orchestrator's five)

| Check | Verdict | Own evidence |
|---|---|---|
| Nothing passed was loosened | MET | criteria 1-15 are unchanged; 16-18 are added. Addendum A's judge step is folded in unchanged. F1t's base `seal` check now also needs `action`, which is stricter and matches F5's passed shape (`F5-book2.md:82-88`). The old go-live check 3 ("a paper strategy, or no trade daily") becomes check 4 with the same effect. New go-live checks: F4 for Book 2, D6 registration, full history, the model on the test fire |
| Deadline and seal under v4's timeline | MET | decision seal by 15:10:00 (observation 1), reveal 15:10:10, observation 2 15:11:00, E3 deadline 15:12. G11's v4 forecast routines of the same books reveal at 15:10:10 (`fno/ai/book.py:9`, "15:10:10 under v4"), after every decision seal, so one book's v4 forecast cannot reach the other book's decision before it is sealed. The overlap is safe on the clock, but the text does not say so (m1) |
| Unknown model = no trade, and its proof before go-live | **PARTLY** (SF1) | `model_unverified` is no trade (unchanged), and go-live check 6 requires the test fire to report the registered model. But the reported model can be the wrong one; see SF1 |
| A rehearsal never fires a routine | MET | criterion 18: under `rehearsal()`, no `RoutineTrigger` is built, no HTTP call is made, and the step is `refused` with `ai:REHEARSAL_NO_FIRE`; with no book live it is `not_live` as in a real run; the trigger factory is a spy |
| NoJudge fails closed | MET | until F4 merges, `NoJudge` gives `unavailable` ("judge not built (F4)"), so Book 2 is `judge_failed` every day; Book 3's verdicts never block (F4's design); criterion 16 tests both; Book 2's go-live needs F4 |

## Findings

1. **Should fix: "model_reported" can claim the registered model while another one serves.**
   - The fixed answer rule (unchanged from judge 301) takes first "the exact model ID the session's own instructions state", then the tool's `session_context.model`.
   - Both name the model the session is *set* to run, not the one serving it. A Claude Code session's own instructions say plainly that the serving model "can differ from that and can change mid-session" (fallbacks). The tool reports the served model apart: `external_metadata.last_served_model`.
   - So on a fallback day, a book could report and record a "match" while an unregistered model decided: a wrong attribution in a lane-1 record. That is the opposite failure to "unknown".
   - The 15-23 Oct evidence (10 of 11 `unknown`) makes this rule the one that decides whether the books ever trade, so it must be right.
   - **Fix (text):**
     - with the tool, `model_reported` is `external_metadata.last_served_model`, recorded beside the configured model;
     - a difference between them is `model_mismatch`, no trade;
     - with the instructions line only, record its source (`instructions`), and state whether that counts as verified: an owner or orchestrator ruling, put plainly;
     - go-live check 6 names which source the test fire must show.

## Minor

- **m1:** state in the timeline that every decision seal (15:10:00) comes before any reveal (forecast or decision, 15:10:10). That ordering is what keeps the overlap honest. Also add to Known limits: four reveal pushes to `main` at 15:10:10, beside the daily run's own pushes, can race; a reveal that still loses at 15:11:00 is `not_revealed`, never a trade. Add it to the test fire's checks.
- **m2:** "a meter that cannot be read fires the books ... as G11 does" is fail-open on cost. Say it is deliberate: cost only, never a trade risk, and the owner set no cap.

## Notes

- Open question 1 (does 25 Oct lift the 15 Oct "strategy passed first" rule?) is correctly put to the owner, with the builder's recommendation labelled. The code is the same either way.
- The orchestrator's two earlier notes hold: the timeline, and that a slow `book1` never moves an observation (the child-process observer, judge 301).
