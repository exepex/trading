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
**Across containers (13 Oct 2026, from E1):** E1's operating-system lock protects one machine only; cloud routines run in separate checkouts. Every account write therefore runs as: pull, write under `AccountLock`, commit, push; if the push is rejected, drop the unpushed local account commit, reset to the new `origin/main` and re-apply the same fills (E1 makes fills idempotent by fill ID; a plain pull merge-conflicts on `cash_ledger.csv`, judge 1). E1's 600-second lock lease can block a retry in the same container inside the fills window: set the lease for E3's timetable, not by default.

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
the deployed dashboard with matching numbers; (4) the stock migration: W6 parity and W7 write continuity pass on the
same disposable server before W5's cutover. Out: unit tests inside each repository.

**Expected design:** `tests/integration/` in this repository for (1); a shared fixture publication published as a
versioned artifact the dashboard repository's CI consumes for (2); a recorded manual-plus-script check for (3).

**Acceptance criteria:**
1. Test 1 passes in this repository's CI against a disposable Postgres built from X1's scripts.
2. Test 2 passes in the dashboard repository's CI using this repository's fixture publication of the current contract
   version.
3. Test 3's record shows five numbers matching between the repository records, the database and the screens.
4. Test 4: W6 parity and W7 one-writer switch, write continuity and rollback, and K3's exactly-once inbox import pass
   together on one disposable Azure-compatible Postgres built from X1's scripts, before W5's cutover.

**Test plan:** the four tests.

**Judge verifies:** re-runs tests 1, 2 and 4 and reads test 3's record.

**Depends:** P3, X1, W2, W3, O1 (W6, W7, K3 for test 4) · **Size:** M · **Status:** later

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

---

## O5. Public-record safety scan

**Repository:** trading

**Description:** As the owner, I want every committed record scanned for credentials, personal data and broker
identifiers, so that the public repository never exposes anything it should not, while numbers and hashes stay
auditable.

**Context and why:** Both repositories are public during development (owner decision, design 13.2 and 13.7); the
dashboard login protects the screens, not committed records. Decision records, packs, role cards, session exports,
forecasts and reports are committed (D3, E2, F1, G3, P2). ChatGPT review 26 (M2): the dashboard payload scan (W4) is
not enough.

**Scope.** In: a scanner and its CI gate over `journal/`, `research/data/quotes/`, `reports/`, `book3/`, `playbook/`,
`agents/` and session exports before they are sent. Out: rewriting git history (if anything is ever found, the
owner decides; credentials are rotated at once).

**Expected design:** `tools/check_records.py`: patterns for tokens and keys (including the names in
`fno/constants.py`), e-mail addresses, phone numbers, Indian PAN and Aadhaar formats, broker client and account
identifiers, and Groww order or account fields; an allow-list for known safe values (the #fno-desk channel ID); runs
in tests and before every commit made by a routine.

**Acceptance criteria:**
1. Planted examples of each pattern in fixture records are all caught; the allow-listed channel ID is not.
2. The daily routine refuses to commit when the scan finds anything and sends an alert naming the file (not the
   value).
3. The scan of the current repository passes.

**Test plan:** fixture tests; a routine dry run with a planted value.

**Judge verifies:** plants a fake token in a record and confirms the routine refuses to commit.

**Known limits (accepted by judge 2, finding 6):** bare 10-digit phone numbers, spaced labels such as "Client Code:",
unlabelled random secrets and old-format Slack IDs are not caught.

**Depends:** - · **Size:** S · **Status:** built; awaiting re-judge (judge 2 findings addressed) (claims: `reviews/claude/response_36_2026-10-13-o5-record-scan.md`)

