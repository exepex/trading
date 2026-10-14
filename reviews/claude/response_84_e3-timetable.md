# Response 84: story E3, the daily timetable: builder's claims

Builder session, 14 Oct 2026. Branch `story/e3-timetable`, from `main` e3506ec (C3 merged). Judge first; nothing goes
to `main`.

**Verdict in one line:** `DailyRun.run(day)` walks one fixed timetable:
- packs → decisions read at a hard deadline → one execution capture (second recorder capture, its own committed
  capture record, one common retry) → fills (C3 data gate, C4 seam, D3's timing rule) → exits.
- Each step is logged to `journal/runs/<date>.json` and committed. A restart repeats nothing.
- Tested end to end over 5 simulated days; 24 of 24 mutations caught.
- **Not live yet:** each book's orders and exit rules come from E5 (F5/F6 for the AI books), and C4 is a seam.

## 1. The design (`fno/desk/`, wired in `fno/desk/daily_wiring.py`)

| Part | What |
|---|---|
| `timetable.py` | `desk.timetable` in `config.yaml` (new allowed key `desk`), **proposed until S1**: pack 14:58 (retried until 15:10), deadline 15:12, execution snapshot 15:15, fills by 15:20, account lock lease 60 s. Refused if a time is missing, out of order, or the lease does not fit the fills window. |
| `daily_run.py` | `DailyRun.run(day)`. A day that is not a recorded session (A7: closed, or a muhurat-only evening) writes one `skipped` step and nothing else. Otherwise it runs the steps below in order, each at its time, each skipped if already in the run log. |
| `daily_steps.py` | The steps. Each reads what earlier steps committed (pack file, decision runs, capture records, accounts), never memory, so a restart continues where it stopped. |
| `daily_ports.py` | The seams: `Packs`, `DecisionSource`, `OrderBuilder` (E5/F5/F6), `ExecutionCapture`, `ValidityGate` (C4), `ExitRules` (E5), `AccountSync`, `Committer`, `VersionKeeper`, `Waiter`. |
| `run_log.py` | `journal/runs/<date>.json`: each step's start, end, inputs and result, written atomically and committed after the step. A step is never recorded twice. |
| `packs.py` | `WrittenPacks`: E2's common pack plus Book 1's private pack, after a `git pull`, so another container's 3 pm snapshot is seen (judge 72). `desk pack` now uses it too (one place). |
| `committed_decisions.py` | `D3CommittedDecisions`: a book's latest D3 run whose `records.sha256` was committed **before the deadline** (git's commit time). Later runs are never read, so a slow book cannot join late. |
| `no_decision.py` | `journal/<book>/decisions/<date>/no_decision.json`, the committed "no decision (late)" record, written once. |
| `execution_capture.py` | `RecorderExecutionCapture`: A4's recorder takes a **second capture** (`QuoteSnapshotRecorder.capture()`, new and never canonical) with its own ID. Its **capture record** (ID, times, quote-file and sidecar SHA-256) goes to `journal/execution/<date>/<id>.json` and is committed with the quote files. `CommittedExecutionSchedule` gives C3 the day's latest record and the window 15:15-15:20, so C3's `SnapshotMatchesRecord` checks the execution capture itself (judge 81 ruling 2). |
| `git_sync.py` | `GitCommitter` (pull, commit, push, retried) and `GitAccountSync` (E1's rule: pull, write under `AccountLock` with the timetable's lease, commit, push; **on a rejected push: reset to the new `origin/<branch>` and apply the same fills again**). |
| `book_versions.py` | `Book1Versions` (judge 80 follow-up a), see section 2. |

**Order of a day:** `versions` → `pack` → `decisions` (at 15:12) → `snapshot` (at 15:15) → `fills` → `exits`.
- **Fills:**
  - no valid snapshot means no new risk for any book;
  - each order needs a completed C4 pass (`ValidityGate.problems` empty);
  - C3's gate on the order's legs;
  - D3's rule checked again against the snapshot actually taken: a commit not before its start is late, never filled;
  - then E4's entry under the account sync.
- **Exits:** every book is reviewed whatever happened before. With an unreadable snapshot, C3's alert names the exits
  that are due.

**C3 change (one line, tested):** the data gate now skips an alert whose text it has already sent, because the run checks
the same data at the snapshot, each fill and each book's exits.

## 2. Judge 80 follow-up (a): Book 1 is never unscored by accident

`Book1Versions.keep(day)` runs first each day, before any decision is committed.
- It compares Book 1's served playbook digest (`playbook_digest(playbook, day)`: what D3 records as `served.playbook`)
  with the active D6 version.
- Any approval (counts from the next session), pause or retirement (from the same day) changes that digest. When it
  changes, it registers and commits `<version>+<YYYYMMDD>` starting that day, with the other components kept.
- That commit lands before the day's decisions, as D6 requires ("strictly before").
- It deliberately does **not**:
  - create Book 1's first version (the owner's act, D6);
  - renew a change to any other component, such as the config. That stays unscored until the owner registers it,
    and the line says so;
  - register two versions on one day: D6 forbids it. A pause and a resume on the same day give "NOT renewed …
    the owner registers it" (tested).
- Why here and not in D1's status change: the digest is a function of the *day* (an approval dated D changes the
  digest only from D+1). The daily run is the one place that runs before each day's decisions. Reasoning only.

## 3. Across containers and the lock lease

- Account writes follow E1's rule exactly. The test uses two real checkouts of one origin: container A pushes first,
  container B's push is rejected, B resets to the new origin and applies the same fill again. The result is both fills
  once each, and the rejected commit is gone.
- **Risk to know:** the reset (`git reset --hard`) discards that checkout's unpushed work. The daily run must run in
  its own routine checkout, never a person's. This is stated in `git_sync.py`.
- Lease 60 s: one book's write takes seconds, and the 15:15-15:20 window must allow a crashed writer's retry.
  Proposed, not measured.

## 4. Not done here, said plainly

1. **`OrderBuilder` and `ExitRules` are seams with no real implementation.**
   - Turning a D3 run into `EntryOrder`s (with C2's decision) and naming each trade's exit rules is each book's part:
     E5 for Book 1, F5/F6 for the AI books.
   - `build_daily_run` takes them as arguments, so the run cannot go live until E5 exists. For the same reason there
     is no `desk run` command yet.
2. **C4 is the `ValidityGate` seam**, tested per book with a fake that passes or fails. Wiring the real C4 is one line
   in `daily_wiring.py` once it merges.
3. **The AI books' receipt and promotion deadlines** (F1) are those books' own. Here every book is held to the same
   decision deadline on its committed D3 run.
4. **Times are proposed.**
   - The pack step tries from 14:58 until 15:10 (the recorder's window end).
   - Book 1 then has until 15:12 to decide, which is tight if the canonical snapshot lands late.
   - S1 calibrates and freezes the times from measured run times.
5. **Today's real two-spot gap** (C3, judge 81) is still to be measured on the first real capture. It is not part of
   this story.

## 5. Evidence

- `tests/timetable/test_daily_run.py`, end to end over 5 simulated days, with the real E4 desks, C3 gate, capture
  records and run log, and fakes only at the seams:
  - **normal:** both books fill at one snapshot ID and hash (criterion 2), and the commits come in timetable order;
  - **slow book:** committed 15:13, so "no decision (late)" is committed, and the other book fills at 15:15 unchanged
    (criterion 1);
  - **failed snapshot:** two attempts, no new risk, and the due time exit still closes (criterion 3);
  - **holiday** (20 Oct) and a **muhurat-only evening** (8 Nov): nothing runs (criterion 4);
  - **restart:** the run is killed after the fills and restarted: no second capture, no second fill (criterion 5);
  - **week of run files:** every step has times, inputs and result; decisions come before the snapshot, and the
    snapshot before the fills (criterion 6);
  - **C4 per book:** a decision without a C4 pass never fills, and the other book does (criterion 7);
  - **retry:** a successful common retry fills every book at the retry's capture;
  - **clock skew:** a decision whose commit time is not before the capture's start is late at the fill.
- `tests/timetable/test_parts.py`:
  - the timetable's checks;
  - the recorder's second capture is never canonical, even with no 3 pm canonical;
  - the pack's retry until 15:10;
  - D3 runs read at the deadline (the latest timely one; one at exactly the deadline is late);
  - the written-once late record;
  - Book 1's version keeping.
- `tests/timetable/test_git_sync.py`: the rejected push resets and re-applies on real git, and the committer pulls,
  commits and pushes.
- Mutations (`python -B`, caches cleared): **24 of 24 caught**, plus the C3 dedupe plant.
  - The first run left 4 survivors, each a missing test: a muhurat day, the retry's capture, a step recorded twice,
    and a plant aimed at the wrong line of the recorder. Tests were added and the plant re-aimed.

## Addendum 1: judge 82 (FAIL), fixed

Both must-fixes were checked against the code and are right:
- the fill step asked the decision source again at fill time;
- `GitAccountSync` reset with no look at what else the checkout held.

1. **A late book no longer fills.**
   - **On time is what the collector observes:** the decisions step pulls once at the deadline and records the origin
     commit it saw. For each book it records the visible run's ID, its holding commit and its committer time.
   - The committer time before the deadline stays as the second check, and D3's rule against the actual snapshot start
     as the third, at the fill.
   - **Fills read only those records:** `DecisionSource.recorded(book, day, run_id, commit)`, refused if that run is not
     held by that commit. A book recorded late is never filled.
   - **Restart after the deadline:** if the decisions step starts more than 30 s after the deadline, it fails closed and
     every book is late.
   - Tests:
     - judge 82's probe: committed 15:11:50, visible from 15:13, so late and never filled;
     - a newer run pushed after the deadline never replaces the recorded one;
     - a restart at 15:14 is all late, with no fills and the exits still run.
2. **A reset never destroys other work.** "Dedicated checkout" is now a check:
   - Every account write is refused, with an alert, unless the tracked worktree is clean and nothing is unpushed (after
     a fetch).
   - Before a reset it confirms that exactly one commit, this write's own, is ahead of the commit it pulled. Otherwise
     it stops and alerts (`CheckoutNotDedicated`).
   - Tests on real git:
     - an unpushed decision commit is kept, and so is an uncommitted tracked edit;
     - other work committed during the write stops the reset;
     - the clean case still resets and applies again.
3. **Rulings applied:**
   - automatic `Book1Versions` registration is kept as built;
   - the story status now says "built, not live" (no `desk run` command, no routine, no E5, no C4 yet).

Mutations (`python -B`, caches cleared): **31 of 31 caught**. The new plants:
- fills asking the source again;
- a late book filled;
- a restart not failing closed;
- no observation;
- the recorded commit not checked;
- a dirty checkout allowed;
- a reset over other commits;
- tracked edits ignored.

The first run left the "fills ask again" plant alive. My fake had frozen visibility at the observation, while a real
checkout sees later pushes. The fake was made realistic and a test added for the case where it matters: a book whose
newer run lands after the deadline.

## Addendum 2: judge 83 ruling (C4 at the fill)

- The fill's `ValidityGate` is now `RecordedC4Pass` (`fno/desk/recorded_c4.py`), wired in `daily_wiring.py`, so C4 is
  no longer a seam passed in.
- It reads the committed D3 record's `validity.c4`, in C4's own format (`{"mode", "ok", "checks": [...]}`), from the run
  the decisions step recorded (`CommittedDecision.run`).
- An order fills only if all of these hold:
  - its record exists (by the order's `decision_id` = the record's opportunity ID);
  - the run's files still match their committed `records.sha256`;
  - the C4 report has `ok: true` and at least one check.
- It takes no market, snapshot or validator, so C4 can never be re-run at the 15:15 capture. Those quotes differ from
  the decision's and would fail every leg's price check.
- **Requirement on E5 (and F5/F6):** each `EntryOrder.decision_id` must be its D3 record's opportunity ID. This is
  stated in the module.
- Tests (`tests/timetable/test_recorded_c4.py`, 7 cases):
  - a recorded pass fills;
  - none of these fill: null `c4`, empty checks, `ok: false`, a non-boolean `ok`, a record hand-edited from fail to
    pass, a missing record, or no run folder;
  - the gate's signature takes nothing but the decision and the order.
- Plants caught: 4 of 4 (failed pass ignored, edit check off, empty checks accepted, missing record ignored).
- Written into story E3, criterion 7.

## 6. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: the
results are in the commit message and the message to the orchestrator.
