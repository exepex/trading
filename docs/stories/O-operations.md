# Epic O: operations

Roles: head of desk, data engineer, risk manager, judge. Goal: the finished product runs every trading day without
the owner doing anything, fails safely and visibly, and is proven to work across repositories (design 9, 13.1 item 10,
13.8). Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## O1. The daily desk routine

**Changed by REPLAN (line 61, issue #76):** the story text is now `docs/stories/O1-daily-run.md` (one daily run:
weather, v4 forecasts, quotes, data checks, desk, card). The earlier text is in this file's history.

**Depends:** E3, E2c, T1, M1, G7, A4, A7 · **Size:** M · **Status:** story text (`reviews/claude/response_165_o1-daily-run.md`)

---

## O2. Failure handling, end to end

**Changed by REPLAN (line 62) and started by the owner on 16 Oct 2026:** the story text is now
`docs/stories/O2-failure-handling.md` (one end-to-end suite over O1's real daily run: Drive, Slack and Groww/NSE
outages, a routine that never starts, a partial run and its rerun, design 9's rows, book isolation). The earlier text
is in this file's history.

**Depends:** O1, E2c, C3, C4, E3, O8 · **Size:** M · **Status:** story text (`reviews/claude/response_203_o2-failure-handling.md`)

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
unlabelled random secrets and old-format Slack IDs are not caught. Added after judge 4: a short all-letter password next to its label
("password: sunshine") or a key in parentheses after its label is not caught; the git hook gates Claude sessions only,
so a push from ChatGPT, Codex or a person's own clone is caught only by CI after the push.

**Depends:** - · **Size:** S · **Status:** done (judge passed, `reviews/judge/judge_4_o5_record_scan_rejudge.md`)


---

## O6. Fetch in GitHub Actions, reason in triggered Claude routines

**Repository:** trading

**Description:** As the owner, I want every scheduled download to run as a free GitHub Actions job that stores raw data
in Google Drive and then triggers the Claude routine that reasons on it, so that AI runs only when new data exists,
every role reuses the same data from Drive, and no AI credit is spent on downloading.

**Context and why:** Owner decisions, 13 Oct 2026 (`docs/DESK_DECISIONS.md`): fetch and reason are separate; GitHub
Actions download raw data into Drive and fire the matching routine through its API trigger; the routine reads from
Drive, reasons and writes results back to Drive (derived area); a publisher's new version triggers a re-run, with old
and new results kept; routines run on the owner's Claude subscription, never on pay-per-use API keys. The current
scheduled routines keep running until the new pipeline is deployed and proven, then they are decommissioned (or kept
once a day as a fallback). Facts checked in Claude Code's routines documentation (13 Oct 2026): `POST
https://api.anthropic.com/v1/claude_code/routines/<trigger id>/fire` with a per-routine bearer token (made by the owner
in the web page, shown once), headers `anthropic-beta: experimental-cc-routine-2026-04-01` and `anthropic-version:
2023-06-01`, optional `{"text": ...}` delivered to the run as untrusted data; 30 fires per hour per routine; research
preview, so the shape may change.

**Scope.** In:
- a small shared pipeline layer reused by every download job (A12's filings job included; agree the boundary with the
  A12 builder by reading its code, never by rewriting it): run summary and progress manifest in Drive, one-line
  run report to #fno-desk, and a `RoutineTrigger` interface with a `/fire` adapter (wired in a composition root) that
  sends only a pointer (dataset, Drive path, batch id, version), never data;
- an idempotent "processed" record in Drive per batch and version, so a routine never processes the same version
  twice, and a new version is processed again;
- migrate the F&O routines that need no AI to plain Actions: the 3 pm quote recorder (start early, about 14:20 IST,
  and wait, since Actions schedules can start late; first check whether NSE's public option data can replace Groww so
  no broker key goes into GitHub; if Groww is still needed, stop and ask the owner), the daily participant-OI release
  check and the monthly participant-OI sweep. Each keeps its current commands, outputs and alerts;
- one example reasoning routine wired end to end (a dry-run routine that reads the pointer, opens the files from Drive,
  writes a small derived summary and its processed record), to prove the trigger path;
- the owner checklist: which tokens to generate, which secrets to add, how to switch off each old routine.

Out: any change to the stock tool's repository (paused; its routines move later with the owner's go-ahead); deleting
or disabling any existing routine (the owner decides after the new path has run cleanly for 5 sessions).

**Acceptance criteria:**
1. Each migrated job runs on schedule in GitHub Actions and gives the same outputs as its routine on the same day
   (the 3 pm recorder for at least 3 sessions side by side; the participant-OI check for at least 3).
2. A download that finds new data fires its routine exactly once per batch and version; no new data fires nothing; a
   republished file fires again (tests with a fake trigger; one real fire of the dry-run routine).
3. A failed fire, an expired token or a refused Drive upload posts one clear line to #fno-desk and never fails
   silently (tests).
4. No secret value in any file or log (record scan; a test greps the output). No broker key in GitHub unless the owner
   approved it.
5. The pipeline layer sits behind interfaces with concrete classes wired only in composition roots; no file or class
   over 350 lines.

**Judge verifies:** compares a migrated job's outputs with the routine's for the same day; plants a duplicate batch and
a republished file; reads the Actions logs for secrets.

**Depends:** A9, A11, A12 · **Size:** L · **Status:** awaiting judge (`reviews/claude/response_58_o6-fetch-and-trigger.md`; 3 pm recorder on NSE data per the owner's choice (a), side by side)
