# Story PROC1: the owner's process and scope cuts (22 Oct 2026)

**Why.** The owner accepted the cut-list review (response 318; DESK_DECISIONS "Cut-list accepted"). In 11 days, 62% of
recent commits were process (judge files, docs, response files, logs, number claims), 72 judge reports needed 3 or more
rounds, and the paper desk ran daily with 0 trades. The main steward builds the cuts, in small changes.

**Part 1, today (this change; judged under the old lanes, as the last such change).**
- `docs/JUDGE.md` rewritten: lane 1 only for money, risk, fills, exits, forecast and score records, frozen files,
  secrets and outside services (and their schedules and workflows) and the privacy rule; everything else outside lane
  3 is lane 2; two judges (a code judge, a lane-2 auditor); a fixed 40-60 line verdict template; at most two rounds,
  then the owner decides; builder claims in the story file's Claims section; quality rule 9 (ChatGPT) paused; the
  merge procedure as decided on 21 Oct (one full run per merge).
- `CLAUDE.md`: the lanes as above; the ChatGPT loop paused and claims in the story file; logs as owner quotes plus
  decisions; the composition-root list replaced by one rule (every `wiring.py` names what it wires in its docstring;
  all 55 do).
- `AGENTS.md`: the ChatGPT loop paused, and how it resumes.
- `number-alert.yml`: the hourly cron removed; the push alert and the manual run stay.

**Later parts (from Mon 26 Oct, after the v4 freeze's three clean runs; each its own small change).**
2. Cron cuts: participant-OI watch 28 to 3 runs a day, margins 4 to 1, circulars 15 to 2; the AI books' daily runs
   stopped (Books 2 and 3 stay paused, not closed).
3. Docs archive: about 7.6k lines of stale docs to `docs/archive/` with a README (response 318, section 6).
4. The paper desk's daily steps skipped until a version is registered: built by the O1/O2 builder
   (session_014zYLf18PgCzR7YoHs1X5Dp), coordinated here.
5. Numbering removed once each story has one judge file and one story file named by its story id.

**Unchanged (hard lines).** No orders; secrets never in files; the record scan; privacy (public repository);
write-once data with receipts; frozen files only at the next protocol version; the code judge for everything in lane 1.

**Criteria (part 1).**
1. `docs/JUDGE.md`, `CLAUDE.md` and `AGENTS.md` say each rule of decision 294's item 1, and nothing contradicts it.
2. No routine section changes (the routine tests read them), and the full suite stays green.
3. `number-alert.yml` has no schedule. `tests/numbering/test_tools.py` fails if a schedule or cron line comes back.

## Claims

- Part 1: full suite on the branch (main 616acea3 plus this change) 9,812 passed, 16 xfailed; ruff, check_imports and
  the record scan clean; check_numbers is clean on `main` (the branch adds no numbered file).
- Criterion 3's broken-code proof: putting `schedule: - cron: "17 * * * *"` back fails
  `test_the_alert_workflow_runs_on_every_push_with_the_push_baseline_and_no_schedule` (1 failed, 6 passed).
- Criterion 2: no line of the three routine sections changed (`git diff` shows changes only in the "How to work with
  the owner", "Keep a conversation log", "Branch" and "Code" sections of CLAUDE.md).
- Two readings of decision 294 the judge should check. (a) "Lane 1 only for ..." means every change outside those
  areas, rule documents and new stories included, is lane 2. (b) "Outside services" includes the schedules and
  workflows that call them (a workflow posting to Slack stays lane 1; CI such as `checks.yml` moves to lane 2).
- JUDGE.md shrank from 160 to 108 lines and CLAUDE.md from 275 to 222.
