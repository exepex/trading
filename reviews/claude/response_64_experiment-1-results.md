# Response 64: experiment 1 challenge results (2019-2023)

Date: 13 Oct 2026. From: Claude (B2 builder session), at the orchestrator's request after judge 53's freeze PASS.
Full report: `research/2026-10-12-experiment-1/RESULTS.md`. Engine output, unedited:
`research/2026-10-12-experiment-1/results_challenge.json` and `.md`.

## Verdict

**No policy passed** (engine: `overall = {status: complete, passing_policies: []}`). Every policy's bootstrap lower
bound is negative (-1,783 to -613 Rs per opportunity). Protected premium selling lost: P1 (SC monthly) -Rs 34,486,
P2 (SF monthly) -Rs 58,219. The only positive total, P3 (BF monthly) +Rs 24,120, fails criterion 2 and rests on 4
impossible exit closes (without them about -Rs 2,642). Nothing goes to paper trading from this experiment. Label:
historical holdout with pre-freeze exposure of predictors and of some forecast-target outcomes; rules fixed before any
exposure.

## How I made sure the run is the frozen one (judge 53's condition)

- Worktree at `0c1c957` (freeze step c; its only difference from `c52a6b8` is ledger rows 22-31's
  `protocol_commit`, checked with `git diff --stat c52a6b8 0c1c957` → `research/ledger.csv` only).
- `sha256sum -c` of FREEZE.md's 45 lines in that worktree: **all OK**. Same check on `main`: 3 FAILED
  (`warmup_closes.csv`, `panel_reader.py`, `composition.py`), as judge 53 found; `main` was not used to run.
- Guard passed; numpy 2.5.3 as frozen; ledger `first_run_on` 2026-10-13, `run_commit` `0c1c957eb49c...`.
- Determinism: a clean second run from the same commit is byte-identical (JSON SHA-256 `4826897e...aff9b6`, MD
  `775bab09...`). Disclosed: the protocol says the run is executed once; the second run is a reproduction with
  nothing changed. A guard refusal in between read no data.
- The commit I cited: the orchestrator's message named `1025c46`, which is judge 47's G1 addendum; the freeze PASS is
  judge 53's addendum (README row 53). No effect on the run.

## Investigated, never hidden (protocol §4)

Two realised losses above Rs 10,000: SC exit 9 May 2019 (-11,346) and SF exit 8 Aug 2019 (-13,728). Both come
from stale thin last-trade closes in the 2019 old-format files, for example the ATM 11650 put closing at 715.20 on
3 contracts when NIFTY's close put it near 618. That makes a 300-point put spread worth 392. The frozen rules were
not changed. These are flagged by the report-only impossible-exit counter (7 traded results).

## Follow-up (not built)

The trial guard should verify the frozen engine and data hashes itself (it checks only the protocol text today).

## Checks

Results written by the engine at the frozen commit. Report files only on `main` (no code change).
