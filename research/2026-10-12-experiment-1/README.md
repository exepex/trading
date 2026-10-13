# Experiment 1: how to reproduce the frozen result

Experiment 1 is finished; see `RESULTS.md` (no policy passed). The panel files on `main` grow append-only with new
sessions from 14 Oct 2026 (story A13, G1 protocol v3; owner decision in `docs/DESK_DECISIONS.md`). **A run from
`main` is therefore never the frozen experiment.** The frozen result is reproduced only from the worktree it ran from:

```
git worktree add ../experiment-1-frozen 0c1c957eb49cfa3c2ea3efb6b93befa66d6b6928
cd ../experiment-1-frozen
grep -E '^[0-9a-f]{64}  ' research/2026-10-12-experiment-1/FREEZE.md | sha256sum -c   # all 45 OK
pip install numpy==2.5.3                                                               # as frozen
python -m fno research run 2026-10-12-experiment-1 --period challenge
sha256sum research/2026-10-12-experiment-1/results_challenge.json
# 4826897ed4d7e4edf738ec49b926111eb924e3c47cf471fb0aaa73d4e6aff9b6
```

`0c1c957` is the freeze commit `c52a6b8` plus the ledger's `protocol_commit` (step c), which the trial guard needs.
`tests/research/test_experiment_1_frozen.py` checks on every run of the suite that the 45 frozen files still have their
frozen bytes at that commit, and that the published result has the SHA-256 above. It needs full git history
(`fetch-depth: 0`, as CI uses).
