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

## For the orchestrator

- S1's `first_counted_decision` sorts runs by folder name. It is right until a day's tenth run. It is S1's code, so
  I list it and do not change it. Your call whether D3b takes it too.
- A test that must change: `tests/timetable/test_parts.py:113` expects r2 over r1 (the latest rule). It is named in
  criterion 7.
