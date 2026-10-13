# Response 65: story A13, the NIFTY option panel extends daily (stopped at a frozen file)

Date: 13 Oct 2026. From: Claude (builder), for the orchestrator. Task from judge 47 addendum 4.

## What is done

- **Story A13 written** in `docs/stories/A-data-foundation.md`: scope, two design options, acceptance criteria and
  the judge's checks.
- **Not built:** no Actions step, no module, no tests. Each path touches a frozen file, and your rule is: "If the panel
  code is frozen by G1 v1/v2 or by experiment 1, the extension must live in a new module wired in baseline_wiring, or
  you must state plainly why it can't, and stop." I stopped.

## Why it can't be done without touching a frozen file (strong evidence: hashes and code read)

1. **The panel code is frozen by experiment 1.** `fno/research_data/panel_rows.py`, `panel_store.py` and
   `panel_reader.py` are in experiment 1's engine list (`research/2026-10-12-experiment-1/FREEZE.md`). `panel_rows`
   and `panel_store` still match those hashes. `panel_reader.py` already differs: O6's 277b31b changed it, and judge 53
   listed this.
2. **The wiring is frozen by G1 v2.** `fno/forecast/baseline_wiring.py` is in `FREEZE_v2.md`'s byte-checked table
   (all of `fno/forecast/*.py`, at your request to cover the v2 code). A new reader module wired there breaks the v2
   freeze. The live capture would then stop with exit 1 until a version 3 is frozen.
3. **The only path with no code change touches frozen data and two tests.** The capture reads
   `read_nifty_panel(PANEL_FOLDER, ...)`, so appending rows and manifest entries to the existing panel folder would
   reach it without changing code. But:
   - `manifest.json` and the year files are experiment 1's frozen inputs, with their SHA-256 in its freeze record.
     G1 v1 and v2 record them as "grows with new days (A3)", not byte-checked.
   - `tests/forecast/test_golden.py` would fail: `differences` reports every new panel day as "not in the golden
     file".
   - `tests/forecast/test_backfill.py` would fail. Its byte-equality check fails, and so does its `pack_sha256 ==
     panel_pack_sha256()` check, because the back-fill's pack hash is the manifest's hash at its build.

## The deadline

The panel's options end 12 Oct 2026. By the session calendar, Q5's base rate turns `iv30_history_stale` on
**13 Nov 2026**. This corrects my earlier "about 10 Nov": the Diwali holidays push it later. Until then nothing is
lost. After it, Q5's base rate (and Book 1's Q5, which uses the base rate and the model) records "no forecast"; it
never goes wrong.

## Options for the owner, with my recommendation

| | A: append into the panel folder | B: separate folder plus a new reader |
|---|---|---|
| Frozen code changed | none | `baseline_wiring.py`: needs protocol v3 |
| Frozen data changed | experiment 1's panel inputs (its run is done; its record already says re-check by checking out 9d16431) | none |
| Tests to re-scope | v1 golden test and G2 back-fill test, to their own date range (the back-fill's pack hash checked against the manifest at its commit) | none |
| Consistent with the frozen G texts | yes: v2 section 7 says "Q5's base rate needs the panel rebuilt at least every 21 trading days"; v1 and v2 record the manifest as growing | needs v3 text |
| Time to live | about a day of building plus a judge check | v3 text, judge, freeze, then the build |

**My recommendation: option A** (reasoning, based on the frozen texts).
- Both G1 freezes were written expecting the panel to grow in place.
- Experiment 1's challenge run is complete, and its record already pins the reproduction to its commit.
- O6 has already done the same to `warmup_closes.csv`, another of experiment 1's frozen inputs, with approval.
- The test re-scoping fixes a real flaw rather than hiding one. Those two tests check "history as built at a date",
  but today they assume the panel never grows. That fails at the first legitimate A3 rebuild too, not only with A13.

What A needs from you:
- an explicit yes to changing experiment 1's recorded panel inputs from now on;
- an explicit yes to re-scoping the two G tests.

Option B is cleaner isolation but puts a protocol-version change into the live forecasts one day after they start.

## Checks

No code changed. Only this file, the story text and the conversation log were edited. The holdout rule was kept: no
2019-2023 rows of the golden or back-fill files were opened, printed or analysed.
