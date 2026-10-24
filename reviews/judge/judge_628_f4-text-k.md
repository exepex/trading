# Judge 628: F4 story text, the AI books' daily code judge, `story/f4-ai-judge` at fe5721d39 (round 1 of 2, judge K, judge 2 of 2)

**FAIL, lane 1** (decides Book 2's trades), text only. 1 should-fix, 1 minor. Judged by reading.

The change against main is Markdown only: `docs/stories/F4-ai-judge.md` (new, 232 lines), `F-ai-layer.md` (F4's old
section replaced by a pointer), response 271 and its README row. Doc-reading tests on fe5721d39, Slack token set:
922 passed, 14 xfailed. I did not read judge E's verdict.

## Checks (the orchestrator's four)

| Check | Verdict | Own evidence |
|---|---|---|
| The `JudgeStep` port is F1t's only copy | PARTLY (SF1) | F4 design 4: "`JudgeCase`, `Judged` and the `JudgeStep` interface are F1t's ... F4 defines no second copy". `JudgeCase`'s fields (book, day, registered_model, decision, common, private, common_sha256, private_sha256) match F1t's call on main (`F1t-ai-trading-runner.md:357-359`). But the type `Judged` carries is not in the port; see SF1 |
| NoJudge fails closed for Book 2 until F4 lands | MET (as text) | F4 design 4 and F1t's "The judge" on main: `NoJudge` is always `unavailable` ("judge not built (F4)"); `blocks` is true for Book 2 when not `pass`, so every Book 2 day is `judge_failed`, never a trade. F1t criterion 16 tests it |
| Book 3's verdicts never block | MET | design 3: `blocks` is "true exactly when the book is Book 2 and the status is not `pass`; for Book 3 it is always false". Criterion 2: the same failure on Book 3 gives `blocks: false` and a verdict file |
| Judge 308.1's remaining item closed by F1t revision 2 | MET | on main (F1t at 4dbf786d7, merged): `judge_step.run(JudgeCase(...))` before `decide()` (line 357); `AcceptedDecision.judge: str` and `judge_blocks: bool` (327-328); the run check refuses a chosen trade under `judge_blocks` (351); the 5 s budget inside the 15:11:00-15:12:00 window (364). All four items 308.1 named are there |

## Findings

1. **Should fix: the verdict type that `Judged` returns has no owner in the port.**
   - `Judged(verdict, path)` is F1t's. F1t reads `judged.verdict.blocks` and the verdict's reason line, and F1t's `NoJudge` must build an `unavailable` verdict before F4's code exists.
   - But F4 design 3 puts the verdict in F4's own `fno/judge/verdict.py`. As written, either F1t's `ports.py` imports `fno/judge` (a port depending on its implementation, and impossible before F4 merges), or `NoJudge` builds something else, which would be a second shape.
   - **Fix (text, in F4 and, by one line, F1t):** the port also holds the small verdict type `ai_collect` reads, for example `JudgeVerdict(status, blocks, reason)`, beside `Judged`. F4's `verdict.py` builds the full file content (design 3's fields) and returns that type in `Judged`; `NoJudge` returns it too. Name it in both texts so there is one shape.

## Minor

- **m1:** say what `NoJudge`'s `Judged.path` is. F1t needs a path for `AcceptedDecision.judge`, and "every record's `judge` equals it". Does `NoJudge` write a verdict file ("judge not built (F4)"), with design 3's fields where they apply, to `journal/ai_decisions/<YYYY>/<d>_<book>_judge.json`, or is the path empty and the check skipped? I recommend the file, written once: the day's no-trade reason then has its record.

## Plants

None: text round.

## For round 2

SF1 and m1 are text only, in F4 plus one line in F1t's "The judge" paragraph (the type's name). No code and no
new evidence are needed; round 2 can pass by reading.

## Notes

- `F-ai-layer.md` now points to `F4-ai-judge.md`. The old six criteria are carried there: Book 2 blocks and Book 3
  records, a missed budget is `unavailable` (Book 2 no trade), and the monthly audit.
- The owner's "code daily + AI monthly" (16 Oct) and the 308 addendum's closed items stand unchanged.
