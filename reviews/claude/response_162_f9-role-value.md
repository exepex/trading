# Response 162: story F9a, role-value scoring code (so S1 v1 can freeze); story text for the judge

Builder: Claude, 15 Oct 2026, branch `story/f9-role-value` (issue #61). Lane 1 (a new story; scoring). Orchestrator:
session_01VG1RqxLFUVdvvPuMRYZtDH. **Text only: no code until a judge PASSes this text.**

## What and why

- REPLAN slice B and S1's `frozen_files` (owner's option A, 14 Oct 2026): S1 v1 is frozen only once F9's code exists, so
  every scoring rule is hashed before the first counted decision. **Strong evidence** (the two texts say so).
- So F9 is split: **F9a** builds only the scoring code on records (rotation, record checks, score, interval, review
  gate, control counts, report). **F9b** (slice E) makes the shadow decisions and writes the records. F9a reports
  nothing real until books 2-3 trade. **Reasoning only** (the split is my proposal).
- Story text: `docs/stories/F-ai-layer.md`, section F9.

## Claims (to check against the text)

1. F9a values both actions of a pair by importing S3's `fno/scoreboard/standard_unit.py` (orchestrator, 15 Oct 2026;
   S3's text on `story/s3-scoreboard-a`, item 2), never a copy. **Revised:** my first text read pre-valued nets from
   the rows. That is worse: the standard unit values through the time exit and E7 settlement on later snapshots, so a
   net stored on the day would be incomplete, and the valuation path would sit outside the hashed scoring code.
   Open actions are cut and listed, as in S3. **Strong evidence** (S3's text); F9a's code round waits for S3's merge.
2. F9a reuses F8's `allocate` for cost (shares are already keyed `(purpose, book, role_or_bundle)`,
   `fno/budget/allocation.py:21`). **Strong evidence** (read the code).
3. F9a cannot reuse an existing bootstrap: `fno/scoreboard/uncertainty.py` is a ratio of net to risk (and not mine to
   change), and `fno/forecast_scoring/block_bootstrap.py` is pinned to protocol v2's frozen constants (seed 20261013,
   linear percentiles). A third small bootstrap is the honest cost of three frozen protocols. **Strong evidence**
   (read the code); whether to unify them later is a judgement call (reasoning only).
4. Control roles are scored from C4's failure log only (`fno/checks/validity_failures.py`: one row per failed check,
   with `opportunity_id`). C3 keeps no per-book refusal log, so C3 is a Known limit. **Some evidence** (I read the
   C3 gate's code, not every caller).
5. No file over 350 lines: about six small modules (role set and rotation, paired-row source and checks, score,
   bootstrap, controls, report and CLI). **Reasoning only** until built.

## Questions for the owner (via the orchestrator), each with my recommendation

S1's text leaves these open; the code must fix one answer before the freeze.

1. **"One-sided 95% interval" with two ends.** `role_value_minimum_sample` drops on "upper end below zero" and keeps on
   "lower end above zero", but a one-sided interval has one end. Options: (A) 5th and 95th percentiles, each a one-sided
   95% bound (a 90% two-sided interval); (B) 2.5th and 97.5th. **Recommend A**: it matches the words "one-sided 95%"
   for each claim, and nothing is dropped automatically. Reasoning only.
2. **Holm across roles.** `uncertainty_criterion` applies Holm when several claims are made at one review. With 6
   units each tested at 5%, the chance of at least one false "drop proposed" is about 26% (1 - 0.95^6). Options:
   (A) no Holm, because every verdict is only a proposal the owner decides; (B) Holm across a book's units at each
   review, using bootstrap one-sided p-values. **Recommend B**: it is what S1 already says for claims, and a false
   "drop" costs a role that may help. Some evidence (the arithmetic), reasoning for the choice. It adds about 20 lines.
3. **Cost per opportunity.** Options: (A) the unit's allocated cost over the period divided by every day its card was
   consulted (it runs every day, ablated only 1 day in n); (B) divided by ablation days only (overstates the cost n
   times). The shadow session's own usage is evaluation cost, recorded under its own purpose and shown apart, not
   charged to the role. **Recommend A** plus the separate evaluation line. Reasoning only.
4. **Blocks.** "Blocks of 20 ablation days of that role": I read it as 20 of the unit's applicable opportunities in
   date order (with n units, about 20n trading days). **Recommend** that reading; say so in S1's text. Reasoning only.
5. **Shared input with S3: settled** by the orchestrator (15 Oct 2026): F9a imports `standard_unit.py`; any
   change to it goes through the orchestrator to S3's builder.
6. **S1's `frozen_files`.** F9a's files (`fno/role_value/*.py`, not `wiring.py`/`cli.py`) must join the list; that is
   S1's text, so I propose it to S1's owner rather than edit it.

## Known limits

In the story text: no rows until books 2-3 trade; 30 changed opportunities may take years; F9a trusts the rows'
hashes (F9b tests the real withholding); C3 not counted; the shadow's own usage shown apart.
