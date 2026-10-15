# Response 125: story D3b, a book's timely decision is its first original run (story text for the judge's story check)

Builder: Claude. Branch `story/d3b-first-timely-decision`, from `main` at 49b09b1. Story text
only. Orchestrator decisions 58 and 59 (b). Quality rule 9 applies after the code PASS.

## What the story asks (docs/stories/D-playbook-decisions.md, "D3b")

- E3's collector takes the first non-correction run committed before the deadline, for every book.
- Corrections, and other runs it did not take, are recorded in the run log and shown apart on scoreboard B, never
  collected or scored.
- Runs are ordered by commit time, then by run counter as a number.

## Facts found in code (strong evidence unless marked)

| Fact | Where |
|---|---|
| The collector takes the **latest** timely run | `fno/desk/committed_decisions.py:36-41` (`reversed(runs)`) |
| Run folders sort by name, so `-r10` comes before `-r2` | `fno/playbook/decision_store.py:41-45` |
| Book 1's orders and exits read **every** run's records, keyed by trade ID, so a later record with the same ID replaces the earlier one | `fno/books/book1_records.py` `decided_trades`, `recorded_terms`, `decided_exit_days` |
| A fill's `decision_id` is the opportunity ID, not the run | `fno/books/book1_orders.py:4` |
| No correction writer exists yet (`corrects` is always None) | `fno/playbook/decision_record.py:93` |
| The card and the packs read no decision run | `fno/cards/`, `fno/desk/pack*.py` |
| S1's first counted decision already takes the first run, by folder name | `fno/evaluation/order.py` `first_counted_decision` |

## Decision 60 taken into the story

- One shared ordering function (commit time, then the run counter as a number) for the collector, the run log,
  `book1_records` and S1's `first_counted_decision`. A test fails if any caller sorts run folders itself.
- `fno/evaluation/order.py` is in no freeze: `git ls-tree origin/main research/evaluation/` lists only `PROTOCOL.md`.
- "Unchanged on today's data", said plainly: `main` holds no committed decision run yet (`git ls-tree -r origin/main
  journal` finds no `records.sha256`), so today's data is empty. The test that matters is a fixture of runs r1 to r9,
  where the old and new orders must agree.
- The `book1_records` fix stays the core: the opening run is the source of truth, and a later record naming the trade
  gets one alert.
- The test that must change is named in criterion 7: `tests/timetable/test_parts.py:113` (r2 over r1).
