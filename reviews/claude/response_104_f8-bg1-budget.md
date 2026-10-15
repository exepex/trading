# Response 104: F8 (minimal) AI usage and cost, and BG1 budget meter and stop-rule tracker

Builder claims for the judge. Lane 1 (new stories; touches accounting records and the owner's budget rule). Branch
`story/f8-bg1-budget`. Story texts: `docs/stories/F-ai-layer.md` ("F8 minimal"; the original F8 is kept above it and
now marked as "F8 part 2, later") and `docs/stories/BG-budget.md` (BG1). Nothing is scheduled, nothing is posted to
Slack, no order code is touched.

**Revision 3, the commit sent with this file.** It answers judge 104 (FAIL on `eddd035`) item by item, adds the
owner's answers of 15 Oct ("5 A", INR 20,000, "7 A"), and fixes a third independent review. Revision 2 (`8a3e562`)
was never sent to the judge.

## Revision 4: answer to judge 104 addendum 1 (FAIL on `553ab47`, data routines only)

| Item | Done | Where (code; tests) |
|---|---|---|
| **MF3, data routines.** Uncaptured data-routine minutes sit in the measured denominator, so 200 missing minutes turned a true 30% `ok` into a 90% `alert` | **Accepted, fixed** with the orchestrator's option (a), response 113. On the measured basis the level is `unknown`, naming the reason, until every expected run is recorded. "Expected" means each routine named in `budget.data_routines` (today: the 3 pm quote recorder) once on every NSE session day of the month before today (`SessionCalendar`, A7). A run counts only as a `data_routines` row for that routine on that day: its own self-timed record, through `record-usage --self-timed --purpose data_routines --role "3 pm quote recorder"`. The owner's-figure basis is unaffected. The allocation also warns "book shares overstated". **Not done, the owner's step:** adding the timing record to the recorder's prompt (same lines as the books' proposal below). Until then October reads "0 of 10 expected run(s) recorded" and the level stays `unknown` | `routine_coverage.py`; `cap.py` `_gaps`; `wiring.py`; `test_items_and_cap.py` (the judge's 45/55/200 probe: `unknown`, then the truth of 30% `ok` once captured, and the owner basis stays `ok`); `test_meter.py` (missing runs, recorded runs complete, other purposes don't count) |
| **Minor: who adds the plan cost each month** | **Fixed:** one config value, `budget.plan_cost` (Rs 20,000 from 2026-10), cites the owner's row, and that row must exist. The meter applies it to every month from October until a newer decision changes the value; nobody adds rows by hand. A recorded payment row is that month's cash spend, and a payment that differs from the decided figure is flagged. October's recorded row stays. Months before October: unknown | `plan_cost.py`; `wiring.py`; `test_plan_cost.py`; `test_meter.py` (November shows "Rs 20,000.00 (decided monthly fee ...)" and allocates it; September is unknown) |
| "Two months = Nov and Dec" | The config comment now says it is the orchestrator's decision (response 113), which the owner may change | `config.yaml` |

**Mutations for revision 4:** 15 more planted, all caught:
- the routine gap ignored, or wrongly applied to the owner's figure;
- coverage always reading complete;
- today counted as an expected run;
- rows of any purpose counted as runs (the one survivor, now caught by a new test);
- the routine gap not wired;
- the decided cost applied before its month, or its citation not checked;
- a payment difference not flagged;
- the recorded payment ignored;
- the decided cost not allocated;
- each warning dropped;
- the development gap ignored;
- the owner basis.

In total: 72 effective mutations, 71 caught. The 72nd is the equivalent anchored-citation mutation.

## Answer to judge 104, item by item

| Judge 104 item | Done | Where (code; tests) |
|---|---|---|
| **MF1** A real export was refused: real pages omit `has_more` on the last page | **Accepted, fixed.** An absent `has_more` means "this is the end". Only `true` means "more pages"; any value other than true, false or absent is refused. A page following one without `has_more: true` is refused | `usage_export.py:61-77`; `test_usage_export.py:110` (the real envelope: last page with no `has_more` and no `data`), `:97`, `:56` |
| **MF2** A missing middle page was accepted | **Accepted, fixed** (already in revision 2). Each page stores the `before_id` it was read with, which must equal the newer page's `first_id`; the first page has none | `usage_export.py:61`; `test_usage_export.py:49`, `:36` |
| **MF3** Development sessions are never captured, so the levels and allocation shares were biased | **Accepted, fixed.** New roster `accounting/ai_session_roster.csv`, from a chained `list_sessions(mine=true)` export (ids and times only). On the measured basis the level is `unknown` until development is fully captured: the roster must have been read after the last complete day, and every development session active in the month must have a reading that holds every day up to its last active day. With the owner's figure set, only book coverage matters. Missing book sessions turn `ok` into `unknown` and mark `alert`/`stop` "at least this level". **One part pushed back, with reasoning:** the judge asked for `unknown` whenever book coverage is incomplete. Adding the missed book minutes can only raise books/total (books ≤ total) or books/figure, so an `alert` or `stop` reading is a proven floor. Hiding it would hide a real stop. The allocation warns "book shares overstated" or "understated" | `session_roster.py:32`, `:98`, `:120`; `cap.py:84`; `allocation.py:65`; `test_session_roster.py:27-93`, `test_items_and_cap.py:68`, `:77`, `test_meter.py:100` |
| **MF4** Rounding differs from S1's decided rule | **Accepted, fixed.** Each share is rounded down to the paisa and all the remaining paise go to the largest share (most minutes; on a tie, the first by name). Minutes are summed as decimals, so float error never moves a paisa | `allocation.py:58`; `test_allocation.py:23` (Rs 1,700 over 3 equal shares: 566.68 / 566.66 / 566.66; a 10:11 split gets its 1 paisa on the larger share) |
| **MF5** Gap list | **Accepted.** Full list below. 8.1's Drive storage line is now printed as a stated gap. The 6.5 alert "a stop-rule date reached" is built (dry run). The original F8 is marked "F8 part 2, later", naming S2's `AiCostAllocation` port. S1's label "development, not a book cost" is used | `items.py:29`; `stop_rule_tracker.py` (`review_reached`); `report.py` (development label); `docs/stories/F-ai-layer.md` original F8 status |
| **SF1** Tests to pin: dry-run wiring, `v4_freeze_date` read, weekend fallback, the token-known check | **Accepted, all added** | `test_signal.py:46`; `test_stop_rule_tracker.py:52`, `:46` (a January 2027 freeze gives Fri 30 Jul 2027); `test_meter.py:108` |
| **SF2** Any text with "DESK_DECISIONS" passed | **Accepted, fixed.** The whole source must read `DESK_DECISIONS <date>: <bold title>`, and that (date, title) pair must be a row of the decisions table. Negative amounts are flagged too. **Stated limit:** whether the cited row approves this very cost is left to the reader | `items.py:23-24`, `:55`, `:70`; `test_items_and_cap.py:115` (a fake title, a wrong date, a "not in ..." prefix and a partial title are all flagged) |
| **SF3** Self-review by independent agents | **Done three times:** 2 reviewers on revision 1 (16 findings), 1 on revision 3 (8 findings) | tables below |
| Minor 1: 99.6% printed as 100% | **Fixed:** floored to one decimal in the meter and in the alert | `cap.py:105`; `test_signal.py:58`, `test_items_and_cap.py:111` |
| Minor 2: a bad `--month` gave a traceback | **Fixed:** every refusal is one "refused:" line with exit 1 | `cli.py`; `test_budget_cli.py:40`, `:59` |
| Minor 3: config numbers not checked | **Fixed:** 0 < share ≤ 100 and 0 < alert ≤ stop, checked when read | `cap.py:43`; `test_items_and_cap.py:101` |
| Minor 4: an export inside the repository was accepted | **Fixed:** refused, including symlinks and `../` paths. **Limit:** a hard link cannot be told apart cheaply | `cli.py` `_outside_repository`; `test_budget_cli.py:40` |
| Minor 5: the dry-run sender beside `NoAlertSender` | **Explained** in its docstring: a dry run is the intended outcome and keeps the texts it would have sent | `fno/alerts/dry_run.py:1-3` |
| Minor 6: a turn crossing midnight IST | **Stated:** a turn counts on the day its result was written; a self-timed run on the day it ended | `docs/stories/F-ai-layer.md` criterion 4; `test_self_timed.py:35` |
| Minor 7: special Saturday sessions | **Stated:** any NSE session counts, a special weekend session included (design 8.2 does not say) | `stop_rule_tracker.py:1-6` |
| Owner "6": INR 20,000 a month | **Recorded** for October 2026: `accounting/operating_costs.csv`, source `DESK_DECISIONS 15 Oct 2026: Claude plan cost: INR 20,000 a month` (the row exists) | `test_items_and_cap.py:130` |
| Owner "7 A" plus judge point (a): two months, then a fixed figure, with a dated end | **Done:** `budget.measured_basis_until: "2026-12"`. After that month, if no figure is set, the level is `unknown` and the meter says "the owner's fixed monthly figure is owed". **Owner to confirm:** "two months" read as November and December 2026, October being partial | `config.yaml` `budget`; `cap.py:84`; `test_items_and_cap.py:86` |
| Owner "5 A": the routine records its own usage at the end of each run | **Built, as far as is possible today:** `SelfTimedUsageReader`, behind the same interface (see the finding below) | `self_timed.py`; `test_self_timed.py` |

### Finding on "5 A": it cannot work through the session tools

A `result` event is written when a turn ends, and a fired routine runs one turn. So at its end, a routine reading its
own session finds no usage for the run in progress. (Reasoning only, from the event model; the first live run will
confirm or refute it.)

What a routine can do is time itself:
- at its start, note the time and its session id (`get_session` with no id);
- at its end, write `{"session_id", "model", "started_at", "ended_at"}`;
- record it with `python -m fno budget record-usage --self-timed`.

Tokens are then unknown. The reader refuses:
- a run ending after today;
- a run longer than 24 hours;
- a run that ends before it starts;
- a time without a zone.

**Not done here, and why:** the books' prompt has to change to write this record. A prompt change is a new registered
book version (F1/G5 versions, transcript audits), so it is the orchestrator's call. The lines to add, as a proposal:

> At the very start, run `date -u +%Y-%m-%dT%H:%M:%SZ` and call `get_session` with no id. At the very end, write
> `{"session_id": <id>, "model": <configured_model>, "started_at": <start>, "ended_at": <now>}` to the usage path
> named by the story that wires it, and commit only that file.

**One existing test changed (lane 1, said openly):** `tests/accounting/test_ledgers.py:83` pinned the cost file as
empty. The owner's INR 20,000 row changes that, so the test now pins that exact row and checks that C1's ledgers
reconcile with it. It is no looser. Only `accounting/operating_costs.csv` changed; S2's scoreboard reads the per-book
`journal/<book>/operating_costs.csv`, which is untouched.

## Independent review 3 (revision-3 code): 8 findings

| # | Finding | Severity | Check and response |
|---|---|---|---|
| B1 | A real development gap read as "complete": a reading taken on a session's last active day was counted as covering that day | blocking | **Accepted**, reproduced. The ledger now stores each row's `complete_before` day. A session is covered only when a reading holds every day up to its last active day (or up to the last complete day) (`session_roster.py:120`; `test_session_roster.py:77`) |
| B2 | Citations: the match was not anchored, and any bold title passed for any item or date | blocking (reviewer) | **Accepted**: anchored, and the date and title must match a real row (SF2 above). Tying a row to a particular item stays a stated limit |
| M1 | Tracebacks: missing file, export not a JSON object, event without created_at, a zone-less roster time, `nan` minutes | minor | **Accepted**: each is refused in one line (`usage_reader.py:40` `shaped`, `session_roster.py:62`, `usage_ledger.py:106`, CLI catches `OSError`); tests `test_usage_export.py:86`, `test_session_roster.py:51`, `test_usage_ledger.py:103`, `test_budget_cli.py:59` |
| M2 | An event without `result` was skipped silently | minor | **Accepted**: refused, never skipped (`test_usage_export.py:86`) |
| M3 | `has_more: "true"` (a string) was taken as the end | minor | **Accepted**: refused (`test_usage_export.py:97`) |
| M4 | A self-timed run in the future, or a month long, was recorded | minor | **Accepted**: both refused (`self_timed.py:17-18`; `test_self_timed.py:40`, `:49`) |
| M5 | The roster's `limit` is self-reported | minor | **Partly accepted:** a limit outside 1-100 (the tool's maximum) is refused (`test_session_roster.py:46`). A false limit inside that range cannot be detected: a stated limit |
| M6 | Hard links into the repository | minor | **Stated limit**, not fixed (the cost is not worth it) |

Checked sound by the reviewer:
- the export page chain;
- the roster page chain;
- the order of the rules in `cap._gaps`;
- 20,000 random allocations, exact to the paisa;
- the symlink and `../` refusals.

## Reviews 1 and 2 (revision 1): 16 findings, all fixed but one

These were fixed in revision 2 and are kept:
- a day still running at export time was frozen short;
- one session could get two ids;
- a missing middle page went unnoticed;
- float rounding at the 80% and 100% boundaries;
- bad durations;
- unknown shapes;
- `ok` despite missing captures;
- a damaged ledger;
- "0.00" shown for unrecorded rows;
- negative plan costs;
- odd fire logs;
- times without a zone;
- the alert-text rounding;
- today's fires counted as missing.

**Not fixed:** a lock for two `record-usage` runs at the same time. Nothing runs the command yet; this is stated in
the docstring.

## Gap list: every requirement mapped

| Requirement (source) | Status |
|---|---|
| 8.1 Claude subscription: the books' and roles' allocated share each month | covered: F8.1-F8.3, meter |
| 8.1 AI use capped at half the plan's measured minutes; owner "7 A" | covered: BG1.2, BG1.3, `measured_basis_until` |
| 8.1 GitHub Actions and Drive: no cap | covered: BG1.1 |
| 8.1 Drive storage reported monthly | **out, stated on the meter**: no Drive size source is wired (later; needs a Drive size call) |
| 8.1 Azure, Groww API, paid data: owner records | covered: BG1.1, BG1.5 |
| 8.1 Recorder hosting: a Claude routine, "cost measured by F8" (owner, 15 Oct) | covered: purpose `data_routines`, and its coverage is checked against the NSE calendar (revision 4). The routine's timing record is the owner's prompt step |
| 8.1 A new recurring cash cost needs a written yes | covered: BG1.5 (the cited row must exist) |
| 8.1 / 6.5 SYSTEM alert at 80% and 100% | covered as data plus a dry run; the Slack sending is wired by a later routine |
| 6.5 SYSTEM alert "a stop-rule date reached" | covered: `review_reached`, dry run, from the date on |
| 7.6 Stop order; code jobs keep running | covered in the signal. Acting on it is **out**: no AI role exists yet |
| 8.2 Review date: projected while v4 is not frozen | covered: BG1.6 |
| 8.2 The date moves only by a written owner decision | partly: there is no override key; `v4_freeze_date` is the only input |
| 8.2 Test A and Test B, three results each; zero shadows gives "undecided" | the status and missing inputs are covered. Computing them is **out** (G6, G8, R1, R3) |
| 8.2 The 20-day questions are reported, not judged; the honest-expectation numbers | **out**: G8's report, and the 2027 calendar |
| S1 `ai_cost_allocation`: formula, rounding, "development, not a book cost", unknown when no cost, no tokens | covered: F8.1-F8.3; tokens are shown but never used in the allocation |
| Original F8: per-book lines in C1, scoreboards, dashboard, S2's `AiCostAllocation` port | **F8 part 2, later** (named in the story status) |
| Owner brief: tokens never invented; no cost shows unknown; "measured minutes" made explicit; CLI; no scheduling | covered |

## Claims (code at this commit)

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| F8.1 | Exact to the paisa; the remainder to the largest share, with the tie-break; a negative cost refused | `allocation.py:46`, `:58` | `test_allocation.py:18`, `:23`, `:34`, `:56` | strong |
| F8.2 | Allocated cost apart from cash; "development, not a book cost" | `report.py`; `allocation.py:15-16` | `test_meter.py:46` | some: only this story's outputs |
| F8.3 | No cost: unknown, never zero | `allocation.py:46` | `test_allocation.py:45`, `test_meter.py:59` | strong |
| F8.4 | Only the session's own figures, per IST day; self-timed runs | `usage_export.py:97-121`; `self_timed.py:26` | `test_usage_export.py:16`, `:29`, `:71`, `:140`; `test_self_timed.py:22-49` | strong |
| F8.5 | Anything that could under-count is refused; the real envelope is accepted | `usage_export.py:61`, `:79`; `usage_reader.py:40` | `test_usage_export.py:36-122`, `:146` | strong (the envelope shape is the one judge B read) |
| F8.6 | Written once; `session_<id>` only; complete days only; `complete_before` kept; damaged or `nan` rows refused | `usage_ledger.py:75`, `:106`, `:117` | `test_usage_ledger.py:29-117` | strong |
| F8.7 | Coverage of book sessions (fire logs) and development sessions (roster) | `capture_coverage.py`; `session_roster.py:98` | `test_meter.py:65`, `:76`; `test_session_roster.py` | strong; `cse_` = `session_` proven by judge B |
| BG1.1 | Every 8.1 item; "not recorded"; storage gap stated | `items.py:29`, `:46` | `test_items_and_cap.py:28` | strong |
| BG1.2 | Decimal boundaries; floored display | `cap.py:97`, `:105` | `test_items_and_cap.py:38`, `:47`, `:111` | strong |
| BG1.3 | Measured basis until 2026-12, then the owner's figure; settings checked | `cap.py:43`, `:71`, `:84` | `test_items_and_cap.py:60`, `:86`, `:101` | strong; the 2026-12 end needs the owner's confirmation |
| BG1.4 | Signal data; dry-run wiring only | `signal.py:42`; `wiring.py` | `test_signal.py:22-58` | strong |
| BG1.5 | Cited row must exist; negatives flagged | `items.py:55`, `:70` | `test_items_and_cap.py:115`, `:130` | strong; tying a row to the item is a stated limit |
| BG1.6 | Review date; freeze date read; weekend fallback; "not computable yet"; date-reached alert | `stop_rule_tracker.py`; `wiring.py` | `test_stop_rule_tracker.py:15-63`; `test_meter.py:87` | strong |
| BG1.7 | A level only when known; warnings on the allocation | `cap.py:84`; `allocation.py:65` | `test_items_and_cap.py:53`, `:68`, `:77`; `test_meter.py:100` | strong; the "only raise" argument is reasoning, written in `cap.py`'s docstring |

## Mutations: 61 planted, one at a time, each restored

60 were caught by `tests/budget`. One more ("anchored" by switching `match` to `search`) cannot change behaviour,
because the pattern already starts with `^`; removing the `^` itself is caught. The new paths are all covered:
- the absent `has_more`;
- the chain;
- the `has_more` type;
- event shapes;
- the roster chain, end, limit and staleness;
- the needed-day rule;
- the remainder rule and its tie-break;
- the development label;
- the basis expiry;
- the settings check;
- the citation row;
- the freeze date read;
- the weekend fallback;
- the date-reached alert;
- the inside-repository refusal.

Each failed 1 to 15 tests. The script and its output are in the builder's scratchpad; the judge should re-run their
own.

## Real output on the repository at this commit (`python -m fno budget meter --month 2026-10`, abridged)

```
  Claude subscription: cash spend Rs 20,000.00; cap: AI minutes cap for books and roles (below)
    allocated, not a bill (minutes_share_v1):
      not allocated yet (no measured usage this month): Rs 20,000.00
    WARNING: 2 fired AI book session(s) not captured: book shares understated
    WARNING: development not fully captured (no session roster read since 2026-10-15T00:00:00+05:30): book shares overstated
  GitHub Actions and Drive: cash spend not recorded; cap: no cap needed (free); storage not reported yet: no Drive size source is wired (later)
  measured books_and_roles: no rows recorded (unknown, not zero)
  AI cap: books and roles 0.00 of 0.00 minutes = unknown; level unknown
    unknown: no minutes to measure against; 2 fired AI book session(s) not captured
    development capture: no session roster read since 2026-10-15T00:00:00+05:30
```

`python -m fno budget stop-rule` prints:
- "31 May 2027 (projected: depends on protocol v4 (story G6) freezing in November 2026 ...)";
- 228 days left, counted from 15 Oct;
- the 2027 weekday fallback note;
- Test A and Test B both "not computable yet", each with its missing inputs (G6, G8, A16; R1, R3).

## Known limits (said plainly)

1. The books' usage is not captured until their routine writes a timing record (owner "5 A"). That needs a new book
   version, which is the orchestrator's call. Until then, the books' level reads `unknown`.
2. The data routines' timing record is not in their prompts yet (the owner's step). Until it is, the measured level stays
   `unknown`. Only routines that run once per NSE session are modelled; the coming 15-minute recorder needs its own
   expected-run rule when it is built.
3. The measured basis moves with development work; after 2026-12 a fixed figure from the owner is required.
4. Python cannot call the session tools. A Claude session must save the exports and run the commands; nothing is
   scheduled.
5. Main-loop tokens undercount side calls. Self-timed rows have no tokens.
6. No lock for two recorders running at once. A false roster `limit` within 1-100 cannot be detected. A hard link into
   the repository is not detected. A cited row is not tied to its item.
7. The stop-rule inputs have no paths yet; each producing story adds its own.

## What the judge should test hardest

- A real export of a finished session, read end to end, including the real last page. Then the same export with a
  middle page dropped, and one with `captured_at` set to midday.
- A real `list_sessions(mine=true)` export through `record-roster`; then drop one development session's usage and see
  `unknown`.
- Recompute S1's rounding by hand on an uneven month, including the tie-break.
- A fake, partial or misdated citation.
- The pushback on MF3: that `alert` or `stop` with only book sessions missing is a proven floor.
