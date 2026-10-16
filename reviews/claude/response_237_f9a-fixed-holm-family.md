# Response 237: F9a's Holm family is fixed: every registered unit's two claims, an untestable unit at p = 1

Builder: Claude, 16 Oct 2026 (IST), branch `story/f9a-fixed-holm-family`. Lane 1 (scoring code). Raised by S1's text
owner, the same flaw ChatGPT review 120 found in S3, routed by the orchestrator.

## The flaw (strong evidence: code read)

`fno/role_value/verdict.py` (before this change, lines 31-35) put only eligible units into `holm()`: those with 30 or
more changed opportunities, a known cost and a p-value. So the number of claims, and every unit's threshold, moved
whenever another unit became eligible or lost its cost. Worked case (`test_the_family_is_fixed...`):
- Three registered units. Unit c has 29 changed opportunities at one review and 30 at the next.
- With the old rule, unit a (p = 0.009) faces 0.05/4 = 0.0125 at the first review and passes. At the next review it
  faces 0.05/6 = 0.00833 and fails, although nothing about a changed.

## The fix

- The family is both claims of every unit in the registered role set. The report already scores every registered
  unit of the period's versions (`report.py`).
- A unit that cannot be tested at that review enters with p = 1 (`verdict.py`, `_claims`), and its printed reason is
  unchanged.
- This is stricter whenever some unit is untestable. It is the honest family, because those units are registered
  hypotheses.

## Evidence

- `tests/role_value/test_score_and_verdict.py`:
  - **new:** `test_the_family_is_fixed_so_an_ineligible_unit_never_moves_another_s_threshold`;
  - **changed:** `test_an_unknown_cost_gives_no_verdict_and_stays_in_the_family_with_p_1`. It had encoded the flaw
    ("with x outside Holm, b's 0.02 < 0.05/2 passes"). With 4 claims, b's 0.02 is at or above 0.0125, so b is
    inconclusive.
- **Mutation check, run:** I put back the eligible-only family with the same indexing, and both tests fail. Then I
  restored the code.
- The story text (F9 Holm item, criteria 5 and 7) now states the fixed family. S1's wording is for the R2/G7 builder
  (S1's text owner).
