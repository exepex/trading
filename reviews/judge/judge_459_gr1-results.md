# Judge 459: GR1's results (run 2 at 56fe1c8f, response 314 at 4cdbd8bc)

Judge B, 22 Oct 2026. This is the last review step of protocol section 12 (step 5). Builder: G13/G13b
(session_01UkTaDeTRF9ksDgQB9cTU5C). Number claimed with `tools/claim_number.py`.

## Verdict: FAIL (2 should-fix, both wording in response 314)

The numbers and the conclusion stand.

## What I verified myself

| Item | Result |
|---|---|
| Run once | `final.json` exists in exactly one commit (56fe1c8f, `git log --all`), after the selection commit 476aa240. The only code change since the freeze is none: 56fe1c8f adds `final.json` alone |
| Reproduction | On a worktree of 476aa240 (the frozen code 08731ac6 plus the committed `selection.json`), I called `guard.check_code`, then `study.run_final(...)` through the same `encode`, reading the data through the verified Drive cache. My output's SHA-256 is `55f636f30d8fec362993582808498b50aac478ebc9b99438c18ee1167e554f62`, **equal to the committed file**. It names `selection_sha256` 083756a0 and `records_sha256` 6f39e4de |
| The verdict table | matches `final.json` (below) |
| Ledger and DATA_SPEND | rows 56-66 and 68-70 now carry the run date and run commit 08731ac6; row 67 (not tested) has none. `LEDGER.md` gives the result, and the global cues are `exposed`. Lane-3 record rows, consistent with the run |

The verdict table, checked against `final.json`:

| Cell | Winner | Paired mean difference | 95% CI | p | Holm | Verdict |
|---|---|---|---|---|---|---|
| NIFTY/N1 | C8 | +1.84e-5 | [-0.13e-5, +3.40e-5] | 0.048 | not significant | not sharper |
| NIFTY/N3 | C9 | +1.16e-5 | | 0.319 | | not sharper |
| BANKNIFTY/N3 | C10 | +1.26e-5 | | 0.335 | | not sharper |
| BANKNIFTY/N1 | none | | | | | not shown at this sample size |

Implied's coverage figures, C1's and C2's -0.13% to -0.20% on the N1 cells (590 against 611 points, 1,490 against
1,611), and the N0 table (0.779 / 0.751 / 0.730; N0-A 0.900 / 0.507) all match `final.json`.

**Conclusion (strong for its stated scope, exploratory by status):** none of the three 2024 winners is sharper on
2025 - 20 Oct 2026, and all three point the wrong way. The intervals bound how much any of them could help:
- C8: at most about 0.03% of QS;
- C9 and C10: at most about 0.13-0.14%.

Implied stays. That is the protocol's honest negative result.

## Should-fix 1: the C9 split quoted is NIFTY N1's, not the winner's cell

Response 314 says the weekday effect "changes sign with the expiry day" and quotes NIFTY N1: -3.2e-5 before 1 Sep 2025
and +0.8e-5 after. But C9 was the winner of **NIFTY N3**, and its own split in `final.json` is:

| Segment | Paired difference | Sessions |
|---|---|---|
| before 1 Sep 2025 | +0.43e-5 | 164 |
| after 1 Sep 2025 | +1.59e-5 | 276 |

So C9 was worse than implied in both pieces, and more so after the change. The N1 pattern may be quoted too, but the
cell decided on must be the one shown, and "consistent with an expiry artefact" should rest on both cells.

**Fix:** give NIFTY N3's split first, and label N1's as a cell where C9 was not the winner.

## Should-fix 2: two evidence labels say more than the data allows

- **(a) N0-A's coverage.** N0-A is called "the honest one ... no fitted parameter". Its share of 0.607 was measured by
  G13b on **2020-2025**, which overlaps the final period's 2025. Protocol section 11 says this share is exposed. So
  N0-A's 0.900 / 0.507 coverage on 2025-26 is partly in-sample, and "supports phase 2's 09:15 issue [some evidence]"
  needs that caveat. The clean check is N0-A on sessions after the share was measured (from 2026, or prospectively
  from A22's live 09:15 data).
- **(b) The headline label.** "Strong evidence for these candidates" should say what is strong: "strong evidence that
  none of the three improves QS by more than about 0.15% on 2025-26 (exploratory: spent data)". As written, it reads
  like strong evidence that no conditioner can ever help.

## Notes (one line each)

1. **The first Tuesday expiry was read outside the frozen code.** `splits.py` promised that run 2 would report it;
   the builder read it from run 2's own expiry cache instead (29 Aug 2025 file, expiry 2 Sep). It is disclosed and only
   descriptive. Mark it in the results as "read outside the frozen code".
2. **The late-December 2024 rows** read January 2025 outcomes in run 1. This is disclosed, as judge 442 asked.
3. **Q-GR1 (a prospective trial of a constant N1 shrink from 21 Oct 2026)** is rightly marked untested and post hoc.
   C1 and C2 are also the "known before the study" candidates (judge 428). Any such trial must be registered before
   any data from 21 Oct is read, and its protocol must cite this result as its origin.
4. **For the owner:** the 2024 winners' gains were 0.2-0.8% of QS and all reversed on new data. Large candidate sets
   on one year of selection data mostly find noise. This is the first measured case in this project.

## To pass

Fix both should-fixes in response 314. They are wording only; no number changes. Then the branch may merge, keeping
the freeze commits in history (a merge commit).
