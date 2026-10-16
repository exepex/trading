# Judge 310: G13 code, the valuation record and price-distribution forecasts (story/g13-price-distribution at 794877c2)

**Verdict: FAIL, 1 should-fix and 3 minor. Lane 1.** The maths and the numbers are right, to every printed digit.
The should-fix is in the daily rerun path.

The head judged is 794877c2: f4f21feb with `origin/main` merged. The conflicts in O1's files were resolved additively
(the steps run `card`, `price_distribution`, `candles`). G13's own files are unchanged by the merge. O1's owner reviews
the plug-in lines.

## Gates (run myself on 794877c2)
- `pytest -q -n auto`: **7,972 passed, 15 xfailed** (351 s).
- `ruff check` clean; `ruff format --check`: 1,447 files formatted; `check_imports` ok; `check_records` clean
  (6,790 files).
- Largest new file: `records.py`, 170 lines.
- Frozen files: no diff under `fno/forecast/`, `fno/forecast_scoring/` or `fno/forecast_v4*`. No new IV inverter:
  `pricing.py` wraps `Black76`.

## Independent recomputation (a review agent in my session, with its own script and no package import; spot-checked by me)
From the real 16 Oct NSE file:

| Item | Recomputed | Code / fixture |
|---|---|---|
| 27 Oct forward | 23,121.9596 | same |
| 23 Nov forward | 23,225.2246 | same |
| ATM IV, 27 Oct / 23 Nov | 11.85 / 12.73 | same |
| CDF edges, 27 Oct | 0.021709 / 0.989479 | same |
| CDF edges, 23 Nov | 0.103448 / 0.874151 | same |
| Raw decreases | 3 / 10 | same |
| 27 Oct q05 / q50 / q95 (levels) | 22,262.88 / 23,146.82 / 23,821.74 | same |
| 27 Oct q05 / q50 / q95 (log returns) | -3.786% / +0.107% / +2.982% | same |
| Tail quantiles q01 / q99 (27 Oct); q05 / q95 (23 Nov) | equal | same |
| Exact mean (closed form) vs a numerical integral | within 0.001 points | |
| h1 implied (6 sessions; 20 Oct is a holiday) | -0.0155858 | same |
| rv20 | 15.5368 | same |
| hist750 h1 and h5 quantiles | equal | same |
| One QS value by hand | 0.00451935 | same |

These agree with my own probe of judge 304, and with the committed fixture. The dry run writes nothing: the
worktree is unchanged afterwards, and `_value` never builds the store.

## Findings

**Should-fix 1. A rerun turns a day "written with problems" into success.** Strong evidence (code read by me).
`recorder.py` `record()` treats any existing live file as `already recorded`, with no problem attached. That includes
the `missing` placeholder it writes itself for an underlying whose chain was absent, and a record whose own
`problems` list is non-empty.

Effect:
- First run: exit 1, "written with problems: BANKNIFTY no canonical 3 pm chain".
- O1's rerun of the failed step: exit 0, "recorded".

So the day's run log ends `ok`, and O8's health check sees no problem. The owner's go-live gate counts exactly this
kind of hidden failure (row 247, "zero silent failures"). The review agent reproduced it with the test fakes. The
rerun also locks out a chain that arrives late, which is acceptable under write-once, but must be visible.

Fix: when an existing live file holds `status: missing` or non-empty `problems`, report it as "already recorded with
problems: ..." and keep exit 1. Add a test: a first run with problems, then a rerun, still exits 1 with the same
problems listed.

**Minor.**
1. **Two pinned rules have no test** (the agent's surviving mutants; I reproduced one).
   - "Gap at most 200": changing `<= MAX_STRIKE_GAP` to `<` (`density.py:120`) passes all 106 G13 tests.
   - The [0, 1] clip after the pooling pass: removing it survives too.
   - Add a 200-point-gap chain, and a chain whose pooled CDF would exceed 1.
2. **Back-fill does not contain a failed day.** In `backfill.py`, a builder raising `RecordRefused` (a `ValueError`)
   stops the whole range, and the file is lost. Criterion 12 says back-fill never fails a run for one day. Contain it,
   as the recorder already does (count the day and continue).
3. **The claims' "Deviations" section is incomplete.** An unreadable chain or a failed build writes no file (exit 1),
   unlike criterion 12's "writes its missing reason". That is sound, and it is explained in self-review finding 2, but
   list it among the deviations.

## Claims vs reality
- The real-output numbers: true (table above).
- "38 of 38 mutations caught": true for the builder's own set. A different set found the two gaps above.
- The EOD back-fill first scores: made by an uncommitted script (the claims say so). Not reproduced; reasoning only
  for me.
