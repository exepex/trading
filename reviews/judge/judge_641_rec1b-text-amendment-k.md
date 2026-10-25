# Judge 641: REC1b text amendment, `story/rec1b-daily-record` at 6460a4ce3 (on 1daf19e1; round 1 of 2, judge K, one judge)

**FAIL, lane 1** (the recommendation record; a #fno-desk post), text only. 2 should-fix, 2 minor. Judged by reading.

The amendment `1daf19e1..6460a4ce3` touches `docs/stories/REC1-recommender.md` alone (+57/-14). Doc-reading tests
on 6460a4ce3, Slack token set: 922 passed, 14 xfailed. The three channels have no post from 00:21 UTC on.

## Checks (the orchestrator's five)

| Asked | Verdict | Own evidence |
|---|---|---|
| Timing independent of market hours | MET for `recommend`; **not** for its school input (SF2) | `DAILY_RUN_STEPS` on the branch: `... card, price_distribution, premium_ranges, school, ...`. The new step goes after `school` and before `candles` (the only later wait, 15:33), so it never waits. The text says it reads sealed records only and is never refused after 15:30 |
| Can an unavailable source look complete | **YES** (SF1) | see below |
| Schema change safe with no record | MET | `fno/recommend/` is not on main (`git ls-tree origin/main`: none), and `config.yaml` has no `recommend` live key, so no record can exist. Adding the required `candidate_sources` before the first write keeps version 1 honest |
| The #fno-desk line leaks nothing | MET (see m2) | the sample holds answers, reason codes, counts, the receipt path and a 12-character hash prefix; criterion 10 scans the line against the record's private fields |
| Card byte-identical | MET | `git diff origin/main 6460a4ce3 -- fno/cards` is empty; `fno/cards/wiring.py` has left REC1b's file list; the card runs before `recommend` and reads nothing of it; criterion 10's golden file covers the step on and off |

## Findings

1. **Should fix: "complete" is not defined, and today's school step is `ok` while it ran nothing.**
   - With `school.enabled: false`, which is the value in `config.yaml` on this branch, `school run` prints "school off" and exits 0. The step is then `ok`, with reason `school:OFF` (`fno/daily/reason_codes.py:103-108`).
   - The text says a source is `complete`, or `unavailable` "with the source step's status (for example not_live, failed, refused, frozen)". Read by status, an `ok` school step that did not run is complete, with no candidates. That is the empty complete list the ruling forbids. The same holds for `school:NOT_A_SESSION`.
   - **Fix (text):** define `complete` positively: the step is `ok` and the source's own record shows it ran.
     - The school: `SessionRun.status == ""`, and its sealed decisions are read and hash-checked.
     - `desk:book1`: Book 1's decision record is present and hash-checked.
     - Anything else is `unavailable`, with the step status and its reason code. That covers `ok` with `school:OFF`, `not_built`, `exercised`, and a step missing from the run log.
     - Add the plant "school off read as complete".
2. **Should fix (text): the stated timing implies the school is refused.**
   - The school step is `StartsBy(..., SCHOOL_STARTS_BY)`, and `SCHOOL_STARTS_BY = 15:25` (`fno/daily/wiring.py:37`, `school:TOO_LATE`).
   - Section 1 puts the record at 15:27-15:30, after the school's 77 s, so the school would start at about 15:26 or later. That is after its own start limit.
   - With GW1 moving the desk's fills later (judge I's finding), the school source would be `unavailable (refused)` on most days. The record would handle that correctly, but the ruling's purpose would be lost.
   - **Fix:** state the dependency, and correct the estimate. The orchestrator should settle GW1's new `fills_by` against `SCHOOL_STARTS_BY` before REC1b's code is written. REC1b's own code need not change.

## Minor

- **m1:** "an unavailable source that holds a rung-3 version" must say where that is read from: the version's rung records, never the source that could not be read.
- **m2:** the line and the card answer side by side in #fno-desk (card: "NO TRADE (no_approved_strategy)"; line: "Paper: NO TRADE (no_established_version)"), and later they can differ (a `PAPER_TRADE` line beside a NO TRADE card). Say in the line which one it is. Also say whether `ELIGIBLE_FOR_YOUR_OWN_REVIEW` names the version in the line. A version ID is not an internal, but the text should state it.

## For round 2

All four are text only: the definition of `complete` (with its plant), the timing line, and two sentences.
