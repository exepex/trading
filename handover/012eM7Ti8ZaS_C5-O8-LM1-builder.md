# Handover: builder 012eM7Ti8ZaS (C5, E1b, O8, LM1, C5d)

Written 21 Oct 2026 (owner's handover order). Everything is committed and pushed; nothing is only in the container.

## (a) Identity

| Item | Value |
|---|---|
| Session | `session_012eM7Ti8ZaSVowgyMkgoGmM` |
| Role | Builder under the orchestrator (`session_01VG1RqxLFUVdvvPuMRYZtDH`) |
| Stories and areas owned | C5 (risk buckets and caps in C2 and C4), C5b, C5c, C5d, E1b (capital top-up), O8, O8b, O8c (daily health check, `fno/health/`), LM1 (position monitor, `fno/monitor/`; handed over from 01XFXpbk on 16 Oct) |
| Reviewer for | O10's changes to `fno/health/` (O10 builder `session_013YJ5gjXdxtFu6mwXP6v48N`) |

**Branches (head SHAs on GitHub):**

| Branch | Head | What |
|---|---|---|
| `story/lm1-code` | see the commit adding this file | LM1 rounds 1 and 2a, the judge 264 fix, A16's port merged in; this handover |
| `story/lm1-round1` | `97cfd132` | LM1 round 1 plus the judge 264 fix only (the judged part, without 2a) |
| `story/c5d-nse-symbols` | `09b3b412` | C5d, judge 404 PASS, not merged |
| `story/o8c-calendar-stop-line` | `7fadc85f` | merged (`72742726`) |

## (b) Done and merged to main

| Story | Merge or commit on main | Judge |
|---|---|---|
| C5 (buckets, Rs 20 lakh account, books and Manual profiles, C4 caps, one-session margin age) | `2da60b2e`..`1cccd7e0` (15 Oct) | judge 105 and addenda, PASS |
| C5b (a brake restart cites the owner's decision row, C2 and C4) | `df56b693`, `1b9b7b30` | PASS (claims response 135) |
| E1b (capital top-up Rs 5 lakh to Rs 20 lakh per book; the real run is data commit `400d6921`) | `725b2491`, `ee8ba24c`, `4fac8983`, `dde94700` | judge 110 and addenda, PASS |
| O8 (daily health check, 17:51 IST, `fno/health/`, `.github/workflows/health-check.yml`) | `1a531830`, `a8024d8f` | judge 164 (text), judge 170 (code) PASS |
| O8b (NSE calendar horizon line once; posted-gated failure alert) | `7881bb24` (merge of `9232281d`) | judge 240 add. 1 PASS |
| O8c (one named line when a command stops on NSE's calendar; index-closes one line per failing run) | `72742726` | judge 246 add. 1 PASS |
| C5c (C4 names the calendar when it cannot count a margin's age) | `38c0130b` | judge 243 PASS |

## (c) Done but not merged

1. **C5d: NSE contract IDs map to their underlying in C5's (C2) and C4's buckets.**
   - Branch `story/c5d-nse-symbols` at `09b3b412`. Claims: `reviews/claude/response_279_c5d-nse-symbols.md`.
   - **Judge 404 PASS** (Judge D, verdict on main at `efe4fa98`). Its trial merge passed 8,016 tests; the only
     failures were main's 2 known ones (g7_series and forecast_history_page), not C5d's.
   - **Merge conditions:**
     - the full gates pass on the exact pushed tree;
     - the S1 text owner (`session_0185gR5DmoDh2zBAvgRU4CEB`) agrees the one PROTOCOL.md line. That line adds
       `fno/contract_symbols.py` to frozen_files' "Score-time computation" bullet; S1's scoring-closure test
       requires it. **No answer from S1's owner had arrived.**
   - By agreement (16 Oct), the orchestrator merges; this builder does not.
2. **LM1 round 1 plus the judge 264 fix.**
   - **Judge 264 add. 1 PASS** (Judge B, `session_01YEVAEMygZa9VgBATxsZrXQ`, verdict on main at `93973e19`).
   - Available alone on `story/lm1-round1` at `97cfd132`.
   - The orchestrator chose to merge LM1 **once**, after round 2a's verdict (see (d)).

## (d) In progress: LM1 round 2a (and 2b, not started)

- **Branch:** `story/lm1-code`. Code heads before this handover:
  - `1d38f6a4`: a test with two broken checks of different error types;
  - `6f39daa8`: local-first alert history;
  - `341c2230`: `MONITOR_TIME_LIMIT_SECONDS = 90.0`.
- **Claims:** `reviews/claude/response_248_lm1-thresholds.md`, sections "Round 1 code claims", "The owner's decision
  applied", "Judge 264 (round 1 FAIL) addressed", "Round 2a code claims" and "Round 2a addition".
- **What 2a is:** in `fno/monitor/`:
  - `MonitorObserver` (behind A16's `MarkObserver`);
  - `MarkReader` (A16's ledger, NSE's archived close);
  - `NoOpenPositions` (the position port; true today);
  - private alert records in Drive's `paper` area (`AlertRecords` over `DriveIndexStore`);
  - public mark rows (the one-handling marker) and the heartbeat, under `research/data/intraday/monitor/`;
  - `MonitorSilence`, and the `monitor_alerts()` seam for O1's `ReportedAlerts`;
  - the `.gitignore` line `journal/monitor/`.
- **Not wired into A16's recorder:** the story's start condition is the first paper or shadow position.
- **Gates at 341c2230:** monitor tests 94 passed. The full suite passed 7,404 at `6f39daa8`. Ruff and check_imports
  were clean.
- **Agreed order (orchestrator, 16 Oct):**
  1. main green;
  2. A16's observer port merged (**now done**: `fno/intraday/observer.py` is on main);
  3. merge main into `story/lm1-code`, run the full gates, send round 2a to Judge B;
  4. after the PASS, the orchestrator merges the whole branch.
- **Next concrete step:** step 3. `story/lm1-code` has not had main merged since 16 Oct; expect conflicts in
  `fno/intraday/` (A16's port landed on main in its final form) and in `reviews/claude/README.md`.
- **Orchestrator OKs already given for 2a** (16 Oct, reasoning only):
  - the path `research/data/intraday/monitor/`: it lets the rows ride in A16's own commit;
  - `DriveIndexStore` over the paper area instead of E2c's `PrivateFiles`, which imports the desk's fill and entry
    modules.
- **Round 2b (not started): the real position adapter.** It needs:
  - E4's net-if-closed extracted as a pure function (today private in `ExitDesk._net_if_closed`; an E4 change);
  - each trade's exit rules from the playbook;
  - C2's `HeldMaxLoss` for the maximum loss at entry.

  Start it only when the first paper position is expected, with the E4 and E3 owners' agreement.
- **Go-live (three one-liners in A16's files, each agreed with the A16 owner `session_01VK88LxJvV1Gi7Wbr3D4fzp`):**
  1. in `_observers()` of `fno/intraday/wiring.py`, `(build_monitor_observer(cfg, folder), MONITOR_TIME_LIMIT_SECONDS)`
     first in the `ObserverGroup` list;
  2. `"monitor/"` added to A16's `OWNED_PATHS`;
  3. `heartbeat_check` also asks `build_monitor_silence(folder, PublishedHeartbeat(...))`.

## (e) Reviews and judging

- **O10's `fno/health/` changes** (`story/o10-part2-freshness-trial`): approved by me at `7966c4f0` after one fix.
  - The fix: a transient `unknown` waits until the session's last run in the window, then counts as a problem.
  - My other conditions were met:
    - margins matched by the `as_of` header, with a position-aware search key;
    - the margins deadline is the desk timetable's pack time, not a typed 09:15;
    - `MARKET_ARCHIVE_BY` 15:00 next day, measured (some evidence: 2 pushes);
    - a session missing from `trial_days.csv` breaks the streak;
    - no writes on a dry run or a broken check;
    - sessions with no live check are not judged.
  - Judge F holds it.
- **A16's ObserverGroup** (`story/a16-observer-group`, `e90551d8` then `63d8de75`): I asked for per-member time
  limits. The A16 owner did it: per-member limits, a 300 s cap, LM1 90 s, A21 10 s. Judge 405 is claimed on main;
  its verdict was not seen.
- **A21** (01XFXpbk): my four conditions for the group are in A21's text (`94cda4a8`).
- **E2d's `trade_marks` in O8's `DESK_RUN_STEPS`:** no objection, told to Judge B. Condition: the desk's O8
  `live_from` must be on or after E2d's merge date, or older run logs read as missed (go-live checklist, noted by
  the orchestrator).

## (f) Open questions, waits and agreements

1. **S1 text owner (0185gR5D):** agree the PROTOCOL.md line for C5d (above), or carry it in the next S1 edit. No
   answer received.
2. **A14c's red tests on main (16 Oct):** the A14c stress-factor data commit `df9bfaff` added factor 2.1 against
   tests pinned to the seed 1.45. Reported to the orchestrator (A14/A14c owner's to fix). Also asked: is 2.1
   applied or held for the owner? A factor jump from 1.45 to 2.1 changes every margin check.
3. **The health check's first scheduled run** was expected on 16 Oct at 12:21 UTC (17:51 IST). No run had been
   recorded at 10:59 UTC that day because the workflow reached main after 15 Oct's slot. Verify that
   `health-check.yml` has run since then.
4. **Agreed with the A16 owner:**
   - LM1 takes "last good mark" from A16's ledger;
   - a missed mark arrives with document None;
   - LM1 runs first in `ObserverGroup` with 90 s;
   - a timed-out member's files go up with the next commit.
5. **Agreed with O10:** O10 extends O8's checks (one checker); I review every `fno/health/` diff before the judge.
6. **Owner's LM1 thresholds:** decided 16 Oct (DESK_DECISIONS `4186a4ce`), in `config.yaml` `monitor`, version
   `owner-2026-10-16`. The owner was told (judge 264's request) that "exit rule reached" alerts once per session,
   not hourly.

## (g) Risks, known bugs and gaps

- **LM1 is not wired:** with a first paper position open, nothing watches it intraday until round 2b and go-live
  are done.
- **LM1 round 2a assumptions to recheck at go-live:**
  - Drive's paper area is reachable from the routine;
  - the recorder runs where `FNO_SLACK_BOT_TOKEN` is set;
  - NSE's previous close is archived before 09:15 (the index-close job runs at 21:11 IST with retries at 07:41 and
    11:41). When it is late, the big-move check cannot run and the mark row says `previous_close_known False`.
- **Frozen `panel-days.yml`** (protocol v3) stays silent on an append calendar stop after a successful librarian.
  The health check covers it; the fix needs O9 or a new protocol version.
- **`nse-margins` gives 2 lines in 2027** (A14's design, accepted). The calendar ends on 31 Dec 2026: NSE's 2027
  holiday rows must be added (the O8b horizon line fires from 17 Nov 2026).
- **F1's 10-page activity-log cap** can make O8 push times `unknown`.
- **My own errors this period, all corrected:**
  - a wrong 13 Oct gap claim (I printed only head and tail of a file; withdrawn);
  - a wrong SHA sent to Judge B (corrected at once);
  - response 270 used before O12 (renumbered to 279);
  - a near-overwrite of `docs/WORK_REGISTER.md` from a branch copy (caught in the diff, not pushed).

  Lesson: read whole files, check SHAs, claim numbers with `tools/claim_number.py`, and add register rows by line,
  never by copying the file.

## (h) The successor's first three actions

1. Ask the orchestrator (or its successor) whether S1's owner agreed C5d's PROTOCOL.md line. If yes, ask the
   orchestrator to merge `story/c5d-nse-symbols` (`09b3b412`, judge 404 PASS) after a full gate run on the merged
   tree.
2. On `story/lm1-code`: `git merge origin/main`, resolve the conflicts (A16's final port in `fno/intraday/`,
   `reviews/claude/README.md`), then run `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto`, `ruff check fno
   tests tools`, `ruff format --check fno tests tools`, `python tools/check_imports.py` and
   `python tools/check_numbers.py`. Then send round 2a to Judge B with the claims sections named in (d).
3. Check on GitHub that `health-check.yml` has scheduled runs since 16 Oct and that its messages look right. Then
   confirm with O10's builder that judge F's verdict on `story/o10-part2-freshness-trial` landed.
