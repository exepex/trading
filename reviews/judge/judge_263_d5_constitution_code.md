# Judge 263: D5 code, Book 3's constitution and strategy registry (story/d5-constitution-code at b76564b7)

Judge B, 16 Oct 2026. Lane 1 (decides trades; C4). Claims: `reviews/claude/response_249_d5-constitution-code.md`.
Built on D4's branch (judge 260, FAIL), so it merges after D4. D5's own commits are 6326913f and b76564b7; the rest
of the diff against D4's head is main merged in.

**Verdict: FAIL.** One should-fix: a benign parallel registration disables Book 3 permanently.

## What the orchestrator asked

| Question | Result | Evidence |
|---|---|---|
| Book 1 and Book 2 unchanged | MET | their lines in `validity_modes` are unchanged; `WaitsFor` is removed because no book uses it. The new wiring does no I/O at construction (`Ledger`, `Git` and `ConstitutionFiles` are lazy) |
| No path trades Book 3 without a registered constitution and strategy | MET | `ConstitutionMode.checks`: no file matching the D6 `constitution` component fails first. `require_registered` needs the row and spec committed at HEAD, `proposed_on` before the day, the spec on disk equal to the committed one with a matching hash, the spec file touched by one commit only, and no edited registry row. `strategy_id` is not set by C4's adapter today, so Book 3 fails closed |
| Registry rows can't be edited after the fact | MET for edits; **over-refuses** (the should-fix) | `edited_rows` compares consecutive committed versions |
| A twin of D4's should-fix | **No twin by the passed text** | Book 3 is not bound to D2's rule default or eligible set; D5's C4 checks are registration, the constitution and the spec's terms. See the question below |

## Should-fix: one parallel registration refuses every Book 3 strategy, for good

`edited_rows` walks `git log --reverse -- registry.csv` and compares *adjacent* versions. With two registrations on
parallel lines of history, merged with both rows kept (the normal resolution under this repository's `git pull
--no-rebase` workflow), the adjacent pair is the two sides, and the side's row reads as "removed".

I reproduced it on a temporary repository with D5's own `StrategyRegistry.edited_rows`:
- base `[x]`;
- branch A `[x, a]`, branch B `[x, b]`;
- a merge keeping `[x, a, b]`.

The result is `['b']`. Because `require_registered` checks `edited_rows()` over the whole history on every call, every
Book 3 strategy is then refused until the code changes. There is no data fix short of rewriting history.

Overlapping routine runs are a real event here: today's A16 root cause was "overlapping runs on one key" (conversation
log 16 Oct). The fix is the builder's design. One way: check each commit's registry against each of its parents (every
parent row present and unchanged in the child, e.g. `git log --format='%H %P'`), not against the previous entry in the
log. Add a test with two parallel appends merged (not refused), and one with a merge that drops or edits a row
(refused).

## Rulings on the six deviations

1. **No `registered_in_commit` column; the commit is read from git: ACCEPT.** A row cannot name its own commit.
2. **C4 checks against HEAD: ACCEPT, but the stated reason is wrong.** The claim and the module docstring say "D6
   repeats the strict check when the decision is scored". D6's `_registered_before` (`fno/books/versions.py:70`)
   checks D6 **version rows**, not Book 3 strategy registrations (grep: no `book3` or `strategy_id` in D6). The
   strictness still holds without it: `proposed_on` is set by the clock and must be an earlier day than the decision,
   and C4 runs before the decision commit. Correct the docstring and claim (no should-fix).
3. **The holding limit checked twice (spec window at registration, the trade's exit at C4): ACCEPT.** Needed, as the
   builder says.
4. **Non-NIFTY and weekly cannot be written in D1's format: ACCEPT.** The constitution's checks remain the second
   guard.
5. **Criterion 7 by construction: ACCEPT.** C4 has no objection input; the decider's behaviour is F6's.
6. **Criterion 8, the trial family only: ACCEPT.** The confirmatory gate is the scoreboard's.

## Other owners' files: OK

`validity_proposal.py` (one defaulted field), `checks/wiring.py` (the Book 3 mapping), `validity_modes.py` (dead
`WaitsFor` removed), and B4's `ledger.py` (one read-only `Git.commits_touching`). Each is minimal.

## A question for the owner (reasoning only, not a finding)

D5 lets Book 3 trade a registered strategy on any day: C4 does not ask whether the spec's own entry conditions held.
That matches the text: C4 checks Book 3 only against hard facts and owner constraints (design 12.4). But it means the
registered spec fixes Book 3's structure, width, lots and holding, not *when* it enters. A strategy's scored record
then mixes the rule with the AI's timing. If the owner wants a registered spec to bind entries too, it is a text change
for D5 or F6, decided before F6 is built.

## Notes only

- `commits_touching` and `edited_rows` read local history. In a shallow clone (depth 1, the default of
  `actions/checkout`) an edit is invisible and the check passes, which is fail-open. Book 3's C4 runs in the book's
  decision run (cloud sessions clone 50 commits, and a same-day edit is recent). Failing closed on a shallow
  repository (`git rev-parse --is-shallow-repository`) would remove the doubt.
- A malformed constitution file raises out of C4 (as D4's envelope does). It is fail-closed, but not a named check.

## Mutations (real cases, all caught)

- `proposed_on >= day` loosened to `>`: 2 tests fail.
- The spec-history check removed: 1 test fails.
- `edited_rows` ignored: 1 test fails.
- C4's holding check always passing: 1 test fails.
- The spec hash and on-disk checks removed: 1 test fails.

## Gates (run by me on b76564b7)

`env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto -p no:cacheprovider`: 7,251 passed. `ruff check`: clean.
`ruff format --check`: 1,292 files already formatted. `check_imports`: clean.
