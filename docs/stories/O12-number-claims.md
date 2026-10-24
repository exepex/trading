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


## O12e: ledger trial numbers are claimed too (orchestrator, 25 Oct 2026)

**Status:** story text on `story/o12e-ledger-trials` (builder session_019rZrcu1GSqUC7PScqwQgo2; O12's builder
session_01KS9xBc14DGACR9QrS6Acdq could not be reached on 25 Oct, so the orchestrator decides who builds). **Lane: 1 is proposed, not 2** (when unsure, lane 1): the guard
below changes `Ledger.register` (B4, the rule that a trial runs only after its registration) and the evaluation
freeze's own trial number (`fno/evaluation/freeze.py`, an evaluation record). The orchestrator decides.

**Why.** `research/ledger.csv` trial ids are taken by hand as "the highest id plus one" in each builder's own
checkout; `Ledger.register` accepts any id it is given, and `fno/evaluation/freeze.py` takes the highest plus one
itself. Two branches cut from the same `main` therefore pick the same ids: on 24-25 Oct the v4 freeze took 101-108
and EDGE2 F1 took 101-106 on its own branch. Nothing is miscounted (the ledger refuses a duplicate id at merge), but
the second branch must renumber, and a renumbered trial must be registered and committed again before it runs
(`require_committed` finds the id in git history). The review series had the same flaw and O12 fixed it with a
registry; trials get the same.

**Design (one more category; nothing else in O12 changes).**
- **Registry `numbers/ledger-trial.csv`**, the same four columns. One row reserves a **block**: `number` is `<a>-<b>`
  (`a <= b`, both whole numbers from 1) or a single `<n>`; `name` is the block's **experiment prefix**, a slug.
- **Items:** the numeric `trial_id`s in `research/ledger.csv` with their `experiment`. Ids that are not whole numbers
  (`book3:<strategy_id>`, Book 3's own registry; none on `main` today) are outside the series.
- **The check** (`tools/check_numbers.py`, unchanged command) adds, for this category: a numeric trial id that no
  block covers; a trial whose `experiment` does not start with its block's name (another branch's block used); two
  blocks that overlap; a malformed block. A block with ids not yet in the ledger is a claim still being written (fine).
- **Claiming:** `python tools/claim_number.py ledger-trial <experiment-prefix> --session <id> --count <k>` (default 1)
  pushes one block row to `main` exactly as O12 does (git decides the race; the loser retries on the new `main`). The
  block starts after the highest block end and the highest ledger id on `main`. `--number <a>-<b>` asks for an exact
  block, refused when it overlaps one taken. The tool prints the ids and the next step: "merge main into your branch
  (`git pull --no-rebase origin main`), then register trials <a>-<b> with experiment starting `<prefix>`".
- **Seeded history, pinned:** the 16 runs of consecutive ids with one experiment on `main` at the merge (1, 2-17,
  18-21, 22-31, 32-36, 37-41, 42, 43-52, 53, 54, 55, 56-70, 71-98, 99, 100, 101-108), each named by its experiment,
  session `existing`, pinned in `fno/numbering/seed_pins.json` like the other series.
- **Reservations already given (the orchestrator, 25 Oct), written as claims in the same commit:** `109-114`
  `edge2-f1-weekly-vrp-gate` for session_01VhppcYHXq3yTJBV2UnsWSs (EDGE2 F1; its branch uses 109-114 with experiment
  `edge2-f1-weekly-vrp-gate-2026-10-25`), and `115-120` `edge2-f6` for EDGE2 F6 (reserved by the orchestrator,
  session_01Mt6dcBU5kp2htdPN2KmiZH; F6's experiment must start `edge2-f6`). Their time is this commit's (the
  reservation's own minute was not recorded).
- **The guard at registration:** `Ledger.register` refuses a numeric trial id that no block in the same checkout
  covers, or whose block's name does not start the experiment, with the claim command in its words. Every writer goes
  through it (the factory's `register`, the evaluation freeze, a registration by hand through the class), so no
  caller needs its own check. A block claimed on `main` reaches a branch when `main` is merged into it.
- **The evaluation freeze** stops taking "highest plus one": it takes the lowest unused id of a block whose name starts
  its experiment, and is refused, with the claim command, when there is none.

**Known limits (said plainly).** The session column is what the claimant typed: the check cannot prove who claimed a
block, only that every trial sits in a block named for its experiment. An id typed straight into `ledger.csv` by hand
(outside the class) is caught by the check on the next push, not before. `ledger.csv` merge conflicts stay git's.

**Criteria.**
1. Each finding is produced once on a planted temporary repository and absent on the clean one: an uncovered trial
   id, a trial outside its block's experiment, two overlapping blocks, a malformed block (`5-3`, `x`, `3-`).
2. `main` at the merge is clean: the 16 seeded rows equal their pin; 101-108 and both reservations pass.
3. A claim with `--count 6` on a registry ending at 120 and a ledger ending at 108 pushes `121-126`; two clones
   claiming at once get two blocks that do not overlap (O12's race test, for this category); an exact block that
   overlaps is refused.
4. `Ledger.register` refuses id 121 with no block, refuses 116 for experiment `edge1-...` (block `edge2-f6`), and
   accepts 116 for `edge2-f6-...`; Book 3's `book3:<id>` is still accepted.
5. The evaluation freeze registers the lowest free id of its experiment's block and is refused without one.
6. `numbers/README.md` and CLAUDE.md's numbering line name the new category; the claim tool's help lists it.
Plants, one at a time and restored: the block check removed; the experiment check removed; the overlap check removed;
the guard removed from `register`; the freeze's highest-plus-one restored.
