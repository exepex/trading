# Story O12: one central place to claim file numbers

**Status:** story text and code on `story/o12-number-claims`, lane 1 (tools, CI, rule documents); judge before `main`.

**Why (owner, 16 Oct 2026).** "let's build one centralized uh, place to claim the file numbers ... the file names must
be categorized based on what they represent. And each category can have its own reference number ... so that those do
not conflict with others ... let's keep it a centralized way of handling uh, that, that thing so that there are no
clashes." And: "do not over-engineer ... Simplicity is also our priority, but not the product quality."

Parallel sessions (Claude builders, judges, ChatGPT) each pick "the highest number plus one" in their own checkout and
push later, so two of them take the same number. On `main` at 9dbf1b3f: `response_66` twice, `judge_233`, `judge_234`
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
highest in that category (for an addendum: the highest `k` of that report). A number can also be asked for exactly
(`--number`, for the convention that a judge report takes its story's response number); it is refused when taken.

**Claiming is atomic through git itself.** `python tools/claim_number.py <category> <slug> --session <id>` works in a
temporary worktree of `origin/main` (the caller's own branch and files are never touched): it appends the row, commits
only `numbers/<category>.csv` and pushes it to `main`. A rejected push means someone else moved `main` first: it fetches
again, recomputes the number on the new `main` and retries (at most 8 tries, with a random 0.5-3 s pause). The number
is the caller's only after the push succeeds; the tool then prints the file name to create (or the addendum heading).
A claim never needs pytest: `numbers/` is lane 3 (status rows), so a claim-only push skips the code checks in CI.

**A check catches what slips past.** `python tools/check_numbers.py` (standard library only) fails when:
1. a numbered file (or numbered addendum heading) has no registry row with its number and name;
2. two files, two headings or two registry rows share a number in one category, unless every row involved is a seeded
   `existing` row (history is recorded as it is, never renumbered);
3. a registry row is malformed (wrong columns, a number that is not of its category's form, a time that is not UTC
   ISO).
A row with no file yet is fine: it is a claim whose file is still being written. It runs in CI on every push (code or
lane-3 only, as the record scan) and in the merge procedure's gates. It is not a pre-commit hook: a builder's branch
does not carry its own claim row (the row is on `main`), so a branch-local check would refuse correct work.

**Seeded from history.** Every numbered file and addendum heading on `main` when this merges gets a row with session
`existing` and no time; the known duplicates are kept as two `existing` rows each.

**Manual equivalent (ChatGPT and anyone who cannot run the tool).** Pull `main`, append one row to
`numbers/<category>.csv` with the next number, commit only that file, push to `main`. If the push is rejected, pull and
take the next free number again; the number is yours only once the push is accepted. Then write the file.

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
   commit that changes only that category's CSV, pushed to `main`; it refuses an unknown category, a taken exact
   number, an addendum of a report that has no row, and a slug that is not lower-case words with `-`, `_` or digits.
3. Two claims racing for one category both succeed with different numbers: the loser's push is rejected, it re-reads
   `main` and takes the next number; after the bounded tries it stops with a clear line and exit 1, never claiming a
   number it did not push.
4. The caller's checkout is untouched (branch, index, working files) and the temporary worktree is removed, success
   or failure.
5. `tools/check_numbers.py` fails on each case in "A check catches what slips past" and passes on the seeded `main`.
6. CI runs the check on every push; `tools/ci_scope.sh` counts `numbers/` as lane 3; `docs/JUDGE.md` lists number
   claims as lane 3 and the check in the merge gates.
7. `AGENTS.md`, `CLAUDE.md` and the three review READMEs say how to claim (tool or manual) instead of "highest plus one".

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
filled registry, per-report addendum sequences, an exact free and an exact taken number; a real race between two
clones of a bare repository (the second claim is rejected once and gets the next number); retries exhausted; the
caller's checkout unchanged; each check failure planted in a temporary repository; the seeded repository passes.
