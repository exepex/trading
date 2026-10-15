# Response 104: F8 (minimal) AI usage and cost, and BG1 budget meter and stop-rule tracker

Builder claims for the judge. Lane 1 (new stories; touches accounting records and the owner's budget rule). Branch
`story/f8-bg1-budget`. Story texts: `docs/stories/F-ai-layer.md` ("F8 minimal", original F8 kept above it) and
`docs/stories/BG-budget.md` (BG1). Nothing is scheduled, nothing is posted to Slack, no order code is touched.

**Revision 2.** The first push (`eddd035`, already sent to judge B) predates the owner's four quality steps. This
revision adds them: a gap list, two independent code reviews (16 findings: 4 blocking, all fixed), a mutation per
claim (35, all caught), and real-figure output. **Judge the newer commit, not `eddd035`:** the export format, the
ledger's duplicate rule, the cap's boundaries and its "unknown" rules all changed.

## Facts checked before building (15 Oct 2026, strong evidence: read with the session tools)

- `list_events(kinds=["result"])` gives, for each finished turn:
  - `duration_ms` (wall time),
  - `usage` (main-loop tokens),
  - `num_turns`,
  - and `modelUsage`/`total_cost_usd` running totals at **API list price** ("costBasis": "list").

  List price is not what the owner pays on a plan, so it is never used.
- `duration_api_ms` can exceed `duration_ms`: one orchestrator turn took 8,206 ms of wall time but 33,957 ms of model
  time, from parallel calls. Minutes here are wall minutes.
- Per-turn `usage` leaves out side calls. Across five turns:

  | | Turn 1 | Turn 2 | Turn 3 | Turn 4 | Turn 5 |
  |---|---|---|---|---|---|
  | `modelUsage` output tokens, growth per turn | 2,091 | 359 | 3,851 | 12,996 | 1,419 |
  | `usage.output_tokens` | 1,487 | 349 | 3,834 | 12,990 | 1,419 |

  The tokens recorded are labelled "main-loop" for this reason.
- **Blocker: the AI books' routine sessions cannot be read.**
  - `get_session` and `list_events` on both 14 Oct fire-log sessions (`cse_01KAro...`, and the same id written
    `session_...`) return "not found".
  - `list_sessions` says trigger-fired runs are not listed.
- **The plan's capacity in minutes cannot be measured.** `rate_limit_info` holds only:
  - `status: allowed`,
  - the window type (`five_hour`),
  - the reset time.

  There are no minutes and no share used.

## Gap list: every requirement mapped (owner step 1)

| Requirement (source) | Where | Status |
|---|---|---|
| 8.1 Claude subscription: books' and roles' allocated share shown monthly | F8.1-F8.3, meter | covered |
| 8.1 AI routine use capped at half the plan's measured session minutes | BG1.2, BG1.3 | covered; the basis is an interpretation (owner choice 2) |
| 8.1 GitHub Actions, Drive: no cap | BG1.1 (cap text) | covered |
| 8.1 GitHub Actions, Drive: storage reported monthly | none | **out**: needs a Drive size call; no source wired yet. "not recorded" is shown instead |
| 8.1 Azure PostgreSQL, Groww API: owner records, reported monthly | BG1.1 | covered (owner-recorded rows) |
| 8.1 Hosting for the recorder and monitor (owner chose a Claude routine on 15 Oct, "cost measured by F8") | purpose `data_routines`, BG1.1 | covered, **added in revision 2** (the gap list found it); same capture blocker as the books |
| 8.1 Paid data: owner approves each | BG1.5 | covered |
| 8.1 Any new recurring cash cost needs the owner's written yes | BG1.5 | covered (cited `DESK_DECISIONS` row) |
| 8.1 SYSTEM alert at 80% | BG1.4 | covered as text and data; sending is dry run (a later routine wires Slack) |
| 8.1 At 100%, AI roles stop in 7.6's order; code jobs keep running | BG1.4 | covered as a signal; acting on it is **out**: no AI role exists yet to stop |
| 8.2 Review date: last session of the 6th full month after v4's freeze | BG1.6 | covered (projected; calendar fallback labelled) |
| 8.2 The date moves only by a written owner decision | config `v4_freeze_date` | partial: there is no override key, by design. The judge should check that no code moves the date |
| 8.2 Judgeable questions V6, V1 (only if A16), V2; the 20-day questions are reported, not judged | BG1.6 inputs | inputs listed. The 20-day report is **out** (G8's scoring report) |
| 8.2 Honest expectation (~125 outcomes; "undecided" most likely) | none | **out**: depends on the freeze date and the 2027 calendar; tracker says "not computable yet" |
| 8.2 Test A and Test B, three results each; zero shadows gives undecided / no_economic_test | BG1.6 | status and missing inputs covered; computing the tests is **out** (G6, G8, R1, R3 not built) |
| 8.2 Stopping for cost is separate; outcomes table; "undecided" options | none | **out**: owner decisions at review time, already in `DESK_DECISIONS.md` |
| F8 design: `ai_usage.csv` columns (`date, book, role_or_bundle, session_id, model, minutes, tokens`) | F8.4, F8.6 | covered, plus `purpose`, `turns`, `tokens_basis`, `source` |
| F8 design: usage read from `get_session` and `list_events` | F8.4, F8.5 | covered through an export (Python cannot call the session tools) |
| F8 design: owner records the plan cost in `operating_costs.csv` | F8.3 | covered (item `Claude subscription`) |
| F8 design: allocation formula frozen in S1 | `FORMULA = minutes_share_v1` | **out**: S1 freezes it |
| F8 design: C1 account ledger shows the allocated cost per book | none | **out**: needs books 2 and 3 trading; the story says so |
| F8 criterion 2: separate fields in ledger, scoreboards, dashboard | F8.2 | partial: only the outputs this story writes (meter, signal) |
| BG1 (REPLAN): "the two tests computed ahead of time" | BG1.6 | partial: reported as not computable, with the missing input and story for each |
| Owner brief: tokens where available, never invented | F8.4 | covered |
| Owner brief: no recorded plan cost shows unknown, never zero | F8.3 | covered |
| Owner brief: how "measured minutes" is measured must be explicit | BG1 story text, `cap.py:12-25` | covered; not measurable as capacity (owner choice 2) |
| Owner brief: CLI prints the meter; no scheduling | `fno/budget/cli.py:17` | covered |

## Claims (code at the revision-2 commit)

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| F8.1 | Allocation sums exactly to the plan cost (paise, largest remainder); a negative cost is refused | `fno/budget/allocation.py:39`, `:51` | `test_allocation.py:18`, `:24`, `:46` | strong evidence. Reviewer: 20,000 random months, all exact to the paisa |
| F8.2 | Allocated cost apart from cash spend, labelled "allocated, not a bill" | `report.py:31`, `:44`; `allocation.py:12` | `test_meter.py:42` | some evidence: only this story's outputs (gap list) |
| F8.3 | No plan cost: flagged, every part unknown, never zero | `allocation.py:39-46`, `:26` | `test_allocation.py:35`, `test_meter.py:53` | strong evidence |
| F8.4 | Figures from the session only, by IST day; tokens blank when unknown; no text kept; bad durations and times without a zone refused | `usage_export.py:116`, `:122`, `:132`, `:139`, `:143` | `test_usage_export.py:16`, `:29`, `:71`, `:78`, `:90`, `:95`, `:113` (the orchestrator's 5 real turns: 3.93 min, 20,079 tokens) | strong evidence |
| F8.5 | An export that could under-count is refused: a page missing (older or middle), out of order, no uuid, no result events | `usage_export.py:82`, `:98` | `test_usage_export.py:36`, `:49`, `:56`, `:85`, `:119`; `test_budget_cli.py:26` | strong evidence |
| F8.6 | Written once; `session_<id>` form only; only days before both today and the capture day; damaged ledger refused; file replaced whole | `usage_ledger.py:72`, `:92`, `:103`; `cli.py:76` | `test_usage_ledger.py:28`, `:34`, `:64`, `:82`, `:89`, `:100` | strong evidence |
| F8.7 | Fired book sessions before today with no usage row are counted; a fired session without a link counts too; an odd fire log is refused, naming the file | `capture_coverage.py:20`, `:31`, `:42` | `test_meter.py:59`, `:70` | strong evidence for the count. **Reasoning only** that `cse_X` is the same session as `session_X` (`usage_ledger.py:29`): never seen to resolve |
| BG1.1 | Every 8.1 item, cash spend apart, "not recorded" never zero; data-routine minutes for recorder hosting | `items.py:40`, `:65`; `report.py:31`, `:53` | `test_items_and_cap.py:23`, `test_meter.py:89`, `test_usage_ledger.py:106` | strong evidence |
| BG1.2 | ok / alert from exactly 80% / stop from exactly 100%, compared in decimals; unknown with nothing measured | `cap.py:51`, `:74` | `test_items_and_cap.py:32`, `:38`, `:70` | strong evidence (a float-compare mutation is caught) |
| BG1.3 | Basis: 50% of all measured minutes, or of the owner's figure; no development minutes reads unknown; data-routine minutes count in the basis, never against the cap | `cap.py:51-71`; `config.yaml` `budget` | `test_items_and_cap.py:44`, `:52`, `:76`, `:90` | strong evidence for the code; the basis is the owner's choice |
| BG1.4 | Signal data (level, %, note, stop flag, 7.6 order, code jobs keep running); dry run only; text floored, never 100% below stop | `signal.py:33`, `:44`, `:69`; `wiring.py:35`; `fno/alerts/dry_run.py:15` | `test_signal.py:22`, `:31`, `:41`, `:46`, `:52` | strong evidence |
| BG1.5 | A new cost without a cited owner decision is flagged | `items.py:49` | `test_items_and_cap.py:57` | strong evidence |
| BG1.6 | 31 May 2027, projected, with its dependency; days left; both tests "not computable yet" | `stop_rule_tracker.py:52`, `:60`, `:72`; `report.py:81` | `test_stop_rule_tracker.py:15`, `:21`, `:29`, `:33`; `test_meter.py:81` | strong evidence (the reviewer also checked year ends) |
| BG1.7 | Missing captures turn ok into unknown and mark alert or stop "at least this level"; shown on the meter and in the signal | `cap.py:59-67`; `report.py:69` | `test_items_and_cap.py:38`, `:81`; `test_meter.py:59` | strong evidence. **Reasoning** behind "only raise": on either basis, adding a missed book session to books and total cannot lower books/total while books ≤ total |

## Self-review by two independent agents (owner step 2)

| # | Finding (reviewer) | Severity | Check and response |
|---|---|---|---|
| 1 | A day still running when the export was taken is frozen short (silent) | blocking | **accepted**, reproduced: an export with 1 turn of 15 Oct, recorded 16 Oct, froze 1.00 minute. Fixed: `captured_at` is required; only days before the capture day are recorded (`cli.py:76`, test `test_usage_ledger.py:64`) |
| 2 | One session recorded twice under differently written ids (silent) | blocking | **accepted**. Fixed: only `session_<letters and digits>` is accepted (`cse_`, spaces and links are refused), and duplicates are checked on the id without its prefix (`usage_ledger.py:26`, `:72`; test `:82`) |
| 3 | A missing middle page is not detected (silent) | blocking | **accepted**, reproduced. Fixed: each page records its `before_id`, which must equal the newer page's `first_id`, and only the last page may have `has_more` false (`usage_export.py:82`; tests `:49`, `:56`) |
| 4 | 80% and 100% boundaries fail on floating-point error (correctness) | blocking | **accepted**, reproduced: 0.68 of 1.70 read 79.999...% `ok`. Fixed: decimal comparison (`cap.py:74`; test `:70`) |
| 5 | Boolean or negative durations accepted (both reviewers) | minor | **accepted**. Refused (`usage_export.py:139`; test `:71`) |
| 6 | Unknown export shape records nothing and exits 0 | minor | **accepted**. Refused, exit 1 (`usage_export.py:98`; test `:85`) |
| 7 | An event without a uuid on two pages counts twice | minor | **accepted** in a stricter form: every result event needs a uuid, or the export is refused. All real events seen had one |
| 8 | The cap reads `ok` while sessions are not captured | minor | **accepted**. `ok` becomes `unknown`; `alert` and `stop` are marked "at least" (`cap.py:59-67`; test `:81`) |
| 9 | A damaged ledger is read as fewer rows; the header can race | minor | **accepted** for the damage: refused with its line number, and the file is replaced whole through a temp file (`usage_ledger.py:92`, `:103`). **Not fixed:** a lock for two runs at once. No routine runs this yet; it is noted in the docstring. Partly checked: no parallel run was tried |
| 10 | A purpose with no rows prints "0.00 minutes" | minor | **accepted**. Prints "no rows recorded (unknown, not zero)" (`report.py:53`) |
| 11 | A negative plan cost breaks the exact sum | minor | **accepted**. Refused (`allocation.py:41`; test `:46`) |
| 12 | Odd fire-log shapes crash with raw tracebacks | minor | **accepted**. Refused with the file's name (`capture_coverage.py:31`; test `test_meter.py:70`) |
| 13 | A created_at without a zone is read in the container's local time | minor | **accepted**. Refused (`usage_export.py:122`; test `:78`) |
| 14 | Alert text says 100% while the level is alert | minor | **accepted**, reproduced (99.96%). Floored to one decimal (`signal.py:33`; test `:52`) |
| 15 | No development rows on the measured basis reads `stop` (books counted as all the use) | design | **accepted**. Reads `unknown` with that reason (`cap.py:64`; test `:76`) |
| 16 | Today's fired sessions are always "missing" | minor | **accepted**. Only days before today are counted (`capture_coverage.py:20`) |

Found by my own run of the real meter after these fixes: a month with nothing measured printed "at least this level".
Fixed: `cap.py:59-62`, test `test_items_and_cap.py:38`.

Reviewer checks that came back clean:
- no reply text reaches the ledger or the signal;
- no path reaches the Slack sender;
- no exception is swallowed;
- the IST day boundary (18:29:59Z vs 18:30:00Z) is right;
- the review date across a year end;
- allocation exactness over 20,000 random months.

## Mutation per claim (owner step 3): 35 planted, 35 caught

Each mutation was applied alone to the revision-2 code, `tests/budget` was run, and the file was restored. Below,
"n of 82" means n of the 82 tests in `tests/budget` failed.

| Claim | What was broken | Tests failed |
|---|---|---|
| F8.1 | Remainder paise dropped; negative-cost refusal removed | 5 of 82; 1 of 82 |
| F8.2 | Label changed | 1 |
| F8.3 | Unknown parts shown as 0.0 | 1 |
| F8.4 | Tokens dropped | 3 |
| F8.4 | Unknown tokens shown as `{}` | 1 |
| F8.4 | Bad durations accepted | 2 |
| F8.4 | Missing zone accepted | 1 |
| F8.5 | Last-page check removed | 2 |
| F8.5 | Chain check removed | 1 |
| F8.5 | Unknown export shape accepted | 1 |
| F8.6 | `>=` turned into `>` (today recorded) | 2 |
| F8.6 | Write-once check removed | 2 |
| F8.6 | Id-form check removed | 4 |
| F8.6 | Damaged-ledger check removed | 1 |
| F8.6 | Capture day ignored | 1 |
| F8.7 | Today counted | 1 |
| F8.7 | Sessions without a link dropped | 1 |
| BG1.1 | Items cut | 2 |
| BG1.1 | Missing amount shown as 0 | 3 |
| BG1.2 | Stop boundary `>` | 3 |
| BG1.2 | Alert boundary `>` | 3 |
| BG1.2 | Float compare | 1 |
| BG1.3 | Owner figure ignored | 3 |
| BG1.3 | Basis = books only | 15 |
| BG1.3 | No-development rule removed | 1 |
| BG1.4 | Stop flag always false | 1 |
| BG1.4 | Slack sender wired | 1 |
| BG1.4 | Text not floored | 1 |
| BG1.5 | Citation ignored | 1 |
| BG1.6 | 7 months instead of 6 | 5 |
| BG1.6 | "projected" label dropped | 2 |
| BG1.6 | Missing inputs hidden | 3 |
| BG1.7 | Missing captures ignored | 1 |
| BG1.7 | Note not printed | 1 |

## Real output (owner step 4)

**The repository today** (`python -m fno budget meter --month 2026-10`, abridged):

```
  Claude subscription: cash spend not recorded; cap: AI minutes cap for books and roles (below)
    2026-10: no Claude plan cost recorded; allocation unknown
  ... (five more items, each "cash spend not recorded")
  measured books_and_roles: no rows recorded (unknown, not zero)
  measured development: no rows recorded (unknown, not zero)
  measured data_routines: no rows recorded (unknown, not zero)
  AI cap: books and roles 0.00 of 0.00 minutes = unknown; level unknown
    unknown: no minutes to measure against; 2 fired AI book session(s) not captured
```

**With real figures:** the orchestrator's five real 15 Oct turns, recorded as development in a temporary copy, with
the real 14 Oct fire log and no plan fee (none is recorded; no fee was invented):

```
2026-10-15 session_01VG1RqxLFUVdvvPuMRYZtDH: recorded 3.93 minutes, 5 turns
  measured books_and_roles: no rows recorded (unknown, not zero)
  measured development: 3.93 minutes, 1 session(s), output tokens 20,079
  AI cap: books and roles 0.00 of 1.97 minutes = 0.0%; level unknown
    unknown: 2 fired AI book session(s) not captured, so the true share may be above the alert level
```

**The stop-rule tracker:**

```
  review date: 31 May 2027 (projected: depends on protocol v4 (story G6) freezing in November 2026; each month
  later moves it a month); 228 days from 2026-10-15
    the NSE calendar has no 2027 rows, so the last weekday is used until NSE's 2027 circular is added
  Test A: not computable yet (missing: G6, G8, A16)   Test B: not computable yet (missing: R1, R3)
```

No usage row is committed: every visible session started on 15 Oct IST, which is not complete yet.

## Known limits (said plainly)

1. The books' usage cannot be captured yet (blocker above), and neither can the data routines'. So the books' cap
   level reads "unknown" today, and will keep doing so until owner choice 1 is settled.
2. The default basis moves with development work, and development sessions that are never recorded lower the books'
   share without being tracked. Both points are printed on every meter.
3. Python cannot call the session tools. A Claude session must save the export and run `record-usage`. No routine
   does that yet; scheduling is out of scope.
4. Main-loop tokens undercount side calls. Background subagents' work may be missing from the parent's events (not
   tested).
5. The stop-rule inputs have no paths yet. Each producing story adds its path to `INPUTS`.
6. There is no lock for two `record-usage` runs at once.

## Owner choices (not decided by the builder)

1. **How the books' (and data routines') usage is read:**
   - (a) each routine reads its own session at its end, if routine sessions have the tools (test on the next fire);
   - (b) the owner records the minutes monthly from claude.ai.

   Recommendation: (a) first (reasoning only).
2. **Cap basis:** keep "50% of all measured minutes", or state a monthly plan-minutes figure. Recommendation: a
   figure, after two months of measured totals (reasoning only).
3. **Plan fee:** record the plan's monthly fee in `accounting/operating_costs.csv` (item `Claude subscription`,
   category `ai`).

## What the judge should test hardest

- Recompute an allocation by hand from two CSV files with uneven minutes.
- Save a real `get_session` + `list_events` export of a finished session, chained with `before_id`. Then drop a
  middle page and change `captured_at` to mid-day, and check both are handled.
- Whether `cse_<id>` and `session_<id>` really name the same session.
- That no path can post to Slack (`wiring.py:35`).
- The "only raise" argument behind BG1.7, and the decimal boundaries.
