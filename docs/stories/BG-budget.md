# Epic BG: budget and stop rules

Roles: tax and cost accountant, portfolio manager, risk manager, statistician. Goal: the project's monthly costs are
measured against the owner's caps, the desk is warned before a cap is reached, and the whole-project stop rule's
review date and inputs are known ahead of time (design v2 sections 7.6, 8.1 and 8.2). Story template and definition
of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## BG1. Budget meter and stop-rule tracker

**Repository:** trading

**Description:** As the portfolio manager, I want each month's costs shown item by item against the owner's caps,
with an alert at 80% and a stop signal at 100% of the AI cap, and the stop-rule review date with which of its inputs
exist yet, so that AI use never quietly outgrows its budget and the stop-or-continue review is never a surprise.

**Context and why:** Owner decisions of 15 Oct 2026 (`docs/DESK_DECISIONS.md`): "Monthly AI budget accepted": AI
routine use for books and roles capped at half of the plan's measured session minutes; any new recurring cash cost
needs the owner's written yes; alert at 80%; AI roles stop at 100% while code jobs keep running. "Stop-rule review":
about 31 May 2027, the last session of the sixth full calendar month after protocol v4's freeze. Design v2 section 8.1
lists the items; section 7.6 the order in which AI roles stop. F8 (minimal, built with this story) measures usage.

**What "plan's measured session minutes" means here, and its limits (stated, not hidden).** The Claude plan has no
published minutes allowance: a session's rate-limit information says only "allowed" and when the five-hour window
resets, never how much of the plan is used (confirmed by judge 104). So the plan's capacity in minutes **cannot be
measured**. Owner, 15 Oct 2026 ("7 A"): "50% of measured minutes for two months, then a fixed monthly figure from real
data". So until `budget.measured_basis_until` (2026-12: November and December as the two months, October partial;
owner to confirm) the cap is 50% of **all measured session minutes in the month** (books and roles, development and
data routines, from `accounting/ai_usage.csv`); after it, 50% of the owner's figure (`plan_minutes_per_month`), which
no builder sets. Limits, printed on every meter: the measured basis moves with development (quiet development raises
the books' share); missed development or data-routine sessions make the share look higher and missed book sessions
make it look lower, so a level is given only when it is known (criterion 7). The data routines' timing records need a
change to each routine's prompt: the owner's step, described here, not done by this story.

**Scope.** In:
- the meter, per month, one line per item of 8.1: Claude subscription (cash spend = the owner's recorded fee, INR
  20,000 a month by the owner's 15 Oct row; the allocated share per purpose from F8, "allocated, not a bill"; the AI
  minutes cap), GitHub Actions and Drive (no cap; storage not reported yet, a stated gap: no Drive size source is
  wired), Azure Database for PostgreSQL, Groww API, recorder and monitor hosting (a Claude routine by the owner's 15
  Oct decision: its `data_routines` minutes, no cash cost), paid data (owner records each). A month with no recorded
  amount for an item shows "not recorded", never zero;
- the new-cost rule: a recorded cost of an item other than the existing Claude subscription and Azure database, of an
  item not in 8.1, or any negative amount, is flagged "needs the owner's written yes" unless its `source` reads
  `DESK_DECISIONS: <bold title>` and that row exists in `docs/DESK_DECISIONS.md`;
- the cap: books-and-roles minutes as % of the cap; levels `ok`, `alert` (from 80%), `stop` (from 100%) and `unknown`.
  The alert text and the stop signal (with 7.6's stop order: analysts, idea generator, post-mortem writer, devil's
  advocate objections, AI forecasters last; code jobs keep running) are data, written to
  `accounting/budget/<YYYY-MM>_signal.json` for a later routine to act on;
- alert sending behind `AlertSender`; this story wires only a dry-run sender that prints what it would send;
- the stop-rule tracker: the review date (projected while v4 is not frozen, saying what it depends on), days left,
  each input of Test A and Test B with the story that produces it and whether it exists yet ("not computable yet"
  while one is missing), and design 6.5's SYSTEM alert "a stop-rule date reached" from that date on (dry run);
- `python -m fno budget meter | signal | stop-rule | record-usage | record-roster`; refusals are one line, never a
  traceback.
Out: any scheduling or routine; sending to Slack (a later routine wires the Slack sender); stopping roles itself (no AI
role exists to stop yet); computing Test A or Test B (G6, G8, R1, R3); Drive storage reporting (no source yet);
F8 part 2.

**Design:** `fno/budget/` with one module per job: `usage_reader.py` (the interface), `usage_export.py` and
`self_timed.py` (its two readers), `usage_ledger.py`, `session_roster.py` (development sessions and their coverage),
`capture_coverage.py` (fired book sessions), `allocation.py`, `items.py` (8.1 items, cash spend, new-cost rule),
`cap.py` (minutes cap, coverage rules, level), `signal.py`, `stop_rule_tracker.py`, `report.py` (printed lines),
`cli.py`; composition root `fno/budget/wiring.py`. Owner numbers (50%, 80%, 100%, `measured_basis_until`) live in
`config.yaml` under `budget`, quoting the decisions, and are checked when read (0 < share <= 100, 0 < alert <= stop).
The review date uses the NSE session calendar (A7); when its year is missing (2027 today) the last weekday is used
and labelled, until NSE's 2027 circular rows are added.

**Acceptance criteria:**
1. The meter shows every item of 8.1 for the month, with cash spend and allocated cost in separate fields, "not
   recorded" (never zero) for an item with no recorded amount, and the storage gap stated (test).
2. The cap level is `ok` below 80%, `alert` from exactly 80%, `stop` from exactly 100%, compared in decimals so an
   exact boundary is never read as just below it (boundary tests, including 0.68 of 1.70 minutes); `unknown` with no
   measured minutes. Printed percentages are floored to one decimal, so 99.6% never reads 100% (test).
3. Until `measured_basis_until`, with `plan_minutes_per_month` unset, the cap is 50% of the month's measured minutes of
   all purposes; set, it is 50% of that number; after that month with no figure set, the level is `unknown` and the
   meter says the owner's fixed figure is owed; bad settings are refused (tests).
4. The signal file holds the level, the % of cap, its note, the alert text, the stop flag, 7.6's stop order and "code
   jobs keep running"; the wiring gives only the dry-run sender, which sends nothing and says so (tests).
5. A recorded new cost or negative amount without a cited, existing owner decision row is flagged; a made-up or
   partial citation is flagged too (test).
6. The stop-rule tracker gives 31 May 2027 for a freeze in November 2026, labels it "projected" with the dependency
   while no freeze date is set, reads `v4_freeze_date` when set, falls back to the last weekday (30 Jul 2027 for a
   January 2027 freeze) while the calendar lacks the year, gives days left, reports both tests "not computable yet"
   with each missing input and its story, and gives the "stop-rule date reached" alert from the date on (tests).
7. A level is given only when it is known. On the measured basis, development must be fully captured (a fresh roster,
   and every development session active in the month read after its last activity), and every expected data-routine
   run recorded (each routine in `budget.data_routines` on its named schedule before today, by its own timing record;
   the 3 pm recorder is `daily`, as it is started every calendar day; an unknown schedule is refused; a
   `data_routines` row must name a configured routine; judge 104 addenda 1-2); otherwise `unknown`, naming why. The owner's-figure basis needs neither.
   Missing book sessions can only raise the books' share, so they turn `ok` into `unknown` and mark `alert` or `stop`
   "at least this level". The allocation warns "book shares overstated" or "understated" accordingly (tests).

**Test plan:** unit tests with constructed CSV files, exports and rosters; CLI tests on a temporary ledger and on the
repository; no network, no Slack.

**Judge verifies:** recomputes one month's cap % and level from the CSV files; plants a cost with a made-up citation;
checks the review date against a hand count of months; drops a development session from the usage; checks that no
code path posts to Slack.

**Owner decisions taken (15 Oct 2026, `docs/DESK_DECISIONS.md`):**
1. "5 A": the routine records its own usage at the end of each run, tested on the next run; the owner's monthly note
   only if that fails. Built as `SelfTimedUsageReader` (a routine cannot read its own run's events at its end); the
   books' prompt change that writes the timing record is a new registered book version, left to the orchestrator.
2. "6 INR 20000 per month": recorded for October 2026 in `accounting/operating_costs.csv`, citing its row, and held as
   one config value (`budget.plan_cost`, citing the same row) that the meter applies to every month from October 2026
   until a newer decision changes it; a recorded payment that differs is flagged (judge 104 addendum 1).
3. "7 A": the measured basis for two months, then a fixed figure (`measured_basis_until`, `plan_minutes_per_month`).

**Depends:** F8 (minimal), C1, A7 · **Size:** S · **Status:** done: judge 104 addendum 3 PASS (4fcea00), merged
757c20d (addendum 4)

---

## BG1-w. The AI books' reveal wait does not count in BG1's cap

**Repository:** trading · **Lane:** 1 (BG1's cap decides when the AI roles and books stop) · **Builder:**
session_016CU8KFuEEtWAM7ZNnFcKxv (BG1's earlier owner is out of reach; orchestrator, 24 Oct)

**Description:** As the portfolio manager, I want BG1 to count only an AI book run's working minutes (brief to seal)
against the cap, with the wait from the seal to the reveal shown apart, so that the v4 books' 24-28 idle minutes a day
never use up the cap or stop the books.

**Context and why (each fact marked):**
- Owner, 24 Oct 2026 (`docs/DESK_DECISIONS.md`, "The AI books' reveal wait does not count in BG1's cap"): "Waiting
  minutes - Option A". BG1 counts a book's working minutes (brief to seal) only. The seal-to-reveal wait is reported
  apart and never capped. (Owner's words.)
- In v4 a book fires at about 14:41 and seals by 14:42-14:46. `reveal` then waits until 15:10:10, about 24-28 minutes
  (G11's story, change 6, on `story/g11-ai-books-v4`; measured from 9 v2 book-days, 16-23 Oct). (Fact, G11's numbers.)
- Today BG1's reader `fno/budget/self_timed.py` records a run's minutes from `started_at` to `ended_at` (judge J,
  verdict 586). One place decides the minutes: BG1's meter and G11's C8 stop (`fno/ai/budget_stop.py` on G11's branch)
  both read the same ledger (`accounting/ai_usage.csv`) through the meter. (Fact, code read.)
- G11's `run_timing.py` (on its branch) adds two fields to each book's timing file: `sealed_at` (an ISO time with zone,
  or null when the run never sealed) and `reveal_calls`. Main's files have neither yet. (Fact, G11's branch at
  d8aabba4c; the fields BG1-w reads are agreed with G11's builder through the orchestrator.)
- The ledger holds 10 rows today, all "start to end" (4 book rows a few minutes each, v2). (Fact.)

**Design (reasoning only, for the judge):**
- `SelfTimedUsageReader` splits a run that has a seal: `minutes` = seal − start (working), `wait_minutes` = end −
  seal. A record without the `sealed_at` key (a data routine, the post-mortem, a book file from before G11) stays start
  to end with no wait, as today.
- `DayUsage` gains `wait_minutes: float | None` (None: not measured apart). The ledger gains one column,
  `wait_minutes`, after `minutes`; a blank is "no wait measured apart". The existing file gets the column in the same
  commit, blank in every old row, so no recorded value changes (rows stay written once).
- The cap, the measured basis and G11's stop read `minutes` only, so the wait is never capped. The wait also leaves the
  measured basis (all recorded minutes of the month): the decision says BG1 counts working minutes, and the wait is one
  idle tool call (a timed sleep until 15:10:10) that uses no model capacity, which the basis stands for. Keeping it in
  the basis would raise the cap by the books' own idle time (reasoning only; the judge may rule otherwise).
- The meter prints the month's wait on its own line, outside the cap.

**Acceptance criteria:**
1. **Working minutes.** A timing record with a valid `sealed_at` gives `minutes` = seal − start and `wait_minutes` =
   end − seal, each to 2 decimals, with the source "self-timed by the routine (start to seal; the wait to the end
   apart)". G: start 14:41:00, seal 14:44:30, end 15:10:40 gives 3.50 and 26.17. Bd: a seal at the start gives 0.00
   working (a measured zero); a seal at the end gives 0.00 wait. B: a seal before the start or after the end is refused,
   naming both times; a `sealed_at` without a zone, or not an ISO time, is refused. E: below (criterion 2).
2. **No seal: working unknown, never 0 and never the whole run.** A record whose `sealed_at` is null or empty is
   refused ("working minutes unknown: the run never sealed"): no ledger row. The fired session then counts as not
   captured (BG1 criterion 7), so the level is `unknown`, or `alert`/`stop` "at least". A fired run with no timing file
   takes the same path. G: a never-sealed run leaves the month `unknown` and names one session not captured. E: no
   timing file, the same. B: a refused record never writes 0 and never the start-to-end minutes.
3. **No `sealed_at` key: unchanged.** A record without the key is start to end with a blank `wait_minutes`, byte for
   byte the row BG1 writes today (G: the post-mortem's record; Bd: a book file from before G11).
4. **The ledger column.** `accounting/ai_usage.csv` gains `wait_minutes` after `minutes`. The migration changes no
   value of any old row (test against the committed file before it). A wait that is negative, not a number, `nan` or
   `inf` is refused on reading, like `minutes`. A blank is allowed. A session-day is still written once (G: a new row
   with a wait; B: `-1` refused; Bd: `0.00`; E: blank).
5. **Never capped.** The cap's books-and-roles minutes and the measured basis read `minutes` only. G: one book run of
   3.50 working and 26.17 waiting adds 3.50 to both. B: a plant that adds the wait to either changes a tested level.
   G11's C8 stop reads the same meter, so it needs no change; a test runs `MeterBudgetStop`'s sum on the meter's rows
   only after G11 merges (G11's file).
6. **The meter shows the wait apart.** `budget meter` prints "AI books' reveal wait (not capped): X minutes over N
   run(s)" for the month. "none recorded" when no row has a wait. G: two runs; E: none; Bd: one run with a 0.00 wait
   counts as one run.
7. **Gates.** pytest, ruff, ruff format, `check_imports`, `check_records`, `check_numbers` on `main`; no file or class
   over 350 lines. Real output sample: `python -m fno budget meter --month 2026-10` before and after.

**Gap list (the decision's parts):**
- Working minutes counted: criteria 1 and 5. The wait reported apart: criteria 1, 4 and 6. Never capped: criterion 5.
- "No seal: working unknown, never 0, never the whole run" and "no timing file": criterion 2.
- Out of scope, with why:
  - **The reveal calls (turns) of the wait** are G11's C17 report (`v4_cost.py`). BG1's `turns` stays 1 per run.
  - **Old rows are not rewritten.** The ledger is written once; the 4 v2 book rows keep their start-to-end minutes,
    which include v2's own short wait. Stated, not corrected.
  - **G11's files.** `run_timing.py`'s docstring ("BG1's reader reads only start and end, so its minutes are
    unchanged") and `v4_cost.py`'s ("start-to-end minutes as BG1's ledger holds them") become wrong once this merges.
    That is for G11's builder, through the orchestrator; BG1-w never edits `fno/ai/`.
  - **Until G11 merges, nothing changes in practice:** main's timing files have no `sealed_at`.
  - **The signal file** keeps the level and % only; the wait is in the meter's lines, not in the signal.

**Test plan:** unit tests on constructed timing records and ledgers in `tests/budget/`; one CLI test of `budget meter`
on a temporary ledger; the migration test against the committed file; no network.

**Judge verifies:** recomputes one split by hand; plants the wait into the cap and into the basis; plants a
never-sealed run recorded as 0 and as start to end; checks the migrated file's old values against `git show` of the
file before it.

**Depends:** BG1, F8c; G11's timing fields (read only) · **Size:** S · **Status:** story text, for the judge
