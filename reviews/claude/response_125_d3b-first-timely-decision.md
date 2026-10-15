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

## Build claims (code)

Decision 61 (ancestry first) and judge 125's minors are built in. Evidence labels: **strong** means a test fails when
the code is broken (a plant), and **reasoning** means read in code, not tested.

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| 1 | The first of two timely original runs is collected, for each of three books | `fno/desk/committed_decisions.py` `committed` | `tests/timetable/test_first_timely_decision.py::test_the_first_of_two_timely_original_runs_is_collected_for_every_book` | strong (M2: the latest rule is caught) |
| 2 | A timely correction is never collected, and it is listed in the run log with what it corrects and why | `committed_decisions.py` `committed`, `others`; `fno/desk/daily_steps.py` `collect_decisions` | `test_a_timely_correction_is_never_collected_...`, `test_the_decisions_step_lists_the_other_runs_in_the_run_log` | strong (M1, M11, M13) |
| 3 | A day with only a timely correction has no timely decision | `committed` | `test_a_day_with_only_a_timely_correction_has_no_timely_decision` | strong (M1) |
| 4 | One order: ancestry, then commit time, then the counter as a number; uncommitted last | `fno/playbook/run_order.py` | `tests/decisions/test_run_order.py` (r2/r10, parallel, a fast clock, a chain with a parallel run, uncommitted, empty); real git: `test_a_fast_clock_that_pulled_the_first_run_...`, `test_a_ten_run_day_is_ordered_...`; S1: `tests/evaluation/test_order_runs.py::test_r2_before_r10_...`; only the shared function orders: `tests/decisions/test_one_run_order.py` | strong (M3, M4) |
| 4b | An uncommitted run is never first counted; on r1 to r9 the result equals the old name order | `fno/evaluation/order.py` `first_counted_decision` | `tests/evaluation/test_order_runs.py` (three days of nine runs and four start dates; an uncommitted earlier day is skipped) | strong (M5). `main` holds no committed decision run, so today's data is empty: the fixture stands in |
| 5 | A Book 1 trade's terms and exit come only from its opening run, and only for filled trades; another run naming it is alerted and never used; a missing, gone or changed opening run gives no terms and no exit, with the reason, never a fallback; E4's own exits still run | `fno/books/opening_runs.py`, `fno/books/book1_records.py`, `fno/books/book1_exits.py`, `fno/books/book1_wiring.py` | `tests/book1/test_opening_runs.py` (filled only; another run or a correction; a missing log; gone, re-summed and edited runs; exit-rule alerts; the first open fill's day; listing by counter); `tests/desk/test_exits.py::test_a_trade_without_exit_rules_still_gets_e4_s_risk_exits`; end to end: `tests/book1/test_book1_daily.py` | strong (M6-M10, M14, M15) |
| 6 | Scoreboard B lists uncollected runs and corrections apart; its scored figures do not change | `fno/scoreboard/committed_runs.py` `uncollected`, `whole_system.py`, `wiring.py` | `tests/scoreboard/test_uncollected_runs.py` | strong (M12) |
| 7 | The existing tests that changed, and why | see below | | |

**Broken-code proofs:** 15 plants, each caught (`M1`-`M15`); M14 survived until the first-open-fill test was added.

**Changed existing tests (criterion 7):**
- `tests/timetable/test_parts.py` (the D3 collector test) expected r2 over r1, the latest rule. It now expects r1, the
  first, and checks the others list.
- `tests/timetable/fakes.py` `Decisions.committed` took `timely[-1]`; it now takes `timely[0]`, as the real collector
  does, and gains `others`.
- `tests/book1/test_parts.py` (terms from records) and `tests/book1/test_exits.py` read terms and exits from records
  with no fill and no run log. That is now refused by design, so they first open the trade (`tests/book1/openings.py`).
  The wiring test commits the run for real, because the real wiring asks git for the committed sums file.
- `tests/book1/builders.py` and `tests/book1/test_book1_daily.py`: the git fake gains `is_ancestor` and
  `committed_bytes`, and the exit rules get `sums_at`.

**Judge 125's minors:**
1. `recorded_c4.py` and `decision_timing.py` are added to the reader table.
2. Ordering is by ancestry where it decides, by commit time otherwise (decision 61).
3. The opening-run fallback is stated: an alert, never the latest record. The exits are named: no time exit, E4
   holds the trade, and its protection, settlement and ordered exits still run (tested).
4. Only filled trades from their opening run are in the book.

**Does this change any C5 cap arithmetic?** No: C5 (risk buckets) is not on `main`, and this branch is from `main`.
On `main`, C2's book view reads terms only for open trades (`fno/risk/book_view.py:32-36`), and every open trade
comes from fills. So the extra entries the old code returned (unfilled chosen trades, runs never collected) never
reached a cap. What does change: an open trade whose opening run is missing or changed now has no terms, and C2
refuses the book view (an input error), where before the latest record's terms were used. This fails closed, and it
is listed under "Known limits" below. When C5 merges, its buckets read the same `recorded_terms`, so they follow the
opening run too (reasoning).

**Shadow trades:** no code fills a shadow account yet (only `start_shadow_accounts` exists), so no shadow trade has
terms here. E6's shadow filler must use `opening_runs` when it is built (reasoning).

## Real output sample

A repository with Book 1's original run at 15:03 and a correction at 15:05, both before the deadline:

```
collected: 2026-10-14-r1 2026-10-14T15:03:00+05:30
others: [{"run_id": "2026-10-14-r2", "commit": "1e1632b1...", "committed_at": "2026-10-14T15:05:00+05:30",
          "corrections": [{"corrects": {"run_id": "2026-10-14-r1", "opportunity_id": "sc-a-v1:2026-11-27"},
                           "reason": "corrected: wrong lot size recorded"}]}]
F&O paper desk book1_rules t1: other runs name it (2026-10-14-r2); the trade follows its opening run
F&O paper desk book1_rules t1: the run log of 2026-10-14 names no decision of book1_rules; no time exit is set, so E4 holds it
```

## Known limits (said plainly)

- An open Book 1 trade with no opening run makes C2's book view refuse. Book 1's decision then fails for the day (no
  new trade) until the record is fixed by hand. It fails closed, but `fno desk book1`'s failure is the traceback that
  E5b removes.
- The "other runs" alert repeats at every exit review while the trade is open: "once" means once per review.
- Ancestry needs both commits in the local history. A shallow clone that lacks one treats the two runs as parallel,
  so commit time decides.
