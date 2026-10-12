# Epic O: operations

Roles: head of desk, data engineer, risk manager, judge. Goal: the finished product runs every trading day without
the owner doing anything, fails safely and visibly, and is proven to work across repositories (design 9, 13.1 item 10,
13.8). Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## O1. The daily desk routine

**Repository:** trading

**Description:** As the owner, I want one scheduled cloud routine that runs the whole day (quotes, packs, decisions,
deadline, execution snapshot, fills, exits, publication, Slack) and commits every record, so that the desk runs every
trading day without me.

**Context and why:** Design 13.5 (a scheduled Claude Code cloud session started before 15:00 IST on a frozen
timetable), CLAUDE.md's routine sections (the 3 pm recorder routine `F&O 3 pm quote recorder (weekdays 14:48 IST)`
already runs this way and pushes to `main`). One routine avoids two schedules racing; the recorder becomes the first
step of the day.

**Scope.** In: the routine's prompt, its CLAUDE.md section, schedule, environment needs (credential names only),
commit and push rules, merging with the existing recorder routine. Out: the steps themselves (E3 and others).

**Expected design:** CLAUDE.md section "Daily desk routine" replacing the recorder section once E3 exists: install,
`python -m fno desk run` (E3's `DailyRun`), commit `journal/`, `research/data/quotes/`, `reports/dashboard/`, push to
`main` after `git pull --no-rebase`; failures alert through P4. The existing recorder routine is updated (not deleted)
to the new prompt on the day E3 goes live, so quote history has no gap. Never places orders; never prints credentials.

**Acceptance criteria:**
1. A dry run on a non-counted day completes every step and commits every record (recorded in the conversation log).
2. The quote recording of that day is identical in format to A4's (baseline test still passes).
3. A failure at any step produces an alert and leaves exits running (O2 tests).
4. The routine's stored prompt matches the CLAUDE.md section (checked after each change).

**Test plan:** dry run; O2's tests.

**Judge verifies:** reads the routine definition and one day's commits.

**Depends:** E3, P3, P4, A7 · **Size:** S · **Status:** later

---

## O2. Failure handling, end to end

**Repository:** trading

**Description:** As the risk manager, I want every failure in design section 9 tested end to end, so that a broken
data feed, a missing AI book or a hit limit always means no new risk, running exits and an alert.

**Context and why:** Design 9: data missing or stale -> no new trades, stale prices never used, alert; a role fails to
report -> its conditions count as not met; judge or AI unavailable -> no new trades for that book, risk-reducing exits
still run; limit hit -> code blocks the trade, broken protection is closed; brake hit -> no new trades, open trades
continue; paper results outside the plan -> as the plan says. 13.5: one book's failure never changes another's fills.

**Scope.** In: an end-to-end test suite with fakes for every row of section 9 and the 13.5 failure cases. Out: new
behaviour (each row is implemented in its own story; this proves them together).

**Expected design:** `tests/e2e/test_failures.py` driving `DailyRun` over fixture days with injected failures:
missing snapshot, stale snapshot, invalid execution snapshot, AI session failure, model mismatch, firewall breach,
judge timeout, limit hit, broken protection, brake hit, publication failure, Slack failure.

**Acceptance criteria:**
1. Each injected failure produces exactly the section-9 outcome and an alert naming it.
2. In every case, scheduled exits of open positions still run (or become pending exits with an alert).
3. A failure in one book never changes another book's decision or fills (hash comparison with a no-failure run).

**Test plan:** the suite itself.

**Judge verifies:** runs the suite and reads three failure transcripts.

**Depends:** E3, E4, P3, P4 (F1, F4 for the AI-book cases, added in M5) · **Size:** M · **Status:** later

---

## O3. Cross-repository integration tests

**Repository:** trading (with dashboard and platform)

**Description:** As the owner, I want an integration test at each cross-repository milestone, so that three
repositories that each pass their own tests cannot still fail as one product.

**Context and why:** Design 13.8 (ChatGPT review 25): every cross-repository milestone has an integration acceptance
test; dependency order: canonical F&O records -> read-model schema and publisher -> Azure platform contract ->
dashboard read path -> F&O screens -> migration and cutover -> automated operations.

**Scope.** In: three integration tests: (1) publisher to platform: P3 writes a fixture publication to a disposable
Postgres built from X1's scripts using the F&O runtime role; (2) platform to dashboard: W2 reads it with the dashboard
role and renders W3's screens with the right freshness state; (3) daily operation: one dry-run day from O1 appears on
the deployed dashboard with matching numbers. Out: unit tests inside each repository.

**Expected design:** `tests/integration/` in this repository for (1); a shared fixture publication published as a
versioned artifact the dashboard repository's CI consumes for (2); a recorded manual-plus-script check for (3).

**Acceptance criteria:**
1. Test 1 passes in this repository's CI against a disposable Postgres built from X1's scripts.
2. Test 2 passes in the dashboard repository's CI using this repository's fixture publication of the current contract
   version.
3. Test 3's record shows five numbers matching between the repository records, the database and the screens.

**Test plan:** the three tests.

**Judge verifies:** re-runs tests 1 and 2 and reads test 3's record.

**Depends:** P3, X1, W2, W3, O1 · **Size:** M · **Status:** later

---

## O4. Runbook and documentation

**Repository:** trading

**Description:** As the owner, I want a short runbook (what runs when, what each alert means, what I must do, how to
restart the brake, how to pause a book) and up-to-date README and CLAUDE.md, so that I can operate and question the
desk without reading code.

**Context and why:** CLAUDE.md working rules (plain words, concise); the owner's only written actions are a brake
restart, judge overrides, approvals and pausing (design 7, 8, 12.8).

**Scope.** In: `docs/RUNBOOK.md`, README and CLAUDE.md updates as stories land. Out: design changes.

**Acceptance criteria:**
1. Every alert the code can send has a runbook entry with its meaning and the owner's action (a test compares the
   alert list with the runbook).
2. README commands all run (`--help` test for each).
3. Owner actions (brake restart, override, pause, approve) each have a worked example.

**Test plan:** the alert-list comparison test; command help tests.

**Judge verifies:** follows the runbook for one alert on a test day.

**Depends:** O1, O2 · **Size:** S · **Status:** later
