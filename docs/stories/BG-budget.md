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

**What "plan's measured session minutes" means here, and its limit (stated, not hidden).** The Claude plan has no
published minutes allowance: a session's rate-limit information says only "allowed" and when the five-hour window
resets, never how much of the plan is used. So the plan's capacity in minutes **cannot be measured from available
data**. This story uses, by default, the literal reading that can be measured: the cap is 50% of **all measured session
minutes in the month** (books and roles, development and data routines, from `accounting/ai_usage.csv`). Two flaws, both reported on
every meter: (a) when development is quiet, the books' share rises and can hit the cap while the plan is barely used;
when development is busy, the cap is loose; (b) the books' routine sessions cannot be read yet (F8 facts), so their
minutes are missing: the reading is then "unknown" or "at least this level" (criterion 7). The owner may instead state a monthly
minutes figure (`budget.plan_minutes_per_month` in `config.yaml`); the cap is then 50% of that number. Choosing is the
owner's decision (open question 2); this story never sets the number.

**Scope.** In:
- the meter, per month, one line per item of 8.1: Claude subscription (cash spend = the owner's recorded fee; the
  allocated share per purpose from F8, "allocated, not a bill"; the AI minutes cap), GitHub Actions and Drive (no cap),
  Azure Database for PostgreSQL, Groww API, recorder and monitor hosting (a Claude routine by the owner's 15 Oct decision: its `data_routines` minutes,
  no cash cost), paid data (owner records each). A month with
  no recorded amount for an item shows "not recorded", never zero;
- the new-cost rule: a recorded cost of an item other than the existing Claude subscription and Azure database, or of
  an item not in 8.1, is flagged "needs the owner's written yes" unless its `source` cites a `DESK_DECISIONS` row;
- the cap: books-and-roles minutes as % of the cap; level `ok` below 80%, `alert` from 80%, `stop` from 100%,
  `unknown` when there is nothing to measure against. The alert text and the stop signal (with 7.6's stop order:
  analysts, idea generator, post-mortem writer, devil's advocate objections, AI forecasters last; code jobs keep
  running) are data, written to `accounting/budget/<YYYY-MM>_signal.json` for a later routine to act on;
- alert sending behind `AlertSender`; this story wires only a dry-run sender that prints what it would send;
- the stop-rule tracker: the review date (projected while v4 is not frozen, saying what it depends on), days left,
  and each input of Test A and Test B with the story that produces it and whether it exists yet; each test reads "not
  computable yet" while an input is missing;
- `python -m fno budget meter | signal | stop-rule | record-usage`.
Out: any scheduling or routine; sending to Slack (a later routine wires the Slack sender); stopping roles itself (no AI
role exists to stop yet); computing Test A or Test B (G6, G8, R1, R3); per-book ledger lines (F8 later).

**Design:** `fno/budget/` with one module per job: `usage_export.py` (reader interface and export adapter, F8),
`usage_ledger.py`, `allocation.py`, `items.py` (8.1 items, cash spend, new-cost rule), `cap.py` (minutes cap and
level), `signal.py` (signal data and the dry-run alert), `capture_coverage.py`, `stop_rule_tracker.py`, `report.py`
(printed lines), `cli.py`; composition root `fno/budget/wiring.py`. Owner numbers (50%, 80%, 100%) live in
`config.yaml` under `budget`, quoting the decision. The review date uses the NSE session calendar (A7); when its year
is missing (2027 today) the last weekday is used and labelled, until NSE's 2027 circular rows are added.

**Acceptance criteria:**
1. The meter shows every item of 8.1 for the month, with cash spend and allocated cost in separate fields, and "not
   recorded" (never zero) for an item with no recorded amount (test).
2. The cap level is `ok` below 80%, `alert` from exactly 80%, `stop` from exactly 100%, compared in decimals so an
   exact boundary is never read as just below it (boundary tests, including 0.68 of 1.70 minutes); `unknown` with no
   measured minutes, and on the measured basis when no development minutes are recorded (the books would otherwise
   read as all the use). The alert text floors its percentage, so it never reads 100% below the stop level.
3. With `plan_minutes_per_month` unset, the cap is 50% of the month's measured minutes of all purposes; set, it is 50%
   of that number; the meter names which basis it used and its limits (test).
4. The signal file holds the level, the % of cap, the alert text, the stop flag, 7.6's stop order and "code jobs keep
   running"; the dry-run sender sends nothing and says so (test with no network).
5. A recorded new cost without a cited owner decision is flagged; with one, it is not (test).
6. The stop-rule tracker gives 31 May 2027 for a freeze in November 2026, labels it "projected" with the dependency
   while no freeze date is set, gives days left from a given day, and reports both tests "not computable yet" listing
   each missing input and its story (test).
7. Missing captures (fired AI book sessions before today with no usage row) are counted. They can only raise the books'
   share, so with missing captures an `ok` reading becomes `unknown` and an `alert` or `stop` reading is marked "at
   least this level"; the signal file carries the same level and note (test). Development sessions never recorded are
   not tracked and lower the measured share; the meter says so (its basis limit) and prints "no rows recorded", never
   0, for a purpose without rows.

**Test plan:** unit tests with constructed CSV files and exports; a CLI test that prints the meter for a temporary
repository; no network, no Slack.

**Judge verifies:** recomputes one month's cap % and level from the CSV files; plants a cost without a decision; checks
the review date against a hand count of months; checks that no code path posts to Slack.

**Open questions for the owner:**
1. **How to read the AI books' routine sessions' usage.** They are not visible to the session tools from other
   sessions. Options: (a) the routine's prompt ends by reading its own session (`get_session` with no id describes the
   calling session) and saving the export, if routine sessions have those tools (to be tested on the next fire);
   (b) the owner reads the usage page of claude.ai once a month and records the books' minutes. Recommendation: test (a)
   first (reasoning only).
2. **The cap basis:** keep "50% of all measured minutes" (measurable, but moves with development) or state a monthly
   minutes figure for the plan. Recommendation: state a figure once two months of measured totals exist, so it rests on
   data (reasoning only).
3. The owner records the Claude plan's monthly fee in `accounting/operating_costs.csv` (item `Claude subscription`,
   category `ai`); until then every allocated figure is "unknown".

**Depends:** F8 (minimal), C1, A7 · **Size:** S · **Status:** built on `story/f8-bg1-budget`, waiting for the judge
(response 104)
