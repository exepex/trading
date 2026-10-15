# Judge 194: story F9a, role-value scoring (code; judge F)

**Commit judged:** `f04076dd3190af5299da34ea6937e70fc11c9ec0` on `story/f9-role-value`. The code commit is `75fa397f`;
the branch is built on S3's branch (`eebf90ef`) and has main merged in. Claims: response 166, "Code round".
Text: judge 172 addendum 1 and its note on `36f6b0fa`. Builder: session_01SFDjjZx7JYziM3jqJytG2z. Lane 1 (scoring
code that S1 hashes).

**Verdict: PASS.** Nothing blocking and no should-fix finding. There are 2 minor findings. Criterion 11 stays
partial until S1's pending edit 3 lands; what remains is listed below. This merges after S3: S3's code passed in
judge 191 addendum 1.

## Gates (run by me at f04076dd)
- `pytest`: 6,431 passed.
- `ruff check`, `ruff format --check` and `check_imports` are clean.
- The largest file in `fno/role_value/` is 99 lines.

## The orchestrator's checks

**S3's interface and F8's `allocate` only (strong evidence).**
- `git log eebf90ef..f04076dd --no-merges -- fno/scoreboard` is empty: F9a edits nothing under `fno/scoreboard/`.
- The imports used: `standard_unit.StandardUnit` (with its CLOSED, OPEN and NOT_FILLED outcomes),
  `matched.unit_legs`, `matched_actions.action_of`, `matched_days.CommonSet`, `committed_runs.CommittedRuns`,
  `series.DailySeries`, `uncertainty.resampled_ratios`, `p_value` and `holm`, and `budget.allocation.Allocation`.
- There is no copied valuation: `valuation.py` only orders S3's calls and sums their nets.

**Criterion 12: risk shown, never deciding (strong evidence).**
- `score.py` builds the p-values from `difference − cost` only. The worst month and the mean maximum-loss difference
  are separate fields that only `render.py` prints.
- My plant C4 put the maximum-loss difference into the values the p-values are built from; it was caught.

**The declared cost split: "unknown" means no verdict (strong evidence).**
- `cost.py` returns None for any consulted day with no usage minutes, or when any `books_and_roles` share of the book
  is None (no plan cost).
- `score_unit` then gives no p-values, and `verdict.py` prints `no verdict: cost unknown`. The unit never enters Holm.
- My plants were caught:
  - C1: a day with no usage treated as zero;
  - C2: no plan cost ignored;
  - C9: the remainder paise dropped.
- C3 (removing the `cost is not None` guard in `_entering`) was not caught, but it changes nothing: an unknown cost
  already has no p-value. The guard is redundant, not a gap.

## Criteria

| # | Judge's evidence | Result |
|---|---|---|
| 1 | `checks.py`: packs, snapshots equal, and equal to the run log's snapshot (C6 caught); the rotation advances on every committed row, a no-trade included (C11 caught) | MET |
| 2 | A bundled role is refused alone (`check_unit`, test) | MET |
| 3 | The hand examples in the docstrings (1,460 − 1,000 = 460; 30 opportunities) | MET |
| 4 | The review gate; `review_dates` (C13: every 4 months instead of 3, caught); the holiday month-end test | MET |
| 5 | See above | MET |
| 6 | Control counts from C4's log, with no profit figure (test) | MET |
| 7 | `verdict.holm is uncertainty.holm`; 2m claims in one list; C8 (p_drop on the wrong sign) caught; C12 (minimum 29) caught | MET |
| 8 | Standard-unit identity and spy test; an open pair waits | MET |
| 9 | A no-trade is 0 and a change, both ways (test) | MET; see minor 1 |
| 10 | Excluded rows, and an unconsulted card, counted apart (C10 caught) | MET |
| 11 | 30, 20, 10,000 and 20261014 are read from S1's text today. The percentiles fall back to the "one-sided 95%" wording | PARTLY, by design (below) |
| 12 | See above | MET |

My plants: 13. Caught: 10. Not caught: C3 (redundant, see above), C5 (only reachable if both one-sided claims pass,
which cannot happen in practice) and C7 (minor 1).

## Deviations 1-8: accepted
1. `consulted_units` replaces `consulted`: the declared split needs every consulted unit. A correction of the text.
2. A pair is "not scored" for S3's reasons (not observed, maximum loss unknown): consistent with S3.
3. Hashes are checked on scored rows only: correct, since an unavailable shadow has no pack or snapshot.
4. The real decision is the run collected on time (`CommittedRuns`): E3's late rule.
5. Criterion 11 is partial: see "What remains".
6. "Sixth full month" follows S1's own example (2 Dec 2026 gives June 2027): checked against the text.
7. `agents/role_units.yaml` does not exist yet: harmless while there are no rows. F2 writes it.
8. Fewer than 20 applicable opportunities give no p-value: only below the 30-changed minimum.

## What remains for criterion 11 (before the S1 freeze, not before this merge)
- **S1's pending edit 3 must state four things:**
  - the 5th and 95th printed percentiles. The test then switches to them by itself.
  - the cost denominator (every consulted day). This has no test yet; add one to `test_protocol_figures.py` when S1
    states it.
  - "blocks of 20 applicable opportunities" in place of "20 ablation days". Today's test matches "blocks of 20 " either
    way.
  - Holm across the book's units.
- The S1 freeze must not hash F9a's files before that test reads the new wording.

## Minor
1. **No test where the decisions differ but the nets are equal.** Example: a take that does not fill (0) against a
   skip (0). My C7 counted "changed" by net instead of by the decisions, and nothing failed. Unfilled entries happen
   in normal running, and "changed" sets the 30 minimum, so add one test.
2. **The rotation counts from the version's first row, not from the common start.** If F9b writes rows before the
   common start (pilot), the cycle position after the common start depends on them. The text says "from the common
   start (or a new version's first day)". Either filter the rows to the common start in `check_rotation`, or state
   that F9b writes rows only from the common start.
3. **Note (no action):** `score.percentile` repeats S3's one-line nearest-rank formula (`uncertainty.py:55`). This is
   acceptable as is. A shared reader in S3 would remove it later.

## Addendum 1: against S3 as passed (650e861d, judge 191 addendum 1)
- The difference from `eebf90ef` (F9a's base) to `650e861d` is only S3's added tie test
  (`tests/scoreboard/test_matched_bounds.py`) and the rename of S3's response file. No change under `fno/scoreboard/`.
- `git diff 650e861d f04076dd -- fno/scoreboard` is empty: F9a sees exactly the S3 code that passed.
- A trial merge of `f04076dd` onto `650e861d` merges clean (README auto-merged).
- The PASS stands.
