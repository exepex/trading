# Judge 664: REC1d text amendment, the recommender's sections in the 08:50 and 20:05 editions, `story/rec1d-sections` at ccc71f331 (round 1 of 2, judge K, judge 2 of 2)

**FAIL, lane 1** (forecast-lab editions), text only. 2 should-fix, 1 minor. Judged by reading.

The change against main is `docs/stories/REC1-recommender.md` alone (+39). Doc-reading tests on ccc71f331, Slack token set:
932 passed, 13 xfailed. No post in the three channels from 03:25 UTC on. I did not read judge J's verdict.

## Checks (the orchestrator's five)

| Asked | Verdict | Own evidence |
|---|---|---|
| Independent flags (school's and recommender's) | **NOT MET** (SF1) | item 2: the section shows "only with `school.reports` on, and from `daily.live_from.recommend`" |
| Byte-identical editions when both are off | MET (as text) | item 2: MS-P1g's golden files are unchanged, plus a new test; criterion (a) with the plant "section always added" |
| Per-section isolation | MET (as text) | item 1: each edition is a tuple of sections, each isolated, with its own `failure_alert`, and the others still post; the reports package imports nothing from `fno/recommend/`; criterion (d) with the plant "one shared `try`" |
| No stale check shown as today's | **PARTLY** (SF2) | the standing answer is named with its record's day, and (c) pins `<` against `<=`. The morning's check lines carry no check date, though |
| Nothing private | MET | item 5: only REC1b's line words and REC1c's check text, no record hash; an unreadable record by path and exception class only |

## Findings

1. **Should fix: the recommender's section depends on the school's switch.**
   - `school.reports` is `true` in `config.yaml` today, and it is the school's own switch (MS-P1g: "the sections ... only when `school.reports` is on").
   - Under item 2, turning the school's sections off also hides the recommender's. Showing the recommender's needs the school's on. The flags are not independent.
   - **Fix (text):** gate the recommender's section on its own key alone, `daily.live_from.recommend` or a new `recommend.reports`, never on `school.reports`. Then criterion (a) has three cases, each with its golden file: both off, school only, recommender only.
2. **Should fix: a check line in the morning carries no date, and "last evening" is not defined.**
   - REC1c's check words, `answer_text` and `trades_text` (`check_run.py:32`'s `LINE` without the record part), name the recommendation's day, never the check's `on` date.
   - Item 3 shows "the latest check of each day checked last evening", but does not say what last evening is. If it means "the latest check" of any date, an older check reads as current. If it means only checks dated last evening, then a night when `recommend check` did not run shows nothing, silently. Only a day with no check file at all is named "check missing".
   - **Fix (text):**
     - "Last evening" is the previous NSE session's date.
     - Each check line names its check date ("checked <on>").
     - Only checks with that `on` are shown as last evening's.
     - When no check file is dated last evening while recorded days wait, the section says so in one line: "last evening's check did not run".
     - Add a criterion with a plant: an older check shown without its date.

## Minor

- **m1:** item 4's "naming the run log's `recommend` status when there is one" should say the status and its reason code only (as REC1b's source statuses do), never the step's printed lines.

## For round 2

Both should-fix findings and the minor are text only: one gate, one definition and one line, plus their criteria.
