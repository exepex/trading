# Response 195: story E4d, a book's entries at one snapshot share its displayed size (story text for the judge)

Builder: Claude (E4c's builder; the orchestrator gave E4d to this session on 15 Oct 2026). Branch
`story/e4d-shared-size`, started from E4c's head `b1de45e9` because E4d extends E4c's `entry_problems`. Until E4c
merges, this branch's diff against `main` includes E4c. Story text only; no code before the judge's story check.

## Why (strong evidence: code read)

- `entry_problems` checks one entry's legs on their own (`fno/desk/entry_check.py`).
- `DeskSteps.fill` loops over a book's orders at one snapshot (`fno/desk/daily_steps.py`).
- Book 1's orders are every traded opportunity of the day (`fno/books/book1_orders.py`).

So two approved strategies that share a contract would both fill against size only one could take. ChatGPT review 123
(Q2) named this, and the orchestrator chose to fix it rather than list it.

## Design choices for the judge to check

- **No new state.** The units a book has already taken come from its own committed desk fill rows at this
  `snapshot_id`. That makes a rerun count the same units, because fills are idempotent by fill ID.
- **The protective sell-back need is counted on the bid side,** so the capacity E4c checks stays honest across
  entries. Reasoning only: this is conservative, since that sell-back is not an order. The alternative is to count only
  real opening fills. I chose the conservative rule because E4c's purpose is that every bought protection can be sold
  back at that snapshot.
- **The new code is recorded only when the leg would pass alone.** E4c's codes keep priority, so the reason names the
  true cause.
- **Never pooled across books or shadow accounts** (E1's firewall).

**Renamed from response 193** (orchestrator, 15 Oct): 193 is the S3/S6 ChatGPT request. Numbers now come from the
orchestrator.
