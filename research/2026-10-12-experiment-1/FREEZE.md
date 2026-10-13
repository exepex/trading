# Experiment 1 freeze record

Frozen on 13 Oct 2026 by the orchestrator's decision after judge 53, before any challenge-period (2019-2023) option
outcome, trade P&L, control statistic or verdict was computed or viewed. Protocol section 10 recipe, steps (a)-(c); the
challenge run (step d) is **not** part of this freeze and waits for the judge's re-check.

## Protocol

- Protocol: `research/2026-10-12-experiment-1/PROTOCOL.md`, version 2.2.
- **Protocol commit (step a): `9d16431d5a9e1fdf1f0979de9cc5c605bfd34837`.** The protocol's `frozen at commit` line names it; the engine refuses the
  challenge unless that commit precedes the run and the protocol equals it without that line (`trial_guard.py`).
- Ledger: trials 22-31 (P1-P8, C1, C2) registered in commit `36d9450` (12 Oct 2026); their `protocol_commit` is set
  to the commit that adds this file (step c, next commit), after which the protocol may not change (B4).

## Inputs (SHA-256 at the protocol commit)

Same values as every results file's `inputs` block (`fno.composition.research_inputs`):

| Input | SHA-256 |
|---|---|
| panel_manifest | `89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636` |
| events | `6429b5b243e289fa09d3e4bc1eb141d3dda0c24ef8c0eeb8a81769fa81fb3c19` |
| session_calendar | `e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d` |
| config_terms | `8f65c3ab9e2f1eef4c7f144b56db31956ce22b4c435f261a0ba08a9f29b45118` |
| numpy | `2.5.3` |

`config_terms` = SHA-256 of `json.dumps({charges, lot_sizes, risk_free_rate} of config.yaml, sort_keys=True)`;
`numpy` is the version whose generator streams the draws use (protocol section 7).

Data and settings files (`sha256sum`; the panel manifest also carries each panel file's SHA-256):

```
89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636  research/data/nifty-panel/manifest.json
9ecff0505b63b63f2ffda7a874a2e8d624729f5175ba824f712e52cb11be0bd0  research/data/nifty-panel/warmup_closes.csv
6429b5b243e289fa09d3e4bc1eb141d3dda0c24ef8c0eeb8a81769fa81fb3c19  research/data/events/events.csv
e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d  research/data/calendar/nse_sessions.csv
ecb8cd3f2dadf764f877930ed844942848541a09396b2f0623db70569ab8fa6c  research/data/calendar/exceptions.csv
450da78bf748e83ca316ebe50ea739f5af6487fc1ee2b6fade281e864e201a1d  config.yaml
```

## Engine code (B1-B4 and what they read), `sha256sum` at the protocol commit

```
3d703dce4c0fdef10a1ae392942e7bcf066d154d58ba6e7da60475be950424fa  fno/research_engine/__init__.py
4b3a06c66037e696f83ce37f5db5d4040f50fa12d9af73fd50cec9fc1479356e  fno/research_engine/close_series.py
9df0e75595240e92abc19b4e33a18198421c77cabd58d2ca65f55c1561193d08  fno/research_engine/controls.py
09be77ec0645c37d5730c8f54889380c9531399f401611ae3e1fe359d9db575a  fno/research_engine/cycle_costs.py
0e4f541aa5d9d854d207f4ebb698291e7951b36e53ad43fbe1e9534102289451  fno/research_engine/cycles.py
d3fab68c2a26b2fa04583aeb19be5f39264840e157783cf47f19e0761d09f1e3  fno/research_engine/event_features.py
480edb77412359b9987f7e5685eacc944300d80ee578d7858886c6784beab22c  fno/research_engine/experiment_1.py
557396994303aa5ca57719fa7a87ebdd178900f598f227fe78e6c1076b911a32  fno/research_engine/experiments.py
95deda07b86be6e7855d621d49195bdb3f03cd0bbcfc167315fe0b6717f3efcb  fno/research_engine/features.py
a752d5acaa41649ef6e02dde0e2dec22349fa1d44ee24fee09a7f144eeef60f0  fno/research_engine/implied_vol.py
afcb6539139bad2eaab7d1d076f3420d93897da23e3cff72954f671242f4a2cc  fno/research_engine/ledger.py
a19228ac26d1eba15d02de4aa0cc76dc71b0840fc048a1616342ff2a82d23b13  fno/research_engine/leg_prices.py
249826bfda9971fce35b9d3ba28f708eb11cd0dde70d7fe53e805c998f61f10d  fno/research_engine/live_features.py
681ddf911590b8f366ce6aa5a2b953665080fd067622aa830a48f2fe94cff2f4  fno/research_engine/live_gate.py
956a2ba831c447abc645ec05762ca9851cd94c5474098d12a4ec113d15a4ccfc  fno/research_engine/live_validation.py
f3494d6355ab812a54bd0c5f81995b84e43a472767165c53339b6f0eeffb4856  fno/research_engine/metrics.py
125a2a3ae37f67a8f32f9247994f6cfd035378dda5b58adb328d63e243bc199b  fno/research_engine/opportunities.py
5562c0d4c0408c31f291ecd37eeecd5bd2b44d25f8e6485d0ce3fa478d9d3545  fno/research_engine/period_report.py
ae13ca2c1e24299f421e42939cd121460bc58ffad5aeea21a732575e0fbc4f04  fno/research_engine/policies.py
17d66dd8880dcb88bd0d8ff12881335a9bf727ae858349752c1473a65c1aeb9a  fno/research_engine/research_cli.py
add8fb4c1b7a928cac883eefc65fbbedebcfa67dee869395cab536dac00fbce5  fno/research_engine/results_file.py
c1a6d798ebb02323c56d2f2e3cc6b30e50c5fca277ecf7226a4c422b05025b87  fno/research_engine/runner.py
abee524cffc05398a683569d25847b78868ed6a878e228d5874d12c6280e9c3d  fno/research_engine/simulator.py
f02e32cf036a10ec11e29bda5222ecd22a0edf5e65c7111e5aa271b41e2df528  fno/research_engine/statistics.py
10a947bc86b8c2db78293039692e350ac24c9fb03749f8f94fd99beeee2c5de5  fno/research_engine/structures.py
9613622c5835c142d69a3859185543ca58755cddd35e67abbd4729646ca35ea8  fno/research_engine/trial_guard.py
fc76074af03dcf509f53b3d17ceceeee63c366d80b93082dd2df6a0f942c00af  fno/research_engine/verdict.py
22f371f681e09b83338f625d5532ba5c3b73f6d62c7b9175346738e21ccfb23b  fno/research_engine/volatility_features.py
13b2244a40d83bc8baf12683181ea897aaa431e67be0685f55f0123db2dd6408  fno/research_data/panel_reader.py
0fb6718d5067b8ab40c73123d0a599c8feff4420e8c789b8e1e62a4cb2f1267b  fno/research_data/panel_rows.py
27ea3b0089f488ace4000d3721f0d9464b1eeb6465a55396a694128b75d418b0  fno/research_data/panel_store.py
b2cbed5d0ae98da0962aa77c4f88f0b9ca0073fa004075423a2f7e2c1af75bd4  fno/research_data/expiries.py
279ae45b5dd689f06332cb217a32b9a7b261ee2cd7c2ddedfe54cd60b6c288f6  fno/research_data/calendar.py
794187c4e0a4a6fc3084930f59a14626d02cd07883830709d4b033cc5673f087  fno/research_data/events.py
106738b7be150a34aecc414e172561f2556f237a2da6c4c9f7db22f5342482e1  fno/costs.py
2df14945232de7eff5920eca6e2dd9b249ef5ef367c935700ffdb9dde29b06f2  fno/analytics.py
0e1004a503bf3472968b75d45ffe8d5ee9de0e362b171aa652468fbbe425ae0a  fno/constants.py
7b2c22ccef8818f4580bbe7d3b66d37f8833d9aefb8ba93879aa18f286ec5214  fno/config.py
e160558ea822f416288293672b85caf8efcb0ee8d39771495b7c15d9bfe83109  fno/composition.py
```

Re-check: `git checkout 9d16431d5a9e1fdf1f0979de9cc5c605bfd34837 && sha256sum <the files above>`.

## Access attestation

Protocol section 10 (frozen text) is the attestation: the access since version 2.1, G1's golden file
(`769fac7`), G2's back-fill (`5632bfc`), the judges' own views, the timing line (every rule written by 12:44 UTC
on 13 Oct; first challenge-period derived values at 12:56), the hard rule and the final-report label "historical
holdout with pre-freeze exposure of predictors and of some forecast-target outcomes; rules fixed before any exposure".
While freezing, no 2019-2023 row of the golden or back-fill files was opened.
