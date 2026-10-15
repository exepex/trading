# Judge 196: S6 code, scorecard measures (judge G)

- **Judged:** `story/s6-scorecard-measures` at `a9f745bf3432a1d75fb5ca383d812f7ad40a0dd7` (builder session
  0185gR5DmoDh2zBAvgRU4CEB; claims `response_180_s6-code.md`). It is built on S3 `650e861d` plus main.
- **Text:** PASSed in judge 158 addendum 1. Lane 1. The orchestrator gave the go; 196 was the next free number.
- **Verdict: FAIL.** There are 2 should-fix findings:
  - the cash-rate placeholder can be frozen silently;
  - three test gaps where my mutations survive on paths the code takes every run.

  There are also 3 notes. The arithmetic I re-ran by hand is right, and 15 of my 18 planted mutations are caught.

## What I re-ran

- **Gates:**
  - ruff check, ruff format and `check_imports` are clean;
  - the largest file is `random_control.py` at 165 lines;
  - `tests/scoreboard tests/evaluation`: 161 passed;
  - full suite: 6,397 passed, 8 failed, 1 error, **exactly main's failure set** (the shallow clone's history-based
    freeze and back-fill tests).
- **S2's tests are unedited.** `git diff 71a1de30 a9f745bf --stat -- tests/scoreboard/` lists only added files.
  `tests/evaluation/test_completeness.py` only adds the five items to the decided list and adds a test that each item
  is required.
- **View (a), recomputed by hand from the index files** (the "judge verifies" item):

  | Step | Value |
  |---|---|
  | Fund return per interval (close change + (earlier Div Yield / 100 − 0.05%) × days / 365) | −1.639272%, +1.301626%, −0.685506% (3 days), +1.607571% |
  | Fund gain on Rs 1,00,000 | Rs 584.42 |
  | Fund gain after 20.8% tax | Rs 462.86 |
  | Cash gain (5.5%, 6 days) | Rs 90.41 |
  | Cash gain after 31.2% tax | Rs 62.20 |

  These equal the test's literal values to the paisa. View (b) follows from the same growth: 20 × 584.42 for the fund
  and an idle Rs 19,00,000 at the cash rate.
- **The fixtures and the archive.** The 7, 8 and 9 Oct fixtures are byte-identical to the archived files (manifest
  SHA-256). The 12 and 13 Oct fixtures differ: they hold four extra index rows that the archived copies lack. Their
  "Nifty 50" rows are identical to the archive, so every figure stands (note 3).
- **The t-check example, by hand:**
  - z = [−50, −175, −150, 75, −50, 350] ÷ 1,333.33, so sd = 0.14475;
  - bound = 0.15 − 2.015 × 0.14475 ÷ √6 = 0.0309;
  - the table's one-sided 95% t values for 1 to 30 degrees of freedom are the standard ones.
- **`claim_allowed` is unaffected.** The disagreement test asserts the claim is unchanged and that the warning is
  appended to `reason`.

## The orchestrator's three decisions

1. **The 5.5% cash rate as a placeholder:** the placeholder itself is fine, but nothing stops it from being frozen
   (finding 1).
2. **Scoreboard A carries no AI or operating cost:** accepted. The standard unit is one lot with no account (S1). A's
   verdict therefore stands for every book, while B withholds an AI book's verdict until F8 is known.
3. **Random-control twins exit at the real exit day's quotes:** accepted as a stated limit. Time exits are the only
   coded exits, so twin and trade normally share the day. Only an E4 retry or an expiry settlement differs, and the
   control is descriptive and never a gate.

## My mutations (each alone, then reverted)

**Caught (15):**

| Area | Mutation |
|---|---|
| Do-nothing | yield of the later day |
| Do-nothing | no expense |
| Do-nothing | cash over 360 days |
| Do-nothing | fund long-term at `>` instead of `>=` |
| Do-nothing | F&O tax on the whole period instead of per financial year |
| Do-nothing | a fund loss taxed |
| Do-nothing | verdict given with the AI cost unknown |
| Measures | drawdown high not starting at 0 |
| Measures | a zero-net trade counted as a loss |
| t-check | no linearisation |
| t-check | `t(k)` instead of `t(k−1)` |
| Random control | ties counted in full |
| Random control | missing cap at 9.9% |
| Missed runs | the report day listed |
| Missed runs | `waiting` not counted as a missed exit review |

**Survived (3):** the oldest remainder kept, the 10-step window at `<` instead of `<=`, and no bucket replay. These
are finding 2.

## Findings

### Should fix

1. **The 5.5% cash rate can be frozen silently.**
   - `Terms.cash_rate = 0.055` is a placeholder; the protocol says "the RBI repo rate on the freeze day, written here
     and in `Terms.cash_rate` ... at the freeze".
   - But `do_nothing_benchmark` is marked "decided by the owner on 2026-10-15", and nothing refuses a freeze while the
     placeholder stands. The freeze hashes the code, so 5.5% would be frozen unless someone remembers.
   - That is a real path: the S1 freeze is scheduled after S3, F9 and E8.
   - **Fix:** make the placeholder detectable and refused at the freeze. For example, put the cash rate in
     `PROTOCOL.md` as a number with a "to be set at the freeze" marker that `evaluation check --decided` and the freeze
     refuse, with the code reading it from there or a test pinning the two equal. Add a test for the refusal.
2. **Three test gaps, each on a path the code takes in normal running:**
   - **t-check, the oldest remainder left out:** keeping the oldest blocks instead survives. The 45-session test uses
     a constant series and checks only the counts. Almost every section has n mod 20 ≠ 0. **Fix:** a known answer on
     a non-constant series where the left-out sessions change the bound.
   - **Random control, the bucket redraw:** removing the `_bucket_room` call from `_twin` survives. The test checks
     `_bucket_room` alone, not that a draw is redrawn, which is criterion 10's wording. **Fix:** an end-to-end case
     where a flip would overfill the bucket and the twin is redrawn.
   - **Random control, the 10-step window boundary:** `<` instead of `<=` survives. Rule 5 asks for the boundary.
     **Fix:** a strike exactly 10 steps away is in the window, and one at 11 steps is not unless it is the real trade's.

### Notes

1. **Scoreboard A's view (a) understates capital.** A take's net sits on its decision day, but its capital is counted
   only on the series' days. A closed take whose exit falls after the series' last day therefore has capital-days cut
   off, so the book looks better per rupee-day. It is descriptive (RM1's gate reads scoreboard B). State it, or extend
   the capital path to each take's exit day.
2. **Twins at the real exit day** (decision 3): accepted, stated limit.
3. **Fixtures for 12 and 13 Oct** are not the archived bytes (four extra index rows; the "Nifty 50" rows are
   identical). Say where they came from in the test docstring, or replace them with the archived copies.

## Project rules

- **Reuse:** S2's resampler and the uncertainty criterion, E4's pricing, C1's `Order`, B2's held model and
  `read_index_figures` are reused.
- **Composition root:** the scoreboard wiring.
- **Size:** every file is under 350 lines.
- **Process:** the self-review is present (1 must-fix and 8 should-fix, 7 applied, 2 stated), and real index files are
  used.
