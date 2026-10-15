# Response 104: F8 (minimal) AI usage and cost, and BG1 budget meter and stop-rule tracker

Builder claims for the judge. Lane 1 (new stories; touches accounting records and the owner's budget rule). Branch
`story/f8-bg1-budget`. Story texts: `docs/stories/F-ai-layer.md` ("F8 minimal", original F8 kept above it) and
`docs/stories/BG-budget.md` (BG1). Nothing is scheduled, nothing is posted to Slack, no order code is touched.

## What was found before building (facts checked on 15 Oct 2026, strong evidence: read with the session tools)

- `list_events(kinds=["result"])` gives per finished turn: `duration_ms` (wall time), `usage` (main-loop tokens),
  `num_turns`, plus `modelUsage`/`total_cost_usd` running totals at **API list price** ("costBasis": "list"). The list
  price is not what the owner pays on a plan, so it is not used anywhere.
- `duration_api_ms` can exceed `duration_ms` (8,206 ms wall vs 33,957 ms API on one orchestrator turn): parallel calls.
  Minutes here are wall minutes of turns.
- Per-turn `usage` misses side calls: the `modelUsage` output totals grow by 2,091, 359, 3,851, 12,996 and 1,419 while
  per-turn `usage.output_tokens` are 1,487, 349, 3,834, 12,990 and 1,419. Tokens are labelled "main-loop".
- **Blocker: the AI books' routine sessions cannot be read.** `get_session` and `list_events` on both 14 Oct fire-log
  sessions (`cse_01KAro...` and the `session_` form) return "not found"; `list_sessions` says trigger-fired runs are
  not listed. So today no book usage can be captured; the meter counts them as "not captured" (2 for October).
- **"The plan's measured session minutes" cannot be measured as a plan capacity.** A session's `rate_limit_info` says
  only `status: allowed`, the window type (`five_hour`) and its reset time; no minutes, no share used.

## Claims

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| F8.1 | Allocation sums exactly to the plan cost (paise, largest remainder) | `fno/budget/allocation.py:39`, `:49` | `test_allocation.py:18` (5 costs incl. 1000.01, 0.02), `:24` hand-computed | strong evidence (tests; mutation "no remainder" fails 5 tests) |
| F8.2 | Allocated cost and cash spend separate everywhere written | `fno/budget/report.py:32`, `:45`; `allocation.py:12` label | `test_meter.py:35` | some evidence (this story writes only the meter and signal; C1 ledger, scoreboards and dashboard are out of scope and not changed) |
| F8.3 | No plan cost: flagged, every part unknown, never zero | `allocation.py:42`, `:26` | `test_allocation.py:35`, `test_meter.py:45` | strong evidence (mutation to 0.0 caught) |
| F8.4 | Usage only from session figures, per IST day; tokens blank when any turn lacks them; no text kept | `fno/budget/usage_export.py:84`, `:94`, `:101` | `test_usage_export.py:16`, `:29`, `:54`, `:72` (the orchestrator's 5 real 15 Oct turns: 3.93 minutes, 20,079 output tokens, by hand 235,550 ms / 60,000) | strong evidence |
| F8.5 | Incomplete export (no page with `has_more` false) refused | `usage_export.py:68-71` | `test_usage_export.py:36`, `test_budget_cli.py:26` | strong evidence |
| F8.6 | Written once per (session, day); only complete IST days | `fno/budget/usage_ledger.py:58` | `test_usage_ledger.py:28`, `:34` | strong evidence (both mutations caught) |
| F8.7 | Fired book sessions with no usage row are counted | `fno/budget/capture_coverage.py:33` | `test_meter.py:51` | strong evidence for the count; **reasoning only** for the `cse_X` = `session_X` match (`capture_coverage.py:15`), never seen to resolve |
| BG1.1 | Every 8.1 item; cash spend apart; "not recorded" never zero | `fno/budget/items.py:40`, `:65`; `report.py:32` | `test_items_and_cap.py:23`, `test_meter.py:35` | strong evidence |
| BG1.2 | Levels ok / alert at 80% / stop at 100% / unknown | `fno/budget/cap.py:54` | `test_items_and_cap.py:32` (39.95/40/49.99/50 of a 50-minute cap), `:38` | strong evidence (`>=` to `>` mutations caught) |
| BG1.3 | Basis: 50% of all measured minutes, or of the owner's figure; named with its limit | `cap.py:43`, `:12-16`; `config.yaml` `budget` | `test_items_and_cap.py:42`, `:50` | strong evidence for the code; the basis itself is an interpretation the owner must confirm (below) |
| BG1.4 | Signal data with stop order and "code jobs keep running"; dry-run sends nothing | `fno/budget/signal.py:42`, `:66`; `fno/alerts/dry_run.py:15`; `wiring.py:35` | `test_signal.py:22`, `:31` (network blocked), `:41` | strong evidence |
| BG1.5 | New cost without a cited owner decision flagged | `items.py:49` | `test_items_and_cap.py:55` | strong evidence |
| BG1.6 | 31 May 2027 projected with its dependency; days left; tests "not computable yet" | `fno/budget/stop_rule_tracker.py:52`, `:60`, `:72`; `report.py:79` | `test_stop_rule_tracker.py:15`, `:21`, `:29`, `:33`; `test_meter.py:63` | strong evidence |
| BG1.7 | Missing captures shown; % then "not a bound" | `report.py:17`, `:75` | `test_meter.py:51` | strong evidence |

Planted mutations (13, one per claim area, each restored): all caught by `tests/budget` (1 to 8 failures each).

## Real output on the repository today (`python -m fno budget meter`, `stop-rule`)

```
Omenix F&O budget meter 2026-10 (design v2 section 8.1)
  Claude subscription: cash spend not recorded; cap: AI minutes cap for books and roles (below)
    2026-10: no Claude plan cost recorded; allocation unknown
  ... (five more items, each "cash spend not recorded")
  measured books_and_roles: 0.00 minutes, 0 session(s), output tokens not available
  AI cap: books and roles 0.00 of 0.00 minutes = unknown; level unknown
    2 fired AI book session(s) have no usage row: the % above is not a bound in either direction
Omenix F&O stop-rule tracker (design v2 section 8.2)
  review date: 31 May 2027 (projected: depends on protocol v4 (story G6) freezing in November 2026; ...); 228 days
    the NSE calendar has no 2027 rows, so the last weekday is used until NSE's 2027 circular is added
  Test A: not computable yet (missing: G6, G8, A16)   Test B: not computable yet (missing: R1, R3)
```

No usage row is committed: every visible session started on 15 Oct IST, which is not a complete day yet.

## Known limits (said plainly)

1. The books' own usage cannot be captured yet (blocker above). The cap % is therefore meaningless for books today.
2. The default cap basis moves with development work (quiet development raises the books' share). It is the literal,
   measurable reading of the decision; it is not the plan's capacity, which no available data gives.
3. Python cannot call the session tools. A Claude session must save the export and run `record-usage`; no routine
   does that yet (no scheduling in scope).
4. Main-loop tokens undercount side calls; background subagents' work may not be in the parent's `result` events
   (not tested).
5. The stop-rule inputs have no paths yet (their stories define them), so they cannot turn "present" automatically
   until G6, G8, A16, R1 and R3 add a path to `INPUTS`.
6. A review-date move needs the owner's written decision; the tracker has no override, only `v4_freeze_date`.

## Owner choices (not decided by the builder)

1. How the books' usage is read: (a) the routine reads its own session at its end (if routine sessions have the tools;
   test on the next fire), or (b) the owner records the books' minutes monthly from claude.ai. Recommendation (a) first,
   reasoning only.
2. Cap basis: keep "50% of all measured minutes" or state a monthly plan-minutes figure. Recommendation: state one
   after two months of measured totals, reasoning only.
3. Record the plan's monthly fee in `accounting/operating_costs.csv` (item `Claude subscription`, category `ai`).

## What the judge should test hardest

- Recompute an allocation by hand from two CSV files with uneven minutes; plant a paisa rounding case.
- Feed a real `get_session` + `list_events` export of a finished session (and one with a missing page).
- Whether `cse_<id>` and `session_<id>` really name the same session (F8.7's assumption).
- That no code path can post to Slack (`wiring.py:35` returns only the dry-run sender).
- The review-date month arithmetic across a year end and a leap February (`test_stop_rule_tracker.py:29`).
