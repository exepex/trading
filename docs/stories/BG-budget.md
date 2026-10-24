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
session_016CU8KFuEEtWAM7ZNnFcKxv (BG1's earlier owner is out of reach; orchestrator, 24 Oct) · **Round 2** of the text
(judge 587: one should-fix, five minors, each answered below)

**Description:** As the portfolio manager, I want BG1 to count only an AI book run's working minutes (brief to seal)
against the cap, with the wait from the seal to the reveal shown apart, so that the v4 books' 24-28 idle minutes a day
never use up the cap or stop the books.

**Context and why (each fact marked):**
- Owner, 24 Oct 2026 (`docs/DESK_DECISIONS.md`, "The AI books' reveal wait does not count in BG1's cap"): "Waiting
  minutes - Option A". BG1 counts a book's working minutes (brief to seal) only. The seal-to-reveal wait is reported
  apart and never capped. (Owner's words; nothing else in this story is the owner's unless it says so.)
- In v4 a book fires at about 14:41 and seals by 14:42-14:46. `reveal` then waits until 15:10:10, about 24-28 minutes
  (G11's story, change 6, on `story/g11-ai-books-v4`; measured from 9 v2 book-days, 16-23 Oct). (Fact, G11's numbers.)
- Today BG1's reader `fno/budget/self_timed.py` records a run's minutes from `started_at` to `ended_at` (judge J,
  verdict 586). One place decides the minutes: BG1's meter and G11's C8 stop (`fno/ai/budget_stop.py` on G11's branch)
  both read the same ledger (`accounting/ai_usage.csv`) through the meter, and only its `minutes` column. (Fact, code.)
- G11's `run_timing.py` (on its branch) writes the `sealed_at` key in every book timing file: an ISO time with zone, or
  null when the run never sealed (judge 587, `run_timing.py` publish, `book_wiring.py:23`). The key is absent only from
  files written before G11 merges. (Fact; the field is agreed with G11's builder through the orchestrator.)
- The ledger holds 10 rows today, all start to end: 7 book rows (book2_hybrid 4, book3_ai 3, v2, about 4-5 minutes
  each) and 3 post-mortem rows. (Fact.)
- A book run that never sealed has happened: 14 Oct (`conversations/2026-10-15.md:398`). (Fact.)

**Design:**
- `SelfTimedUsageReader` splits a run that sealed: `minutes` = seal − start (working), `wait_minutes` = end − seal. A
  record without the `sealed_at` key (a data routine, the post-mortem, a book file from before G11) stays start to end
  with no wait, as today.
- `DayUsage` gains `wait_minutes: float | None` (None: not measured apart). The ledger gains one column,
  `wait_minutes`, after `minutes`; a blank is "no wait measured apart". The existing file gets the column in the same
  commit as `COLUMNS` (`rows()` refuses any other header, `_write` writes the whole file), blank in every old row, so
  no recorded value changes and rows stay written once.
- The cap, the measured basis and G11's stop read `minutes` only, so the wait is never capped. **The wait also leaves
  the measured basis.** Reason: the owner's "BG1 counts a book's working minutes only" covers the basis too (the basis
  is the sum of the same `minutes` column, `cap.py:73-79`), and a smaller basis only gives a smaller cap, so the books
  stop earlier, never later (judge 587's ruling).
- The meter prints the month's wait on its own line, outside the cap.

**A run that never sealed: the builder's choice, one switch, for the owner (reasoning only).** The owner's decision
does not say what a run with no seal time counts. Two rules were weighed:
- **`no_seal_upper_bound` (owner decided 24 Oct (DESK_DECISIONS); the orchestrator's recommendation).** The run counts
  start to end, as today, labelled in its row's source "no_seal_upper_bound: never sealed, start to end counted". Its
  working minutes are at most that, so the row is an upper bound: it counts a broken run's wait (if any) against the
  cap, never a sealed run's. The session is captured, the month's level stays known, and G11's stop can act on it.
  Cost: a broken run's idle minutes are capped, which overstates use only on broken runs.
- **`no_seal_unknown`.** The record is refused ("working minutes unknown: the run never sealed"): never 0, never start to
  end. Cost, stated plainly (judge 587): a refused file never becomes a ledger row, and `ai collect` offers it again on
  every run, printing the same refused line each time (`usage_record.py:5`). Its fired session stays not captured for
  the rest of the month, so a month below the alert line reads `unknown` until the month ends (`cap.py:94-95`), and
  G11's C8 stop, which stops only on `stop`, keeps firing the books (fail open). One broken run a month hides the cap
  for that month.
- **The switch** is one named constant, `NO_SEAL_RULE` in `fno/budget/constants.py` (the reader's default; G11's
  recorder builds the reader with the path only, so no `fno/ai/` file changes). Changing the rule is that one line.

**Acceptance criteria:**
1. **Working minutes.** A timing record with a valid `sealed_at` gives `minutes` = seal − start and `wait_minutes` =
   end − seal, each to 2 decimals, with the source "self-timed by the routine (start to seal; the wait to the end
   apart)". G: start 14:41:00, seal 14:44:30, end 15:10:40 gives 3.50 and 26.17. Bd: a seal at the start gives 0.00
   working (a measured zero); a seal at the end gives 0.00 wait. B: a seal before the start or after the end is refused,
   naming both times; a `sealed_at` without a zone, or not an ISO time, is refused. Plant: the split swapped or the wait
   left in `minutes`.
2. **A run that never sealed** (`sealed_at` null or empty), under each rule of the switch. `no_seal_upper_bound`: one
   row, `minutes` = end − start, `wait_minutes` blank, the source naming `no_seal_upper_bound`; the session is captured
   and the level known. `no_seal_unknown`: refused with "working minutes unknown: the run never sealed", no row; the
   session counts as not captured (BG1 criterion 7), so the level is `unknown`, or `alert`/`stop` "at least". G: one
   never-sealed run under each rule. E: a fired run with no timing file is not captured under both rules (unchanged).
   B: under neither rule is a never-sealed run written as 0. The default is `no_seal_upper_bound` (test). Plants: the
   default flipped; the upper bound written as 0; the unknown rule writing a row.
3. **No `sealed_at` key: unchanged values.** A record without the key gives the same values as BG1 writes today, with
   `wait_minutes` blank (G: the post-mortem's record; Bd: a book file from before G11). Plant: a missing key read as a
   never-sealed run.
4. **The ledger column.** `accounting/ai_usage.csv` gains `wait_minutes` after `minutes`. The migration changes no
   value of any old row (test against `git show` of the file before it). A wait that is negative, not a number, `nan` or
   `inf` is refused on reading, like `minutes`; a blank is allowed. A session-day is still written once (G: a new row
   with a wait; B: `-1` refused; Bd: `0.00`; E: blank). Plants: the wait's check dropped; an old value changed by the
   migration.
5. **Never capped.** The cap's books-and-roles minutes and the measured basis read `minutes` only. G: one book run of
   3.50 working and 26.17 waiting adds 3.50 to both. B: plants adding the wait to the cap, or to the basis, change a
   tested level. G11's C8 stop sums the meter's `usage_rows` `minutes` (`MeterBudgetStop`): this story's test checks that
   the meter's rows carry working minutes in `minutes` and the wait only in `wait_minutes`, so C8 reads working minutes
   with no change; a test through `MeterBudgetStop` itself is G11's (session_01Rga1fe3C4rmnrmmE1p3diE), asked through
   the orchestrator.
6. **The meter shows the wait apart.** `budget meter` prints "AI books' reveal wait (not capped): X minutes over N
   run(s)" for the month, "none recorded" when no row has a wait, and under it the count of `no_seal_upper_bound` rows
   when there are any. G: two runs; E: none; Bd: one run with a 0.00 wait counts as one run. Plant: the line summing
   `minutes` instead of `wait_minutes`.
7. **Gates.** pytest (the Slack token kept, DESK_DECISIONS 24 Oct), ruff, ruff format, `check_imports`,
   `check_records`, `check_numbers` on `main`; no file or class over 350 lines. Real output sample: `python -m fno
   budget meter --month 2026-10` before and after.

**Gap list.**
- The owner's decision: working minutes counted (criteria 1, 5); the wait reported apart (1, 4, 6); never capped (5).
- The builder's own rules, each marked as such: the never-sealed run (criterion 2, the switch, for the owner); the
  wait leaving the basis (design, judge 587's ruling); unchanged records without the key (criterion 3).
- Out of scope, with why, and what this change makes untrue elsewhere:
  - **The reveal calls (turns) of the wait** are G11's C17 report (`v4_cost.py`). BG1's `turns` stays 1 per run.
  - **Old rows are not rewritten.** The ledger is written once; the 7 v2 book rows keep their start-to-end minutes,
    which include v2's own short wait. Stated, not corrected.
  - **G11's files** (G11's builder, through the orchestrator; BG1-w never edits `fno/ai/`): `run_timing.py`'s docstring
    ("BG1's reader reads only start and end, so its minutes are unchanged") and `v4_cost.py`'s ("start-to-end minutes
    as BG1's ledger holds them") become wrong. Under `no_seal_unknown`, `usage_gaps.py`'s alert ("stopped before its
    reveal, or its timing could not be published") would give the wrong reason for a never-sealed refusal; under the
    default upper bound the file is recorded, so that alert does not fire for it.
  - **The refused line repeating every collect** happens only under `no_seal_unknown` (stated above).
  - **The dashboard contract** `contracts/omenix-dashboard/api/schemas/fno-budget.yaml:19` says "session minutes"
    for `books_and_roles_minutes`. After BG1-w they are working minutes for a book run that sealed. The contract is
    `x-fill: not_built`; its wording is W3g's owner's, through the orchestrator.
  - **Until G11 merges, nothing changes in practice:** main's timing files have no `sealed_at`.
  - **The signal file** keeps the level and % only; the wait is in the meter's lines, not in the signal.

**Test plan:** unit tests on constructed timing records and ledgers in `tests/budget/`; one CLI test of `budget meter`
on a temporary ledger; the migration test against `git show`; no network.

**Judge verifies:** recomputes one split by hand; plants the wait into the cap and into the basis; plants a
never-sealed run recorded as 0, and flips the switch; checks the migrated file's old values against `git show` of the
file before it.

**Depends:** BG1, F8c; G11's timing field (read only) · **Size:** S · **Status:** story text round 2, for the judge; the
never-sealed rule for the owner (default `no_seal_upper_bound`)

### BG1-w Claims (code, round 1)

Builder session_016CU8KFuEEtWAM7ZNnFcKxv, branch `story/bg1w-reveal-wait`; text PASS judge 587.1. The never-sealed rule
is `no_seal_upper_bound`: owner decided 24 Oct (DESK_DECISIONS).

**What changed:**
- `fno/budget/self_timed.py`: `_split` gives (counted minutes, wait apart, source). With a seal the wait is the whole
  run less the working minutes, so the two parts always add up to the run (0.33 + 0.34 for 20 s + 20 s). The reader's
  `no_seal` argument defaults to the switch, read when the reader is built.
- `fno/budget/constants.py`: `NO_SEAL_RULE`, the one switch.
- `fno/budget/usage_reader.py`: `DayUsage.wait_minutes`.
- `fno/budget/usage_ledger.py`: the `wait_minutes` column, its reading check, and the record line names the wait.
- `fno/budget/report.py`: the meter's wait line, and the count of upper-bound rows (by the rule's name in the source).
- `accounting/ai_usage.csv`: the column added, blank in the 10 earlier rows. No other byte of a value changed.

| Criterion (code) | Tests (`tests/budget/test_reveal_wait.py`, `test_wait_ledger.py`): good / bad / boundary / empty | Plants, each caught |
|---|---|---|
| 1 working minutes (`_split`) | 3.50 and 26.17; a seal at the start (0.00 working) or the end (0.00 wait); a seal in UTC; a seal outside the run, with no zone, not ISO, or a number, refused under both rules; the parts add up | C1a split swapped (7); C1b the wait left in `minutes` (6); C1c a seal outside not refused (2); C1d the wait rounded on its own (1) |
| 2 a never-sealed run, each rule explicitly (judge 587.1's condition) | the upper bound: start to end, labelled, null and ""; the unknown rule: refused, null and ""; the default is the upper bound, and flipping the switch flips it; a bad rule is refused. End to end through G11's recorder (unchanged) and the meter: captured with the level known, or not captured with the level `unknown`. E: a fired run with no timing file is not captured under both rules | C2a default flipped (2); C2b upper bound written as 0 (2); C2c the unknown rule writing a row (4); C2d "" read as a time (2) |
| 3 no key: unchanged values | start to end, wait blank, the old source, under both rules | C3 a missing key read as never sealed (11) |
| 4 the ledger column | a new row with a wait; `26.17`, `0.00` and blank read; `-1`, `-0.01`, `nan`, `inf` and text refused; every earlier row of the committed ledger equal to `git show d062fe347` with a blank wait | C4a the wait's check dropped (5); C4b the wait not written (3); C4c an old value changed (1); C4d the record line hiding the wait (1) |
| 5 never capped | one run of 3.50 + 26.17: the cap's minutes 3.5, the basis 3.5, the cap 1.75; the ledger row carries 3.50 in `minutes` (what G11's C8 sums) | C5a the wait into the cap; C5b the wait into the basis. Each was also run with a non-crashing `.get` variant on the new tests alone, so the catch is this test, not a KeyError elsewhere: 2 and 1 failed |
| 6 the meter's line | none recorded; two runs (26.17 and 0.00) give "26.17 minutes over 2 run(s)" with the cap at 33.17; one run with a 0.00 wait is one run; the upper bounds counted | C6a summing `minutes` (2); C6b a 0.00 wait not counted (2); C6c the upper bounds not shown (1) |

18 plants, 18 caught, run in a separate worktree, each restored with `git checkout --` (`git status` clean).

**Real output sample.**
- `python -m fno budget meter --month 2026-10` on the repository, before and after: one new line, "AI books' reveal
  wait (not capped): none recorded". Every other line is identical (diff of the two outputs), because no committed
  timing file has `sealed_at` until G11 merges.
- From a test ledger (one sealed run, one never sealed):
  ```
  measured books_and_roles: 33.17 minutes, 2 session(s), output tokens not available
  AI books' reveal wait (not capped): 26.17 minutes over 1 run(s)
    1 run(s) never sealed, counted start to end (no_seal_upper_bound, an upper bound)
  AI cap: books and roles 33.17 of 500.00 minutes = 6.6%; level ok
  ```
  The ledger rows: `...,3.50,26.17,1,...,self-timed by the routine (start to seal; the wait to the end apart),...` and
  `...,29.67,,1,...,self-timed by the routine (no_seal_upper_bound: never sealed; start to end counted),...`.

**Self-review** (an independent agent, given the diff and the story only): no blocking findings, 2 should-fix and 4
minor.
- **Fixed:**
  - The parts now add up to the run.
  - The upper bounds are counted by the rule's name, not the source's exact wording, and the report no longer imports
    the reader.
  - The record line names the wait.
  - The tests write through `record`, not the private `_write`, and the 0.00 wait has its own one-run case.
- **Stated limits (should-fix 1 and 2):**
  - **Cost allocation changes meaning with the minutes.** BG1's allocation (`allocation.py:42`) and F9a's unit cost
    (`role_value/cost.py:43-44`) split the plan cost by `minutes`. Once G11 merges, a v4 book day counts about 3.5
    minutes, not about 30, so the books' share of the plan cost falls about 8 times. Development still counts its idle
    wall time. In October, rows from before G11 (wait included) and v4 rows (working only) sit in one month on two
    bases. This is consistent with the owner's "working minutes only", but the owner may want the allocation on another
    basis. That is for the orchestrator and F9a's owner, and nothing is changed here.
  - **Merge hazard.** The branch rewrites every line of the ledger. A row that `ai collect` appends on `main` before
    the merge (a trading day, about 15:15-15:35 IST) conflicts. Resolve it by giving each newer row a blank
    `wait_minutes` and nothing else; `rows()` refuses a 15-field row, so the full suite catches a wrong resolution.
    Merge outside 15:15-15:35 IST.
- **Not changed:** criterion 3's good case uses a book record with the key dropped. The real post-mortem record is
  already covered by `test_self_timed.py`.

**Also open, for other builders through the orchestrator:**
- G11's `tests/ai/test_run_timing.py:58-60` (on its branch) asserts 4.17 minutes for a record with `sealed_at`, which
  is start to end. After both merge it reads working minutes, so G11's builder updates that expectation.
- G11's two docstrings, and the dashboard contract's "session minutes" (gap list).

---

## BG1-t. The stop-rule tracker reads Test A's real inputs and the freeze date from the freeze record

**Repository:** trading · **Lane:** 1 (the whole project's stop-or-continue review and its tests) · **Builder:**
session_016CU8KFuEEtWAM7ZNnFcKxv (BG1's owner) · **Size:** S

**Description:** As the portfolio manager, I want the stop-rule tracker to see Test A's inputs when they exist and to
take protocol v4's freeze date from the freeze record itself, so that Test A can become computable and the review date
can never disagree with the freeze.

**Context and why (each fact marked):**
- Owner, 15 Oct 2026 (DESK_DECISIONS "Stop-rule review and its 'undecided' action"): the review is the last session of
  the sixth full calendar month after protocol v4's freeze. (Owner's rule.)
- **Test A can never become computable today** (fact, `fno/budget/stop_rule_tracker.py:57-60`). Its three inputs have
  no path and no `present` check, so `exists()` is always false:
  - G6, the frozen family;
  - G8, v4 daily scores of V6, V1 and V2 against their primary baselines;
  - A16, 15-minute quotes long enough for V1.
  Found by the v4 freeze builder, 24 Oct; checked by the builder.
- **The freeze's own record** (fact): `research/forecasts/FREEZE_v4.md`, carrying "Frozen on: YYYY-MM-DD", read by
  `LookRecords.frozen()` and `frozen_on()` (`fno/forecast_scoring/v4/records.py:53-64`, wired at
  `fno/forecast_scoring/v4/wiring.py:30,100`). G8's looks are written to `research/forecasts/v4_scores/<day>.json`, with
  `exploratory` true before the freeze (10, 17 and 24 Oct so far). The file does not exist yet; the freeze targets Sun
  25 Oct (G6 freeze, story/v4-freeze).
- **V1's start rule** (fact, `research/forecasts/PROTOCOL_v4.md` section 1.3): "V1: when A16 has 20 non-void
  sessions". The code is `V1_START_SESSIONS = 20` in `fno/forecast_v4_rules/capture.py:46`: A16's live rows with a
  value, counted by `DayForecasts._v1`.
- **The freeze date lives in two places today** (fact): config `budget.stop_rule.v4_freeze_date` (null on main), read
  by `fno/budget/wiring.py:82`, and the record's "Frozen on:" line. G6's freeze story (on `story/v4-freeze`, section 7
  and criterion 8) plans to set the config key to "Frozen on:".
- **The review date with a freeze on 25 Oct 2026** (fact, the owner's rule): October is the freeze's own month, so
  November-April are the six full months. That is the last session of April 2027, Fri 30 Apr 2027 by the weekday
  fallback until NSE's 2027 circular is added. "About 31 May 2027" was the estimate from a projected November freeze.

**Design (reasoning only):**
- Each Test A input gets a `present` check, as Test B's R1 input already has (`_shadows_registered`):
  - **G6 family:** frozen when `LookRecords.frozen()` is true and `frozen_on()` reads a date. A record without its
    "Frozen on:" line is not frozen; the reason is reported, never a traceback.
  - **G8 scores:** at least one look in `v4_scores/` that is not exploratory and is dated after `frozen_on()`.
    Exploratory looks never count.
  - **A16 for V1:** at least `V1_START_SESSIONS` (20, imported, never retyped) A16 live sessions with a value, read
    through the same rows `build_v4_forecasts` reads. **Stated reading:** the tracker's "long enough for V1" is
    protocol 1.3's start rule. If Test A meant a longer series (for example the 250 sessions HAR-intraday needs,
    `HAR_INTRADAY_SESSIONS`), that is a gap for the G6/G8 owner to name. BG1-t uses the start rule and says so on the
    tracker line.
- **The freeze date comes from the record only.** `build_review_date()` takes `frozen_on()` when the record exists,
  else the projected month as today. The config key `budget.stop_rule.v4_freeze_date` is removed. Its readers:
  `fno/budget/wiring.py:82`, `tests/budget/test_stop_rule_tracker.py:59`, `config.yaml:177,198`, and BG1 criterion 6's
  text. `projected_v4_freeze_month` stays for the time before the freeze. A config with the old key is refused, naming
  "FREEZE_v4.md's Frozen on: line", so a stale value can never be read.
- **Coordination with G6's freeze, through the orchestrator:** G6's section 7 and criterion 8 set the key. Under
  BG1-t, the freeze sets nothing in config; criterion 8 becomes "`build_review_date()` gives 2027-04-30 from
  FREEZE_v4.md". If the freeze merges first, BG1-t's commit removes the key it set and its test. Whichever merges second
  carries that change.

**Acceptance criteria:**
1. **G6 input.** Present iff FREEZE_v4.md exists with a "Frozen on:" date. G: a record dated 2026-10-25. B: a record
   without the line, not present, and the tracker names why. E: no record.
2. **G8 input.** Present iff a non-exploratory look is dated after the freeze. G: one look on 2026-10-31. B: only
   exploratory looks (today's 10, 17, 24 Oct); a non-exploratory look dated on or before the freeze. Bd: a look the
   day after the freeze. E: no looks, or no freeze.
3. **A16 input.** Present iff at least 20 A16 live sessions with a value exist. Bd: 19 is absent and 20 present. B: 20
   rows of which one has no value is absent. E: no intraday folder. The line says "V1's start rule (protocol 1.3: 20
   non-void sessions)".
4. **Test A computable.** With all three present, `stop_test_status(root, "A")` is "computable"; with any missing, "not
   computable yet" naming it. Test B is unchanged.
5. **The freeze date from the record.** With FREEZE_v4.md "Frozen on: 2026-10-25", the review is 2027-04-30, labelled
   from the freeze and unconfirmed by the weekday fallback while 2027 is missing. With no record, it is projected from
   `projected_v4_freeze_month` as today. A config with `v4_freeze_date` is refused. A record without its date gives
   "projected" with the reason, never a guessed date.
6. **Gates** as BG1-u, the Slack token kept. Sample: `python -m fno budget stop-rule` before and after, on main and with
   a constructed freeze record.

**Gap list.**
- The finding: all three Test A inputs (1-4); the two freeze-date sources (5).
- Out of scope, with why:
  - **Whether Test A needs more than V1's start** (stated reading above; the G6/G8 owner's).
  - **The review date's owner message and the 15 Oct "half budget" wording**, which is moot under BG1-u's no cap.
    Both go to the owner through the orchestrator.
  - **G6's own files** (its story's section 7 and criterion 8, `FREEZE_v4.md`): G6's builder, through the orchestrator.
  - **Test A's own computation** stays G6/G8's. The tracker only says whether its inputs exist.

**Plants (named):** each `present` check always true; exploratory looks counted; 19 sessions counted as enough; a void
row counted; the config key still read; a record without its date read as a date.

**Depends:** BG1, G6 (freeze record), G8 (looks), A16 (rows) · **Status:** story text, for the judge
