# Judge 234: S1 items 8 and 11, `role_value_minimum_sample` in F9a's terms and the role-value files (judge A, lane 1)

**Checked:** `story/s1-role-value` at `37b06a66293db83d7c232c17624de7311c75c8b7`. The diff is 2 files: S1's
`PROTOCOL.md`, in `role_value_minimum_sample` and a new "Role-value files" bullet in `frozen_files`, and
`tests/evaluation/test_role_value_wording.py`. It merges after F9's fixed-family code (891de864,
`story/f9a-fixed-holm-family`, with judge B).

**Verdict: FAIL, 1 should-fix, no blocking.** The text agrees with the code, but F8's allocation code, which computes
the role-value cost, is still unhashed.

## Text against the code

- **Cost: matches `fno/role_value/cost.py` word for word in substance.**
  - The book's day cost is F8's month allocation of the `books_and_roles` shares × the day's minutes ÷ the month's
    minutes, rounded down to the paisa (`ROUND_FLOOR`).
  - It is split equally across the units consulted that day, with the paise left going to the first unit in
    identifier order (`split_paise`).
  - The decider takes no part, so the figure is an upper bound, labelled "conservative cost allocation" (the start of
    `COST_LABEL`).
  - The same dates as the tested net (review 124). The mean is shown apart as the operating cost. Unknown is never
    zero.
- **Bootstrap:** S3's resampler in `fno/scoreboard/uncertainty.py`: `BLOCK_DAYS = 20`, `RESAMPLES = 10_000` and
  `SEED = 20261014`, in date order. "Blocks of 20 observations (not 20 sessions)" is the honest wording for the
  ablation series.
- **Holm over a fixed family** matches `fno/role_value/verdict.py` at 891de864: 2m claims, a unit not testable at a
  review entering at p = 1 (`_claims`), and `holm` over the list. So the protocol and the code agree once 891de864
  merges, as the orchestrator orders.
- The risk effects are shown and never decide ("money only, risk shown"). The verdicts stay provisional until F9b, and
  the owner decides every drop.
- Nothing else in S1 changed: only this item and the new bullet. `python -m fno evaluation check` prints S1 and the
  gate complete on the trial merge.
- **The wording test:** my plant (dropping "equally" from the cost sentence) fails 1 test. The module test pins all
  13 `fno/role_value` modules except `cli`, plus `review_dates.py`.

## Should-fix

**SF1. The role-value cost is computed by F8's `fno/budget/allocation.py`, which no bullet hashes.**
- **Evidence:** `cost.py:18` imports `Allocation` from `fno/budget/allocation.py` ("the month's Claude plan cost split
  by measured minutes … rounded down to the paisa; the paise left go to the largest share"). `book_day_paise` takes
  its shares, so every unit's cost per opportunity, and so every "earns its cost" or "drop" verdict, rests on that
  file.
- **Two reasons it must be hashed:**
  - `frozen_files`' own rule says "the code of F8 and F9 is added to this list before the freeze".
  - It is the same principle as judge 229: code that computes a scored figure is hashed.
- **Path:** a change to the minutes-share formula or the paisa rule after the freeze moves every unit's cost, and so
  role verdicts, while `verify` stays silent.
- **Fix:**
  - Add `fno/budget/allocation.py`, and `fno/budget/constants.py` if a number from it decides a figure, to the
    Role-value bullet or to a separate F8 bullet.
  - Pin it in the wording test.
  - When item 15's closure test lands, also start its import walk at `fno/role_value`, so the walk covers these
    imports too. That test starts only at `fno/scoreboard` today, so it would not catch this.
  - `checks/validity_failures.py` (C4's log reader, from `controls.py`) can be exempted as a reader.

## Notes (one line each, no fix asked)

- WORK_REGISTER's S1 pending-edit line still says "a unit's cost the mean over its consulted days". The new text (each
  opportunity charged its own day's part; the mean shown apart) is the review-124 rule that `cost.py` codes, so update
  the register line.
- Merge order: this branch merges only after 891de864, and then item 15. Whoever lands second rebases the
  `frozen_files` bullets, rows only.

## Gates

- On the trial merge with origin/main a4c15c40 (tree 5ebd59e, clean), `-n auto`: pytest 6935 passed.
- `ruff check` is clean, `ruff format --check` shows 1227 files formatted, and `check_imports` is clean.

**A re-check needs only the F8 file in the list and its test line.**
