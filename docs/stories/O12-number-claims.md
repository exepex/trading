# Story O12: one central place to claim file numbers

**Status:** story text and code on `story/o12-number-claims`, lane 1 (tools, CI, rule documents); judge before `main`.

**Why (owner, 16 Oct 2026).** "let's build one centralized uh, place to claim the file numbers ... the file names must
be categorized based on what they represent. And each category can have its own reference number ... so that those do
not conflict with others ... let's keep it a centralized way of handling uh, that, that thing so that there are no
clashes." And: "do not over-engineer ... Simplicity is also our priority, but not the product quality."

Parallel sessions (Claude builders, judges, ChatGPT) each pick "the highest number plus one" in their own checkout and
push later, so two of them take the same number. On `main` at 9dbf1b3f (still so at a337f4e0): `response_66` twice, `judge_233`, `judge_234`
and `judge_235` twice each, and judge 98 and judge 122 each hold two "Addendum" sections with the same number
(addendum 3 and addendum 4). Judge 233 says "renumbered from 227" and judge 95 add. 1 "renumbered response_94": the
clashes cost re-work and break links.

## Design

**One registry per category, on `main`.** `numbers/<category>.csv`, columns `number,name,session,claimed_at_utc`.

| Category | Files it numbers | Number | Name |
|---|---|---|---|
| `claude-response` | `reviews/claude/response_<n>_<slug>.md` | integer | the file name |
| `chatgpt-review` | `reviews/chatgpt/review_<n>_<slug>.md` | integer | the file name |
| `judge-report` | `reviews/judge/judge_<n>_<slug>.md` | integer | the file name |
| `judge-addendum` | `## Addendum <k>` sections inside `judge_<n>_*.md` | `<n>.<k>`, e.g. `270.2` | a short label |

Each category has its own sequence, so categories never clash with each other. A number is the next one after the
highest taken in that category (for an addendum: the highest `k` of that report), where taken means a registry row
or a file (or heading) already on `main`, so a file written the old way is never handed out again. A number can also
be asked for exactly (`--number`); it is refused when taken. The judges' old convention (verdict number equal to the
response number) ends here: the series have already run apart (judges to 274, responses to 253 on 16 Oct), so the
equal number is often taken; a report names the response it judges in its title.

**Claiming is atomic through git itself.** `python tools/claim_number.py <category> <slug> --session <id>` works in a
temporary worktree of `origin/main` (the caller's own branch and files are never touched): it appends the row, commits
only `numbers/<category>.csv` and pushes it to `main`. A push refused because someone else moved `main` first
(git's "[rejected] ... fetch first" or "non-fast-forward", or the server's "cannot lock ref" when both pushes arrive
together) is a lost race: it pauses 0.5-3 s at random, fetches again, recomputes the number on the new `main` and
retries, at most 8 tries. Any other refusal (no access, a protected branch, no network, a server hook) stops at once
with git's own words. The number is the caller's only after the push succeeds; the tool then prints the file name to create (or the addendum heading).
A claim never needs pytest: `numbers/` is lane 3 (status rows), so a claim-only push skips the code checks in CI.

**A check catches what slips past.** `python tools/check_numbers.py` (standard library only) fails when:
1. a numbered file (or numbered addendum heading) has no registry row with its number and name;
2. two files, two headings or two registry rows share a number in one category, unless every row involved is a seeded
   `existing` row (history is recorded as it is, never renumbered);
3. a registry row is malformed (wrong columns, a number that is not of its category's form, a time that is not
   `YYYY-MM-DDTHH:MM:SSZ`, a seeded row with a time);
4. the seeded rows differ from their pinned SHA-256;
5. a file starts like a series (`response_`, `review_`, `judge_`) but does not follow `<prefix>_<n>_<slug>.md`
   (`response_07_x.md`), since it would escape the check.
A row with no file yet is fine: it is a claim whose file is still being written. Addendum headings count at levels 2
and 3 (`## Addendum 3`, `### Addendum 3`), not inside code blocks; an addendum heading must carry its number (the 14
old unnumbered `## Addendum` headings are outside the series). Blank lines and a byte-order mark in a hand-edited
registry are tolerated. The check runs in CI on every push (code or lane-3 only), as the last step with `if: always()`
so a failing number check never stops the record scan, and in the merge procedure's gates on `main`. It is not a
pre-commit hook or a branch gate: a builder's branch does not carry its own claim row (the row is on `main`), so a
branch-local check would refuse correct work.

**Seeded from history, then pinned.** Every numbered file and addendum heading on `main` when this merges gets a row
with session `existing` and no time; the known duplicates are kept as two `existing` rows each. Seeded rows may
repeat a number, so adding one later could hide a new clash: `--seed` also writes the SHA-256 of each category's
seeded rows to `fno/numbering/seed_pins.json`, and the check fails when they differ. Changing that file is a code
change (lane 1, judged), never a claim. At the merge, the merger runs `python tools/check_numbers.py --seed` on the
merged tree (files keep landing on `main` meanwhile) and reads the rows it added before pushing; the judge's merge
check verifies them.

**Manual equivalent (ChatGPT and anyone who cannot run the tool).** In a separate copy of the newest `main` (a
worktree, a fresh clone, or GitHub's editor), never the person's own working checkout (judge 354 SF1: a reset there
wipes uncommitted work): append one row with the next number; commit only that file; push to `main`. If the push is
refused, refresh that copy (`reset --hard origin/main` there only), never `git pull` (a merge can keep both appended
rows with one number), and take the next number. The number is yours only once the push is accepted. Then write the
file. Steps in `numbers/README.md`. Not protected: a claimed row edited or deleted before its file exists (the check
sees only files, reused numbers and the pinned seed); git history shows it.

### Why integers in a registry, not timestamps or UUIDs (reasoning only)

- A timestamp or UUID needs no central place, but `judge_1739712345_x.md` or `response_3f2a9c1e_x.md` cannot be read
  or cited aloud ("judge 270 add. 2" is how every file, commit and message refers to work today), does not sort with
  the 600 existing numbered files, and breaks the readable series the READMEs index. Epoch seconds can still clash
  (two sessions in the same second); a UUID cannot, but nobody can say which came first or whether one is missing.
- The registry keeps the readable series and makes the clash impossible instead of unlikely: git refuses the second of
  two pushes to the same `main`, so exactly one claim wins each number. The cost is one push per claim (a few
  seconds) and one rule for those who cannot run the tool.

## Acceptance criteria

1. `numbers/` holds one CSV per category above, seeded from `main`: every numbered file and numbered addendum heading
   has a row; the duplicates named in "Why" are rows with session `existing`.
2. `tools/claim_number.py` claims the next number of a category (per report for addenda), or an exact free one, with a
   commit that changes only that category's CSV, pushed to `main`; a number held by a file on `main` without a row is
   taken too. It refuses an unknown category, a taken exact number, an addendum of a report not on `main`, the
   session name `existing`, and a slug that is not lower-case words with `-`, `_` or digits.
3. Two (and four) claims racing for one category all succeed with different numbers: the loser's push is rejected, it
   re-reads `main` and takes the next number; after the bounded tries it stops with a clear line and exit 1, never
   claiming a number it did not push. A push refused for any other reason stops at once with git's message.
4. The caller's checkout is untouched (branch, index, working files) and the temporary worktree is removed, success
   or failure.
5. `tools/check_numbers.py` fails on each case in "A check catches what slips past" and passes on the seeded, pinned
   `main`; a seeded row added after the pin fails wherever it sits.
6. CI runs the check on every push, last, with `if: always()`; `tools/ci_scope.sh` counts `numbers/` as lane 3;
   `docs/JUDGE.md` lists number claims as lane 3 and the check in the merge gates.
7. `AGENTS.md`, `CLAUDE.md` and the three review READMEs say how to claim (tool or manual) instead of "highest plus one";
   `docs/JUDGE.md` ends the judge-number convention and says why.

## Gap list

- Owner's "categorized ... each category its own reference number": criterion 1 (four categories, own sequences).
- "centralized ... no clashes": criteria 2-3 (one registry on `main`, git's push decides).
- "atomic integer, or a timestamp, or UUID": the comparison above; integers chosen.
- "do not over-engineer": one CSV per category, two small tools, no service or lock server.
- Other numbered series found and left out, with the reason: story ids (`O12`, `A16b`) are given by the orchestrator
  and never collided; research and data files are numbered by dates, protocols (`PROTOCOL_v4`) by their freeze.
  Conversation logs are per date. Adding a category later is one row in the category table of
  `fno/numbering/categories.py`.

## Test plan

Positive, negative, boundary and empty cases per criterion, in `tests/numbering/`: the next number on an empty and a
filled registry, per-report addendum sequences, an exact free and an exact taken number, a file without a row; a real
race between two clones of a bare repository (the second claim is rejected once and gets the next number) and four
clones claiming at once in threads; retries exhausted; a server hook refusing the push; the caller's checkout
unchanged; each check failure planted in a temporary repository; the seed pinned and a later seeded row caught.

## O12b: an alert when main's number check is red (orchestrator, 16 Oct 2026)

**Why.** `checks.yml` already runs the number check on every push, but a red run is only a cross on GitHub: nobody is
told, so a stray file (a numbered file written without a claim) can sit unseen while later pushes stay red.

**Change.** `tools/check_numbers.py --alert [--baseline DIR]` posts the problem lines to #fno-desk with the existing
alert sender (`FNO_SLACK_BOT_TOKEN`; without it, it prints "alert NOT sent"). With `--baseline`, only problems the
baseline checkout did not already have are posted. `.github/workflows/number-alert.yml` runs it:
- on every push to `main`, with the commit before the push as the baseline, so the push that turns `main` red is
  announced once and later pushes stay quiet (a missing "before" commit, as on a force-push, means no baseline);
- by hand (workflow_dispatch), without a baseline. (An hourly reminder ran until the owner cut it on 22 Oct 2026.)
It fixes nothing, writes nothing and has read-only repository permission. The plain check stays standard-library only:
the alert sender is imported only when something is posted. Lane 1 (a workflow and a Slack post).

**Criteria.**
1. A red check with `--alert` posts one message listing every new problem line; a clean check posts nothing.
2. With `--baseline`, problems the baseline already had are not posted; a new one is.
3. The workflow runs on every push to `main` (with the before commit as baseline) and by hand (without; the hourly run was cut on 22 Oct 2026, DESK_DECISIONS "Cut-list accepted"), with only
   `FNO_SLACK_BOT_TOKEN` and `contents: read`.
4. (Added 21 Oct, root cause of main's 16 Oct red: judge 307's heading `## Addendum 307.5` was read as 307.307.) A
   claim prints the next step word for word: the file to write, or for an addendum the heading `## Addendum <k>` with
   only the addendum's own number; `numbers/README.md` says the same.
Tests: `tests/numbering/test_tools.py` (the cases above, and the workflow's triggers and command).

## O12c: a refused claim ends on its verdict (judge B, 22 Oct 2026)

**Why.** Judge B wrote `judge_464` after a claim whose commit the record-scan hook refused (this Python lacked
`xlrd`, now imported by the scan's code). The tool did exit 1, but its first line was "NOT claimed (git commit -q -m
...", then the multi-line commit message and the hook's traceback, so the output ended on "ImportError: ...)" and the
verdict was easy to miss.

**Change.** A failed git step prints git's whole output first, then one last line: "number claim: NOT claimed (the
commit was refused, usually by the record-scan hook: git's output is above; a missing package means this Python lacks the
requirements, so run `sh tools/routine_setup.sh`). Nothing was pushed: do not write the file; fix it and claim again."
Every refusal ends with "Nothing was pushed: do not write the file". Exit 1 as before; nothing is pushed.

**Criteria.** A planted failing pre-commit hook (crashing, or refusing with findings) makes the claim stop with exit 1,
the hook's own words before a last line that starts "number claim: NOT claimed", `main` unchanged and the worktree
removed (`tests/numbering/test_claim.py`).

