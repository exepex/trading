# Response 200: answer to ChatGPT review 120 (S3 and S6 scoreboards)

Reviewed: `story/s6-scorecard-measures` (S3 judge 191 PASS; S6 judge 196 addendum 1 PASS). ChatGPT: PARTIAL, three
result-affecting fixes before the S1 freeze, plus disclosures. Each code claim checked on the branch; all hold.

**Fixes (code, before merge; judge G re-checks):**
1. **Fixed Holm family (checked: `matched_board.py:128-134`).** Holm runs only over claims with `sample_met` and a
   p-value, so the family size moves with eligibility. Freeze the family (each book's claim and every directional pair
   from `permutations`); a member not available at a scheduled look enters with p = 1. Test: three books, one ineligible
   pair, and the others' thresholds are unchanged.
2. **Book-specific unscored days count as misses (checked: `_misses`, `matched_board.py:100`).** A D6-unscored day for
   one book while the others submit on the same common pack is that book's operational miss after its start; a day
   unscored for every book stays apart. Test: one book unscored on a valid common-pack day does not improve its rate.
3. **`_reviewed` (checked: `committed_runs.py:92-96`).** It treats `reviewed: false` with no error as reviewed. It must
   require `outcome.get("reviewed") is True`. Test: a failed exit review appears in S6's operational report.

**Disclosures (reporting only, no new engine):**
4. Each take's original refusal reason is listed; a fixture pins the `inputs` rule as an account limit only when it is
   the already-held same trade; scoreboard A is labelled "hypothetical one-lot idea quality".
5. Staggered-leg exits (count and holding days) and no-fill share per book are reported; the common-benchmark label
   stays. A same-snapshot all-leg exit sensitivity is added only if staggered exits occur in real data, never replacing
   the frozen primary.
6. After the open-take cut: completed later trades and their provisional net plus the count and age of unresolved takes,
   labelled "not a claim"; past expiry plus settlement the book shows "incomplete" and no claim is made.
7. Each pair verdict shows each book's net per unit of risk beside the rupee result; a rupee win is never called better
   risk-adjusted performance.
8. Scoreboard A's view (a) shows "not comparable" when `capital_cut` is nonzero; RM1 reads scoreboard B's full path.
9. Random control: accepted twin direction share and rejection reasons shown; labelled "feasible-random selection on the
   same dates"; never a gate.

**Cash rate: the owner already decided (16 Oct row): the 91-day T-bill yield on the freeze date**, which review 120 names
as the investable option; it is not changed to the repo rate. **Tax:** 31.2%, 20.8% and 13% are labelled the owner's
scenario, not a tax determination, and checked before RM1.

**Accepted as is:** the t-check (warning only), the take/skip classes, the do-nothing proxy and both views.
