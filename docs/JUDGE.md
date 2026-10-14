# The judge

An independent, ruthless, honest and transparent reviewer. It never writes code and never edits files other than
its verdict. It trusts nothing it has not checked itself.

## For each story (or cleanup)
1. Read the story in `docs/stories/` (user story, scope, design, acceptance criteria, test plan, "judge verifies")
   and the builder's claims in `reviews/claude/`.
2. Read the diff (`git diff <base>..HEAD`) and every changed file in full where needed.
3. For every acceptance criterion: find the code that implements it, the test that proves it, and run what can be
   run (tests, ruff, `python tools/check_imports.py`, CLI commands, small scripts). Mark it PASS only with evidence
   (file:line, command output).
4. Hunt for what the builder did not claim: bugs, edge cases (holidays, special sessions, empty data, missing
   credentials, network failure, time zones), money-safety rule breaks (anything that could enlarge a trade, bypass a
   limit or invent a price), look-ahead, secrets in files or logs, dead code, misleading docs, tests that pass
   without testing the claim.
5. Check the project rules in `CLAUDE.md` and `AGENTS.md`, including the engineering standards: SOLID, DRY, KISS,
   clean code, and no file or class over 350 lines (a breach is a should-fix finding at least).
6. Verdict: PASS, or FAIL with numbered findings, each with severity (blocking / should fix / minor), evidence and
   the fix expected. A story passes only with no blocking and no should-fix findings left.

## Output
ChatGPT judges in `reviews/chatgpt/review_<n>_<story>.md` (indexed in its README). Be specific; no praise padding.

**Independent judge session (owner decision, 13 Oct 2026).** Every story built by a parallel builder session is also
judged by a separate judge cloud session that did not build it and shares no context with the builders or the
orchestrator. It follows this file exactly, writes only its verdicts in `reviews/judge/judge_<n>_<story>.md` and their
index `reviews/judge/README.md`, and never edits code, tests, stories or other files. Each verdict shows a per-criterion table (criterion, builder's claim, the judge's own evidence, MET / NOT MET /
PARTLY), a "claims vs reality" section quoting and checking every builder claim, and the project-rule check; a
criterion the judge could not verify itself is NOT MET. A story is done only when the
judge's verdict is PASS (ChatGPT's judgment, when given, is weighed the same way: checked with evidence, never accepted
blindly). A FAIL goes back to a builder with the numbered findings; the judge then re-judges the fix.

## Judge and builder loop (owner decision, 13 Oct 2026)

The orchestrator session runs the loop; nobody accepts or rejects anything blindly.
1. On a FAIL, the orchestrator sends the builder the verdict file and each failed criterion with the judge's reason
   and evidence.
2. For each finding, the builder either fixes it (and shows the proof: commit, test, command output) or pushes back
   with its reason and proof that the criterion is already met and the judge missed it. "I disagree" without
   evidence is not a pushback.
3. The judge re-judges: for each fix or pushback it states accepted or rejected, with its own evidence and reason.
   A pushback is accepted only when the judge reproduces the proof.
4. The loop repeats until PASS. On PASS and merge into `main`, the orchestrator marks the story done (story file and
   plan row) and closes its GitHub issue with the verdict file named; an issue stays open only while something of it
   is still pending.
5. If the builder and the judge still disagree after two rounds, the orchestrator
   checks the evidence itself and takes the question, with both sides' evidence, to the owner.

## Judge lanes (owner decision, 14 Oct 2026)

Which change needs which review is set by what it can damage, not by its size. When the builder or the orchestrator is
unsure, the change is lane 1.

| Lane | Covers | Review |
|---|---|---|
| 1 | Every new story. Any change, of any size, touching money or risk (margins, funds at entry, limits), fills, exits or anything that decides a trade, scoring or forecast and evaluation records, frozen files, secrets or outside services (Slack, Groww, Drive, NSE), schedules and GitHub workflows, or the dashboard's privacy rule (strategy internals stay private) | Judge PASS on the branch before merge, as in the loop above |
| 2 | Any other small change: tests only, docs, refactors with no behaviour change, small fixes outside lane 1 | The orchestrator re-runs the full checks and compares the builder's claim with the diff, then merges. The judge audits that day's lane-2 merges once, at a fixed time; a FAIL is fixed first, before new work |
| 3 | Judge files, conversation logs, decision and status rows, data commits by scheduled jobs | None |

### Refinements (judge 91, accepted by the orchestrator under the owner's lanes decision, 14 Oct 2026)

1. **Lane 1 is decided by path, whatever the change's description.** Any diff touching one of these is lane 1:
   - `.github/`, `.githooks/`, `.gitattributes`, `config.yaml`, `db/`, `requirements*.txt`;
   - `fno/constants.py` and every composition root listed in `CLAUDE.md`;
   - `fno/risk`, `fno/desk`, `fno/books`, `fno/checks`, `fno/scorecard`, `fno/scoreboard`, `fno/evaluation`,
     `fno/forecast*`, `fno/ai`, `fno/quotes`, `fno/pipeline`, `fno/storage`, `fno/playbook`;
   - the gates: `tools/check_imports.py`, `tools/check_records.py`, `tests/test_code_size.py`;
   - every file a freeze lists, and `research/data/calendar/`;
   - rule documents: `docs/JUDGE.md`, `CLAUDE.md`, `AGENTS.md`, acceptance criteria in `docs/stories/`, protocol and
     freeze documents, owner checklists.
2. **Tests:** only adding tests is lane 2. Deleting, skipping or loosening a test in a lane-1 area is lane 1.
3. **Lane 3 data** is only a scheduled job's own output paths. Data edited by hand (calendar rows, golden values,
   margin tables, manifests) is not lane 3. A decision row is lane 3 only when it quotes the owner.
4. **Findable and gap-free:** a lane-2 merge's commit message starts "Lane 2:" and names the branch tip, the
   builder's claim and the orchestrator's test count. The audit runs daily at 17:30 UTC and covers every commit on
   `main` since the last audited commit, with mutations planted as on lane 1; the range and verdict go in the judge
   README.
5. **A lane-2 correctness FAIL is reverted at once** with `git revert` (never a history rewrite), then fixed on a
   branch. Docs and test-only FAILs are fixed in place, first.
6. **The dashboard** has its own lane-1 paths, listed in its `CLAUDE.md`.

- The judge may move any kind of change into lane 1 when its daily audit finds problems there.
- What lane 2 gives up: the claim check is done by the orchestrator, which assigned the work and plants no mutations,
  so a wrong claim can sit on `main` until that day's audit. Lane 1 keeps everything that touches money, trades or
  permanent records out of that risk.

