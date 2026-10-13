# Freeze record: forecast protocol, version 1 (story G1)

Protocol commit: `cf489e4c53714ce0fffae61db8850b49648ac391`

Frozen on 13 Oct 2026, before any forecast was made or scored, after:
- ChatGPT review 28, section 2 (`reviews/chatgpt/review_28_2026-10-13-protocols-and-build-order.md`): "CHANGE before
  freeze: (1) and (2); everything else can remain". Both changes are applied: question 5 is void on flagged or missing
  IV30 days, and the confirmatory family is 10 tests (Book 2 and Book 3 against Book 1, per question).
- The orchestrator's check and acceptance of review 28 (`reviews/claude/response_60_2026-10-13-on-review-28.md`), and
  its decision that the G-protocol freeze conditions are met.
- Judge 47 round 2, which accepted the behaviour freeze: golden values in place of library bytes.

Story G4 runs `fno.forecast.freeze.require_frozen_before` on the commit of the first scored forecast. This record and
the protocol commit must be in that commit's history, and every file in the first table must still have these bytes.
A change to any of them is a new protocol version (a new protocol file and a new freeze), never an edit.
`tests/forecast/test_freeze.py` fails on such an edit, and `tests/forecast/test_golden.py` fails on any change to a
golden value.

## Frozen files (checked byte for byte)

| File | SHA-256 |
|---|---|
| `research/forecasts/PROTOCOL.md` | `a4f96c15dafb7180b1cfb5b5bce4fdc58cf82eac9ad35622e4d7d8548a6a0463` |
| `research/forecasts/golden_iv30_rv20.csv` | `dcb011864502dca2566ff168c6014187e17292d03a8f756a60c7fbab0f1355c5` |
| `fno/forecast/__init__.py` | `a0cda94272be5f444276f76e8a8e439c233b911ce286d62e8e421a167dc3122f` |
| `fno/forecast/comparisons.py` | `bacf46dd4fe5063b32159e3ac87c01863e393fbe441e0dcdb416f63280d2412b` |
| `fno/forecast/freeze.py` | `bbe321c82ea3f0275af70dd869dcca3938ef55c031df742d2b0fb96e6f9c4b89` |
| `fno/forecast/golden.py` | `cdb4b34a7889bb7817357002d1e2d115ed17713b76e0ae4569b4fc9cb0f6a7e8` |
| `fno/forecast/iv30.py` | `911d623d4790ac19fdfd86e5ab8a4c1590821034bf78366d857661fa45c0f466` |
| `fno/forecast/schema.py` | `c465583109a1865ac2b629acfa6f332bb3fef3cb62fdb0f34b7efe57a680e60a` |
| `fno/forecast/targets.py` | `5d1c7b639d40e3ba781c6844d52367e4329d3a38cf853e3eeeabd03ee610f616` |
| `fno/forecast/wiring.py` | `e63c5fc439f8b262558a8d620b394159c9b34920aa34399b4b0e436ad3658916` |

**The golden contract** is `golden_iv30_rv20.csv`: for each of 1921 panel trading days from 2019 to 12 Oct
2026, it holds IV30's value, its flag and the expiries used, plus the trailing RV20.
- **Flag:** the flag is part of the contract. 258 days are flagged (13.4%); these are void
  for question 5's primary score.
- **Missing:** 1 day has no IV30.
- **Recompute:** `python tools/forecast_golden.py`.

## Recorded, not byte-checked

| File | SHA-256 at the freeze | Why not checked |
|---|---|---|
| `fno/research_engine/implied_vol.py` | `a752d5acaa41649ef6e02dde0e2dec22349fa1d44ee24fee09a7f144eeef60f0` | B1's Black-76; behaviour locked by the golden values |
| `fno/research_engine/volatility_features.py` | `22f371f681e09b83338f625d5532ba5c3b73f6d62c7b9175346738e21ccfb23b` | B1's ATM IV; behaviour locked by the golden values |
| `fno/research_engine/close_series.py` | `4b3a06c66037e696f83ce37f5db5d4040f50fa12d9af73fd50cec9fc1479356e` | B1's realised volatility; behaviour locked by the golden values |
| `research/data/calendar/nse_sessions.csv` | `e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d` | rows are added each year (A7) |
| `research/data/nifty-panel/manifest.json` | `89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636` | the panel grows with new days (A3); a revision of past days is an A11 revision |
| `config.yaml` | `450da78bf748e83ca316ebe50ea739f5af6487fc1ee2b6fade281e864e201a1d` | `risk_free_rate` 0.065 is read from here |

A panel revision (story A11) that changes a past day's inputs may move golden values only together with that
revision, named day by day. The amended golden file's hash is then recorded here, citing the revision (protocol
section 10).

## Research ledger

Trials 32-36 (`forecasts-v1`, one per question) were registered before any forecast. This commit sets their
`protocol_commit`.

## Access attestation

Protocol section 11 lists what was looked at before the freeze. No outcome of any question was computed on real data.
