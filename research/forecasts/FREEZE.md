# Freeze record: forecast protocol, version 1 (story G1)

Protocol commit: `f936156defa3d6e278c674cc3b91596a14a44518`

Frozen on 13 Oct 2026, before any forecast was made or scored. Story G4 runs `fno.forecast.freeze.require_frozen_before`
on the commit of the first scored forecast: this record and the protocol commit must be in its history, and every file
below must still have these bytes. A change to any of them is a new protocol version (a new protocol file and a new
freeze), never an edit; `tests/forecast/test_freeze.py` fails on any such edit.

## Frozen files (checked)

| File | SHA-256 |
|---|---|
| `research/forecasts/PROTOCOL.md` | `6ee3d40d955ebb7805d0e5cc8a0dffc4629d59d3c66e2170ee427bbd091637b8` |
| `fno/forecast/targets.py` | `ae1c53e837c0596a9c409f0ca4c3ac75f32f4e22a9905f9094ad18e1feb45317` |
| `fno/forecast/iv30.py` | `911d623d4790ac19fdfd86e5ab8a4c1590821034bf78366d857661fa45c0f466` |
| `fno/forecast/schema.py` | `c465583109a1865ac2b629acfa6f332bb3fef3cb62fdb0f34b7efe57a680e60a` |
| `fno/forecast/comparisons.py` | `da1804534c64296f62b3104b4e169784203c64eb6fd0c66683d99ab0c7e4f299` |
| `fno/research_engine/implied_vol.py` | `a752d5acaa41649ef6e02dde0e2dec22349fa1d44ee24fee09a7f144eeef60f0` |
| `fno/research_engine/volatility_features.py` | `1b690bb2dc066746fc3e04c8b415b5e1c64b0318e3078258c7cc1b0302dcbd9f` |
| `fno/research_engine/close_series.py` | `4b3a06c66037e696f83ce37f5db5d4040f50fa12d9af73fd50cec9fc1479356e` |

## Inputs at the freeze (recorded, not checked: they grow with new data)

| File | SHA-256 | Why not checked |
|---|---|---|
| `research/data/calendar/nse_sessions.csv` | `e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d` | calendar rows are added each year (A7); targets use whichever calendar is current |
| `research/data/nifty-panel/manifest.json` | `89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636` | the panel is rebuilt when new days are added (A3) |
| `config.yaml` | `450da78bf748e83ca316ebe50ea739f5af6487fc1ee2b6fade281e864e201a1d` | `risk_free_rate` 0.065 is read from here |

## Research ledger

Trials 32-36 (`forecasts-v1`, one per question) were registered in the protocol commit; this commit sets their
`protocol_commit`.

## Access attestation (what was looked at before the freeze, and why)

- **30-day ATM IV on the panel, 2019 to 12 Oct 2026:** counted interpolated, flagged and missing days per year, and
  read five values (1 Sep to 12 Oct 2026) against India VIX, to state the estimator's flag rate and check it is sane
  (protocol section 3). No target outcome was computed.
- **No outcome of any question was computed on real data** for this protocol; the targets were tested on fixture data
  only.
- **Earlier work that touches the questions:** desk meeting 1 (12 Oct 2026, ledger trials 2-4) measured NIFTY 2024-2026
  5/10/20-day direction persistence (50-52% same direction), related to question 1; story B1 measured F1 (ATM IV minus
  trailing 20-day RV) on 2024-2026 decision days, related to questions 3 and 5. The baselines' and Book 1's methods
  were fixed from design 12.7 and the stories, not tuned on these results.
