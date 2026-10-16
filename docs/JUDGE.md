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
| 2 | Only new tests (added files or cases) and docs outside the rule documents (`README.md`, `reports/`, `research_notes/`, `docs/` outside the rule documents) | The orchestrator re-runs the full checks and compares the builder's claim with the diff, then merges. The judge audits that day's lane-2 merges once, at a fixed time; a FAIL is fixed first, before new work |
| 3 | Judge files, conversation logs, decision and status rows, number claims (`numbers/<category>.csv` rows, story O12), data commits by scheduled jobs | None |

### Refinements (judge 91, accepted by the orchestrator under the owner's lanes decision, 14 Oct 2026)

1. **Lanes 2 and 3 are listed; everything else is lane 1 (judges 92 and 92 addendum 1), whatever a change's
   description.** So the list cannot miss a folder.
   - **Lane 2** is only new tests (added files or cases) and docs outside the rule documents: `README.md`,
     `reports/`, `research_notes/`, and `docs/` outside the rule documents.
   - **Lane 3** is as in the table.
   - **Everything else is lane 1**, for example all of `fno/` and `tools/`, `agents/`, `playbook/`, `journal/`,
     `accounting/`, `contracts/`, `.claude/`, `.github/`, `.githooks/`, `.gitattributes`, `ruff.toml`, `config.yaml`,
     `db/`, `requirements*.txt`, any hand edit under `research/`, any weakened test, and the rule documents
     (`docs/JUDGE.md`, `CLAUDE.md`, `AGENTS.md`, acceptance criteria in `docs/stories/`, protocol and freeze
     documents, owner checklists).
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

### Brake restarts (story C5b)

Every change adding or editing a row of `journal/<book>/owner_overrides.csv` is lane 1. For each `restart_brake` row
the judge reads the `docs/DESK_DECISIONS.md` row whose bold title the row's `decision` column cites, and confirms
itself that the owner's own quoted words restart that book's drawdown brake for the episode being restarted (the brake
that fired before that date, not an earlier one), and that the decisions row was added by the owner's words, not
written for them. The code checks only the form (title once, owner quote, book named, dated on or before the restart,
not reused); whether the words really mean "restart this brake now" is the judge's call, and a doubt is a FAIL.
The judge also confirms the words with the owner directly (asks the owner and gets a yes in its own session); no file
in the repository counts as proof, and no answer is a FAIL (ChatGPT review 110, response 142).

## Quality rules for every story (owner decision, 15 Oct 2026: "rules yes")

Owner: "Everything must have to be reviewed thoroughly and properly. I don't want that we develop story with lot of
gaps." These rules add to the loop above; none of them replaces the judge's own checks.

1. **Story check before code.** The builder writes the full story text (scope, acceptance criteria, test plan) first
   and pushes it alone to its story branch; the judge checks it against the design and the owner's decisions at that
   SHA, and code starts only after that check passes. A missing or wrong requirement is a finding against the story
   text. Stories already being built on 15 Oct 2026 (A15, T1, P1, A17, F8/BG1, C5, STR1) have their story text checked
   first within their code review.
2. **Gap list.** Every story lists each requirement of its design paragraph (and of every design section it cites) as
   covered by a named criterion, or out of scope with the reason. A requirement in neither list is a blocking finding.
3. **Builder self-review.** Before reporting, the builder runs independent code-review agents (correctness and silent
   failures) on its diff and states in its claims file what they found and what it fixed or why not.
4. **Broken-code proof per criterion.** Each criterion names its code (file:line) and a test, and the builder shows
   that the test fails when that code is broken on purpose. The judge plants its own mutations as before; a builder's
   proof never replaces them.
5. **Positive, negative, boundary and empty cases.** For each criterion the builder's tests cover the good case, the
   bad case, the boundary (at, just under, just over every limit) and the empty or missing-input case, and the judge
   checks each of them itself (owner, 15 Oct 2026: "ensure that all the positive and negative use cases are tackled
   properly").
6. **Real output sample.** The claims file shows real output of the story (a card, a table, a refusal message) made by
   the committed code, and says how it was made. Samples obey the cards-in-Drive decision (owner, 15 Oct 2026), the
   privacy rule and the record scan: only NO TRADE cards, redacted output or outputs labelled as historical examples,
   made in a dry run or a test, never by a live post; never live strikes, entry ranges, strategy internals or secrets.
7. **Orchestrator check before the judge.** The orchestrator reads the diff against the story and the gap list, re-runs
   the gates, and sends the judge only a complete story at an exact SHA confirmed from the builder's push output.
8. **End-to-end run after merge.** After a merge, the person who merged (the orchestrator) runs the merged system once
   on real data in dry-run mode (no live post, no order path) and records the command and its result in the
   conversation log and in the merge message or its follow-up commit; the judge's merge check verifies that record. A
   change with no real-data path (documents only), or a run that cannot reach the data from the session, states so and
   why; it is never skipped silently. A failed run is handled as refinement 5: `git revert` of the merge at once, then a
   fix on the branch.
9. **Second reviewer for money.** Stories touching money limits, fills, exits or the real-money gate (C5, E8, RM1 and
   later ones of that kind) also get a ChatGPT review after the judge's PASS and before the merge; its points are
   checked with evidence (accept, partial or reject), never accepted blindly. Any change made after the judge's PASS
   because of that review returns to the judge before the merge.

**Merge procedure: when the gates run (owner, 16 Oct 2026; story X fast checks).**
- The gates (`python -m pytest -q -n auto`, `ruff check fno tests tools`, `python tools/check_imports.py`,
  `python tools/check_numbers.py`) run once, on the final merged tree, before the merge is pushed.
- The gates need the whole git history: the freeze and back-fill tests read past commits. In a shallow clone
  (`git rev-parse --is-shallow-repository` says `true`, as in some cloud sessions) those tests fail with "shallow
  clone: run git fetch --unshallow origin main"; run that command, then the gates again. It is never a code failure.
- A `git pull --no-rebase` just before the push that brings only lane-3 files (`reviews/`, `numbers/`,
  `conversations/`, `docs/DESK_DECISIONS.md`, `docs/WORK_REGISTER.md`: the paths `tools/ci_scope.sh` names) needs no
  rerun of pytest, ruff or the import check: none reads them. The number check reads `reviews/` and `numbers/`, so it
  runs again (under a second). A pull that brings anything else means every gate runs again on the new tree.
- A merge that moves data (a table moved out of the repository, rows adopted into Drive, a migration) also needs one
  run of the moved data's own command in a fresh clone of the merged `main`, with the Drive settings (as A17d's rule-8
  fill).
- CI (`checks.yml`) mirrors this: a push of lane-3 files only skips pytest, ruff and the import check; the record scan
  and the number check run on every push.

**Several judges (owner decision, 15 Oct 2026).** Several judge sessions may run at once, each with a dedicated, limited
set of stories named by the orchestrator, so no judge's load grows too large. Each follows this file in full. Every
judge number and addendum number is claimed in the central registry before the file or section is written (story
O12): `python tools/claim_number.py judge-report <slug> --session <id>` and `python tools/claim_number.py
judge-addendum <label> --session <id> --report <n>`; the report names the response it judges in its title. (The
orchestrator's old convention, verdict number equal to the response number, ends with O12: the two series had already
run apart, judges up to 274 against responses up to 253, so the equal number is often taken.)
