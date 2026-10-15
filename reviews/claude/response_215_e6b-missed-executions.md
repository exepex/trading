# Response 215: story E6b, missed executions in E6's scorecard and S2's board (story text for the judge)

Builder: Claude (session 0134MoC6, E4c and E4d's builder). The orchestrator assigned it on 15 Oct 2026: "take the item-10
reporting follow-up, story text first". Branch `story/e6-s2-missed-execution`. This is story text only. The code waits
for E8, and for S6's follow-ups (`story/s6-followups`), to merge.

## Why (strong evidence: code and register read)

- S1 pending edit (10), in `docs/WORK_REGISTER.md` (S1 text row), collects ChatGPT reviews 122, 123 and 126 (responses
  190, 192 and 209). It asks for net per executed fill and per eligible opportunity, the fill rate, and the misses by
  reason, per strategy and book. It also says: "code follow-up for E6 and S2 raised when E8 merges".
- E6's `execution_costs` (`fno/scorecard/execution_costs.py`) counts every `not_opened` and every partial fill as one
  `not_filled` number, with no reason split.
- S2's board (`fno/scoreboard/book_board.py`, `book_trades.py`) holds filled trades only, so a strategy's misses are
  not on it.
- E8's `TimingReport` (story text) would be a third counter of the same thing. This story makes it one shared class.

## Agreed before the judge (one builder per function)

- **E8's builder (session 01H1CmuW), 15 Oct:**
  - An E8 entry miss is a `not_opened` desk event, with one of E8's eight fixed reasons. There is no new outcome
    code. I accepted this: one outcome for "this opportunity did not become a trade" is what E6 and S2 should count,
    and the reason table tells the cases apart.
  - `entry_pending` means awaiting fill. It is in no denominator until its fill or miss lands.
  - E8's blocked-book refusal is `refused`, a gate refusal.
  - `TimingReport` calls the shared class once per view account. The class takes one account and has no view logic.
- **S1, S2 and S6's builder (session 0185gR5D), 15 Oct:**
  - The rule is its own protocol item, `execution_opportunities`, which they word and land, with status "proposal,
    owner decides".
  - The new module is named explicitly in `frozen_files`.
  - The counter is pure, with no desk I/O.
  - Gate refusals stay out of the denominator and are shown beside the block.
  - On the board, only `book_board.py` gains calls. `sections.py` (S6's file) is unchanged, and the build follows S6's
    follow-ups.
  - Their two corrections were taken in full:
    - (a) an unwound partial fill enters net per opportunity with its actual C1 net, never as 0;
    - (b) an open trade is neither 0 nor a miss: it is counted apart as "open".

## Design choices for the judge to check

- **What counts as an opportunity:** an entry that reached the fill step. The outcome is `opened`, a partial fill, or
  `not_opened` for any reason.
  - Gate refusals (`refused`) are counted apart. Reasoning only: they are risk or data decisions, not failed
    executions. S1's owner agrees, and scoreboard A treats account limits the same way.
  - Not covered: run-level misses (a session with no collected decision). S6's `missed_runs` reports those.
- **Reasons come from one fixed table.** An unknown reason is "other": counted, never dropped. E8's reasons are
  imported from E8's modules, never copied (DRY).
- **Reported only:** no verdict, review, pause, brake, uncertainty test, do-nothing comparison or random control
  changes.
- **The block on the board:** each book's overall section and each strategy entry. It is not on the pilot,
  head-to-head or segment sections. Reasoning only: a miss has no `opened_on`, and putting it in the segment and pilot
  splits would need a rule this story does not set. One line can add it later if S1 asks.
- **E6's present entry line is replaced by the block,** so there is one entry count, not two. The changed report line
  will be stated in the code claims.

## Open for the owner (not decided here)

- Whether `execution_opportunities` becomes "decided". S1's owner keeps it as "proposal, owner decides".

## Addendum 1: ChatGPT review 131 (response 221), text only

I checked review 131 before adding it:
- its arithmetic holds: (9 x 900 - 250) / 10 = Rs 785, and 22 of 30 = 73.3% against 20%;
- its five points fit the design: reporting only, one counter and no new engine.

The story now has:
- the chain from chosen decisions to closed or open;
- gate refusals per strategy and book, by reason, from one named table of the desk's refusal prefixes (checked in
  `entries.refusal`: "risk manager refused", the risk decision not matching, "decision committed at", the snapshot
  incomplete, "open trade ... blocks"; C3's data checks), with unknown ones as "other";
- "fills 20 of 20" next to "opened 20 of 100 decisions";
- the Rs 785 example;
- `open_count`, the oldest open age and the "closed only, provisional" label;
- the cohort label, with a date and version filter in the same counter.

These are covered by new criterion 9. The engineering criterion is now 10.
