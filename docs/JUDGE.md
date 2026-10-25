# The judge

An independent, honest reviewer. It never writes code and never edits files other than its verdict. It trusts
nothing it has not checked itself. Process as cut by the owner on 22 Oct 2026 (DESK_DECISIONS "Cut-list accepted",
response 318).

## Lanes: what each change needs

Which review a change needs is set by what it can damage, not by its size. When the builder or the orchestrator is
unsure, the change is lane 1.

| Lane | Covers | Review |
|---|---|---|
| 1 | Money and risk (margins, funds, limits), fills, exits, anything that decides a trade; forecast, score and evaluation records; frozen files; secrets; outside services (Slack, Groww, Drive, NSE), including the schedules and workflows that call them; the dashboard's privacy rule; rows of `journal/<book>/owner_overrides.csv` | The code judge's PASS on the branch before merge |
| 2 | Everything else that is not lane 3: tools, CI, tests, docs, rule documents and new stories outside lane 1, when they change no record | The orchestrator re-runs the gates and compares the claims with the diff, then it merges; the lane-2 auditor checks that day's lane-2 merges once |
| 3 | Judge files, conversation logs, decision and status rows (a decision row only when it quotes the owner), number claims (`numbers/`), data commits by scheduled jobs (their own output paths only; data edited by hand is lane 1) | None |

- A lane-2 merge's commit message starts "Lane 2:" and names the branch tip, the claims and the orchestrator's test
  count. The audit covers every commit on `main` since the last audited one; its range and verdict go in the judge
  README. A lane-2 correctness FAIL is reverted at once with `git revert`, then fixed on a branch; a docs or test-only
  FAIL is fixed in place, first.
- Deleting, skipping or loosening a test in a lane-1 area is lane 1. The auditor may move any kind of change into
  lane 1 when its audit finds problems there.
- **Rule-document guard** (owner, 22 Oct 2026; DESK_DECISIONS "Rule-document guard"): a change to a rule document
  (e.g. `CLAUDE.md`, `AGENTS.md`, this file, owner checklists, protocol and freeze documents) is lane 2, except that
  one which narrows lane 1 or touches a hard line (no orders, secrets, privacy, write-once data, frozen files) stays
  lane 1 and needs the code judge's PASS.
- The dashboard's own lane-1 paths are listed in its `CLAUDE.md`.

## Sessions, models and roles (owner, 25 Oct 2026; story AG1)

Owner, 25 Oct 2026: "All the implementer agents and executor agents will use Sonnet 5.5 model, while the reviewer
agent and the judge agents will use Opus 5.5 model. And each implementer and judge, they will have their own session.
Do not run them as subtasks in one single session. Keep them separate and in their independent sessions. And you act
as the coordinator of those sessions."

This section owns the rule; `CLAUDE.md` and `AGENTS.md` link here.

- **Models:** builders, implementers and executors run on Sonnet 5.5; reviewers and judges on Opus 5.5. Executors are
  the orchestrator-created sessions that carry out a task (a build, a run, a clean-up step). Scheduled routines are not
  these: each keeps its registered model (the Book 2 and 3 routines run Opus 5.5, `F1-G5-owner-checklist.md`; another
  model makes every day "model_mismatch"). Changing a routine's model is the owner's decision.
- **One session each:** every builder and every judge (and reviewer) is its own separate, trackable session, created
  by the orchestrator. Never a subtask or subagent inside another session, and a session never judges its own work.
- **The orchestrator coordinates:** it creates the sessions, names each story's judge or judges, and decides nothing
  that is the owner's. Each session reports its result to it, plus any question that waits for the owner's decision.
- **Direct contact:** sessions message each other with the `claude-code-remote` `send_message` tool, without the
  orchestrator. A builder hands its work (branch, SHA, files) to its judge directly; the judge answers the builder
  directly; the orchestrator gets the result.
- **Judges are independent, unbiased, honest and transparent:** one **code judge** for lane 1 and one **lane-2
  auditor**, each a separate session that did not build what it judges and shares no context with the builder. Where
  two judges review one change, the second does not read the first's verdict before writing its own.
- **Removals and clean-ups need two independent judges** (owner, 25 Oct 2026: "every removal and cleanup needs to be
  reviewed thoroughly by a judge and independent judge"): any change that deletes or retires code, data, documents or
  rules merges only after both PASS, each with its own judge file and the two-round limit below. This overrides the
  lane table's review column and the one-judge default of "Other lane-1 changes" below. Out of scope, as routine
  upkeep and not removals: a scheduled job's own data paths, conversation logs, judge files, number claims, and
  register rows deleted under the Work Register's own rule. Hand-deleting recorded data is a removal.

## For each lane-1 story

1. Read the story in `docs/stories/`, including its **Claims** section (the builder's claims live there, updated each
   round, not in separate response files).
2. Read the diff (`git diff <base>..HEAD`) and every changed file in full where needed.
3. For every acceptance criterion: find the code and the test, and run what can be run (tests, ruff, the checks, CLI
   commands, small scripts). MET only with your own evidence (file:line, command output); unverified is NOT MET.
4. Hunt for what was not claimed: bugs, edge cases (holidays, special sessions, empty data, missing credentials,
   network failure, time zones), anything that could enlarge a trade, bypass a limit or invent a price, look-ahead,
   secrets, dead code, misleading docs, tests that pass without testing the claim. Plant your own mutations.
5. Check `CLAUDE.md`'s engineering standards (a file or class over 350 lines is a should-fix at least).
6. Verdict: PASS, or FAIL with numbered findings (blocking / should fix / minor), each with evidence and the fix
   expected. A story passes only with no blocking and no should-fix findings left.

## The verdict file: a fixed template, 40-60 lines

`reviews/judge/judge_<n>_<story>.md` (number claimed with `python tools/claim_number.py judge-report <slug> --session
<id>`; a later round is a `## Addendum <k>` in the same file, claimed with `judge-addendum <label> --report
<n>`), indexed in `reviews/judge/README.md`:

1. Title: story, branch, SHA. One line: PASS or FAIL, lane.
2. Criteria: one row each, MET / NOT MET / PARTLY, with your evidence in a few words.
3. Findings (FAIL only): numbered, severity, evidence, fix expected.
4. Plants: how many you planted, how many the tests caught, and any survivor.
5. Notes (not findings), if any.

Quote a builder claim only when it is wrong. No praise, no restating the story.

## Rounds: at most two

1. On a FAIL the builder fixes each finding, with its proof (commit, test, command output), or pushes back with
   evidence that the criterion is already met. "I disagree" without evidence is not a pushback.
2. The judge re-judges once, in an addendum: each fix or pushback is accepted or rejected, with its own evidence. A
   pushback is accepted only when the judge reproduces the proof.
3. **After two rounds, the owner decides** (owner, 22 Oct 2026). The orchestrator puts both sides' evidence to the
   owner; no third round.
4. On PASS the builder merges under the merge procedure below and marks its register row done.

## Two judges for money pieces (owner, 22 Oct 2026)

A lane-1 change that touches money, limits, fills, exits or the safety laws is judged by **two different judges**,
each independently, each with its own judge file and its own two-round limit; it merges only after **both** PASS. If
the two disagree after their rounds, the owner decides. Other lane-1 changes keep one judge. The orchestrator names
the second judge when it routes the change.

## Quality rules for every lane-1 story (owner, 15 Oct 2026: "rules yes")

1. **Story text first**, pushed alone and checked by the judge against the design and the owner's decisions before
   code starts.
2. **Gap list:** each requirement of the design is covered by a named criterion or listed out of scope with its reason;
   a requirement in neither list is a blocking finding.
3. **Builder self-review:** a review of the diff by a separate reviewer session (Opus 5.5, created by the
   orchestrator at the builder's request and contacted directly); the Claims section says what
   it found and
   what was fixed or why not.
4. **Broken-code proof:** each criterion names its code and a test that fails when that code is broken on purpose. The
   judge still plants its own.
5. **Good, bad, boundary and empty cases** for each criterion.
6. **Real output sample** in the Claims section, made by the committed code in a dry run or a test, within the privacy
   rule and the record scan (never live strikes, entry ranges, strategy internals or secrets).
7. **Orchestrator check before the judge:** a complete story at an exact pushed SHA.
8. **End-to-end run after merge:** whoever merged runs the merged system once on real data in dry-run mode and
   records the command and result in the merge message or its follow-up; a change with no real-data path says so. A
   failed run means `git revert` of the merge at once.
9. **Second reviewer for money (ChatGPT): paused** while ChatGPT is inactive (no ChatGPT commit since 16 Oct 2026;
   owner, 22 Oct). It resumes when ChatGPT does.

## Brake restarts (story C5b)

Every change adding or editing a row of `journal/<book>/owner_overrides.csv` is lane 1. For each `restart_brake` row
the judge reads the `docs/DESK_DECISIONS.md` row its `decision` column cites and confirms that the owner's own quoted
words restart that book's drawdown brake for the episode being restarted, and that the row was added by the owner's
words, not written for them. The code checks only the form; the meaning is the judge's call, and a doubt is a FAIL.
The judge also confirms the words with the owner directly; no file counts as proof, and no answer is a FAIL.

## Merge procedure (owner, 21 Oct 2026: one full run per merge)

- The gates (`python -m pytest -q -n auto`, `ruff check fno tests tools`, `python tools/check_imports.py`, `python
  tools/check_records.py`, `python tools/check_numbers.py`) run **once, on the merged tree**. Never push on red.
- If `main` then moves only by lane-3 files (the paths `tools/ci_scope.sh` names: `reviews/`, `numbers/`,
  `conversations/`, `docs/DESK_DECISIONS.md`, `docs/WORK_REGISTER.md`; and scheduled jobs' data receipts, row 271),
  merge it in and push after the fast checks (ruff, `check_imports`, `check_records`, `check_numbers`, the code-size
  test). Any code or test change on `main` in between means a full run
  again before the push.
- A change of Markdown files only (no `.py`, test, config, workflow or requirements file) never runs the full suite
  (owner, 23 Oct 2026): the record scan, `check_numbers`, and the doc-reading tests unless every file is lane-3
  (CLAUDE.md "Code", "Text-only changes"). This holds for the builder, for each judge round and for the merge;
  a round that only rewords text is judged by reading it.
- The gates need the whole git history: in a shallow clone the freeze and back-fill tests fail with "shallow clone:
  run git fetch --unshallow origin main"; run that, then the gates again. It is never a code failure.
- A merge that moves data (a table out of the repository, rows into Drive, a migration) also runs the moved data's own
  command once in a fresh clone of the merged `main`, with the Drive settings.
- CI (`checks.yml`) mirrors this: a push of lane-3 files only skips pytest, ruff and the import check; the record scan
  and the number check run on every push.
