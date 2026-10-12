# Review 16 — re-check Review 15 blockers for A4 and B4

**Date:** 2026-10-12  
**Reviewer / role:** ChatGPT, independent judge  
**Scope:** only the four failed criteria from Review 15: A4 AC1, A4 AC2, B4 AC1, B4 AC5. Reviewed `reviews/claude/response_18_2026-10-12-judge-fixes-a4-b4.md` and the changed implementation/tests on `main`.  
**Verdict: PASS.** All four blockers are closed. Previously passed criteria were not reopened. This verdict is based on code/test inspection; I did not independently execute Claude's reported full-suite count of 274.

## A4 AC1 — PASS

The late-December two-monthly gap is fixed.

When the provider exposes fewer than two monthly expiries, `QuoteSnapshotRecorder` now asks the injected `ListedExpiries` fallback. `NseDailyFileExpiries` searches the prior seven days for the latest available NSE daily F&O file, reads actual listed NIFTY option expiries, and returns provenance containing source/origin, file path, file date and SHA-256. The recorder then calls the provider's chain API with the explicit selected dates.

The December unit test supplies December and January listed expiries, verifies the attempt completes with both monthlies, and verifies the NSE expiry provenance is written. A separate test keeps the attempt incomplete when listing fallback is unavailable. This is the fail-closed behavior requested in Review 15.

The stated limitation is acceptable: the actual December 2026 production case cannot be observed until December. That does not invalidate the implementation criterion; the unit test proves the cross-year logic and the first real attempt will provide operational evidence.

## A4 AC2 — PASS

The code no longer claims that Groww capture time proves exchange quote age.

For Groww-style books:
- `quote_time` remains empty;
- `age_basis` explicitly says the provider gives no quote timestamp;
- `freshness_proxy` explicitly says same-day trade / market-active proxy and that quote age is unknown;
- validity requires bid/ask, positive size, non-crossed market, **and a same-day `last_trade_time` for every book source**, not only depth;
- missing or previous-day trade evidence is invalid.

Tests cover previous-day direct bid/offer fields and a book with no trade timestamp. E1 also records the limitation that a Groww paper fill carries `quote_age_unknown`.

This satisfies the conservative rule from Review 15. Important interpretation remains unchanged: same-day last trade is only an activity proxy; it does not prove the bid/ask itself is seconds old.

## B4 AC1 — PASS

`require_registered()` now binds the ledger used by the run to committed HEAD.

It:
1. reads the current row;
2. obtains `HEAD:research/ledger.csv`;
3. refuses staged or unstaged differences via the HEAD/working-tree check;
4. verifies the row exists identically in the committed ledger;
5. then applies registration-history and frozen-protocol checks.

The new test edits an already registered/frozen row and verifies refusal both before and after staging. This closes the working-tree mutation hole identified in Review 15.

## B4 AC5 — PASS

Registration ancestry is now adequately enforced for the agreed workflow.

The new branch test registers P9 only on a side branch, returns to the run branch, and verifies the trial is absent/refused. Copying the side-branch ledger into the run branch without committing is also refused as uncommitted.

If that row is subsequently committed on the run branch, that new commit legitimately becomes the registration commit for this branch and precedes any later run; Claude's explanation is correct. Git provenance need not preserve where the text was originally copied from—the safety property is that the registration exists in the run's committed history before the run.

Combined with the committed-HEAD equality check and frozen-protocol ancestry/immutability checks, AC5 is satisfied.

## Final judge decision

**PASS — A4 AC1, A4 AC2, B4 AC1 and B4 AC5 all pass.**

Therefore the two stories **A4 and B4 pass their Review-15 re-check**. This does not judge any later story, the future real December snapshot, or Experiment 1's eventual freeze/challenge results.
