# Judge 632: F5 text revision for Q11 (story/f5-book2-q11 @ a369d4f0b), judge B (2 of 2), round 1 of 2

**FAIL (2 blocking, 1 should-fix, 1 minor). Lane 1** (Book 2's paper trades: a money piece, two judges). I judged it by
reading against the owner's Q11 (DESK_DECISIONS row 345: research candidates as Book 2's rule defaults, labelled
"strategy not yet passed", D2's unproven limit, Book 1 unchanged, paper only) and the code on main. I did not read
judge I. Doc-reading tests: 922 passed, 14 xfailed (token kept); record scan clean.

## Criteria (the orchestrator's three questions)

| Question | Result | My evidence |
|---|---|---|
| Can a research rule reach Book 2 without the label? | PARTLY | the text has D3 write `served["strategy_status"]`, and criterion 13 tests it; the refusal of a chosen trade without it is F1t revision 2's run check, not on main (judge 621.1/623: FAIL stands). See m1 |
| Can the limit be bypassed? | YES, two ways | B1 and B2 below |
| Is there a second copy of the approved set? | YES, unnamed | B1 and SF1 below: `approved_on`, `validity_adapter.py:52`, `scorecard/run.py:35` |
| One `book2_tradable` for sheet and C4 | PARTLY | intended; but how it replaces `approved_on` in D2's `RuleEvaluator` and C4's adapter is not stated (SF1) |
| D2's unproven limit unchanged | MET for its own check | `allocation.py:75-80` counts per version from the book's own desk records (`desk/trade_counts.py`), so Book 2's open research trade blocks a second |
| Criterion 13: Book 1 byte-identical | MET as text | named, with its test |

## Findings

1. **Blocking B1: `book2_tradable` includes `paused` versions, which Book 1 may never trade.** The text defines it as
   "the versions D2 approves for paper (`paper`, `paused`)". D2 approves `paper` only. `Playbook.approved()` and
   `approved_on(day)` (`fno/playbook/loader.py:42-66`) take `paper` at the start of the day and still `paper` through
   it ("a pause or retirement stops new entries at once"). `PAPER_STATUSES` in `activation.py` is the activation gate's
   use class, not the approved set. As written, a version paused by E6's hard-loss rule or by the owner would stay
   open for new Book 2 entries. Fix: `book2_tradable` = `approved_on(day)` (the same day rule) plus the registered
   `research` versions by the same start-and-through-the-day rule; never `paused` or `retired`; and a test with a
   version paused that day.
2. **Blocking B2: E6's automatic loss pauses never stop a research version Book 2 trades.**
   - `scorecard/pauses.py` `cumulative_losses` counts a `research` version only on a shadow account
     (`status == RESEARCH and shadow`). Book 2's real-paper trades of it are skipped.
   - `_counts` makes a research catastrophic loss count only on its close day.
   - `AutoPauser.apply` (`pauses.py:128-145`) pauses only `paper` versions. A research trigger is alerted as "shadow
     only" and the version keeps trading.

   So under Q11 a research version on Book 2's book has no cumulative-loss cap, and no pause after a catastrophic
   loss; only D2's 1-open-trade limit remains. Fix: say how E6 counts and stops a research version on a real paper
   book. For example: count Book 2's trades of it from its first Book 2 trade, like an approved version's since its
   approval; and a trigger removes it from `book2_tradable`, a Book 2 pause that leaves the registry and Book 1 as
   they are. Name the files, and add tests for both caps.
3. **Should-fix SF1: where `book2_tradable` replaces the approved set is not named.** `RuleEvaluator.evaluate`
   (`playbook/evaluate.py:50-53`) reads `playbook.approved_on(day)` for book mode and `playbook.shadow_on(day)` for
   shadows; it takes no set. C4's set is built at `fno/checks/validity_adapter.py:52` from `approved_on`. The text must
   say how Book 2's sheet and C4 get `book2_tradable`, by a Book 2 playbook view or a parameter, without changing
   Book 1's path (criterion 13). It must also say that Book 2's sheet evaluates no shadows: otherwise a research
   version is evaluated both in book mode and as a shadow, and Book 2's run writes into D2's shadow books.
4. **Minor m1:** the label's refusal depends on F1t revision 2, which is not on main. Name it as a merge-order
   dependency (F5's code merges after it), or have F5's own C4 or D3 check refuse a chosen research trade without
   `strategy_status`.
