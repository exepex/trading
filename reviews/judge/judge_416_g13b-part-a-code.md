# Judge 416: G13b part A code, NIFTY and BANKNIFTY 15:45 ranges (story/g13b-price-ranges at 1bed71ca and c6252d0a)

**Verdict: FAIL, 3 should-fix findings and 4 minor. Lane 1.** Number claimed with O12's tool.

The maths is right to the cent. A review agent in my session recomputed every forecaster for NIFTY on 21 Oct from
the real chain and closes, without importing the package, and the package matched exactly. I checked the key items
myself. The findings are a dropped failure, a missing guard, tests claimed but empty, and an overstated evidence
label.

## Gates (run myself)
- **1bed71ca merged with today's `origin/main`:** 8,751 passed, 16 xfailed; ruff, format (1,609 files), imports and
  records (7,225) clean. The only conflict was `docs/WORK_REGISTER.md`, which I took from `main` for the local run;
  nothing was pushed.
- **c6252d0a (the cache-prefix fix):**
  - the fix commit only builds both scorers' Drive-cache folder from each package's `folders.py`, with no trailing
    "/" (which `path_parts` refuses);
  - G13 and G13b tests: 185 passed;
  - putting back the old constant fails one test in each package.
  - **Note:** this fixes a live bug in G13's merged `pricedist score`, which fails on `main` against real Drive until
    this lands.

## Recomputation (agent's script `scratchpad/g13b_judge/recompute.py`, run with `python -I`)
NIFTY, 21 Oct 2026, live basis:
- `S_ref` 22,675.15 at 14:57:49 (Groww canonical; NSE 22,680.45 at 14:55:25 as the fallback);
- 2,413 closes before d (20 Oct is a holiday); rv20 daily σ 0.0101649; EWMA s² 8.8281e-5; t4(0.95) 2.13185.
- **Equal to the package at every quantile:** rv20, ewma_t4, hist750 and implied, at N1 and N3. Implied uses share
  (k + 0.0486)/(n + 0.0486) = 0.259 and 0.753 for the 27 Oct expiry.
- **QS by hand:** 0.0031922 = package. `no_change` QS = |log error|.

## Findings

**Should-fix 1. A close-table or seal failure is dropped when no chain was captured.** Strong evidence: code read by
me (`fno/price_ranges/issuer.py:99-100`), plus the agent's repro.
- When every underlying is absent, `record()` returns `0, [*lines, NOTHING]`, so any failure collected earlier (the
  `before()` close-table or seal step: BEFORE_FAILED) never reaches the output.
- Repro: `before=raise OSError`, with no chains. Output: exit 0, "nothing written: ... no canonical 3 pm chain"; the
  OSError line is gone.
- Story A9 says such a failure is a problem line with exit 1. On a no-chain day the owner would see only "no chain",
  never the seal or close-table failure. That breaks "every failure alerted and recorded".

Fix: carry the earlier `problems` into the all-absent return (exit 1 when any exist). Add a test.

**Should-fix 2. "Back-fill is never counted live" and three other claimed rules have no working guard or test.**
Strong evidence: code read, plus surviving mutants.
- `RangeBackfill.run` (`backfill.py:40`) accepts any label, and the production `check_row` call (`records.py:49`)
  passes no `label` or `issue`, so the checks at `records.py:57-58` run only in a direct test.
  - Repro: `RangeBackfill(...).run("live", ...)` writes `backfill/live_...`, and a score report over it counts an
    unsealed back-fill as a sealed live day. That is only unreachable today because the CLI passes a constant (the
    CLI-labelling mutant M22 survives).
  - An unknown issue raises a bare `KeyError` at `build.py:328`, not `RecordRefused`.
- **Criterion 7's tie rule:** the test uses `p_up = 0.5`, where Brier is 0.25 either way, so counting a tie as "up"
  survives (M19, M20).
- **"Under 40 paired days: not tested":** no test (M27 survives).
- **The 90% band's lower edge** is never exercised (M32 survives).

Fix:
- `RangeBackfill` refuses any label other than the back-fill labels;
- `check_row` gets the row's label and issue in production;
- an unknown issue raises `RecordRefused`;
- add tests: a tie with `p_up != 0.5`, a group under 40 days, an outcome between q05 and q25.

**Should-fix 3. The claims' "strong evidence" headline is overstated.** Some evidence (statistics; the agent's
reading, which I checked against the claims text).
- Claims line 144 labels "the option-implied range is the best of the five" as **strong evidence**.
- It rests on back-fill only, on the end-of-day basis (`S_ref` = d's close, tail 0, panel traded closes). That is not
  the live method under test.
- Its N1 edge is bootstrap p of about 0.04 against 4 baselines per horizon, with no multiple-comparison correction.
- BANKNIFTY is significant at N3 only.

Under CLAUDE.md's labels this is **some evidence** (N3), not strong. The owner reads these headlines to decide trust.
Fix: relabel it, state the back-fill basis and the uncorrected p, and keep the label honest wherever the headline is
repeated (FL1's reports).

**Minor.**
1. `RV_YEAR` (`constants.py:35`) is dead. `_daily_sd` (`forecasters.py:148`) duplicates G13's rv20 arithmetic
   instead of importing it (DRY; the story says "reused by import").
2. Story criterion 3 says the t(4) closed form matches tables "to 1e-6". Against 4-decimal tables that is impossible,
   and the test uses 1e-4. Say 1e-4.
3. `hist750`'s `p_up` rule (r > 0 versus r ≥ 0) is untested (M14 survives).
4. The issue is labelled "1545", but O1 runs it right after `quotes_done` (about 15:15-15:30). Point in time is
   unaffected (d's close is never read). Say so beside `issued_at`.

## Mutation summary (agent's 32, each restored)
25 caught: tau constant, implied share (two ways), sqrt scaling, rv20 window and tail, ewma √2, t4 coefficient and
normal swap, Ewma day, N3 scaling, hist window, seal `>=`, unknown push time sealed, `no_change` band, late rows
scored, label pooling, the d-close read, all closes read, `S_ref` source, rerun problems, underlying pooling, implied
`p_up`, the 7-day unknown store. 7 survived: M14, M17, M19, M20, M22, M27, M32. M17 (no next session treated as
sealed) is also untested; add it with should-fix 2's tests.
