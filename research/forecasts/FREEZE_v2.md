# Freeze record: forecast protocol, version 2 (story G1 v2, the interim live input pack)

Protocol commit: `ab2e81193eb14ba97f1902bbc983e34c17d68769`

Frozen on 13 Oct 2026, before any live forecast was made or scored, after:
- ChatGPT review 29, section 2: eight changes for a live 15:00 input pack. The orchestrator checked and accepted all
  eight (`reviews/claude/response_63_2026-10-13-on-review-29.md`).
- Judge 47 addendum 3: PASS, ready to freeze. The judge checked 1b57cb3: all eight changes are in the text and the
  code, the 15:00:01 plant was caught, and v1's frozen files are unchanged.
- The orchestrator's confirmation to freeze.

Version 1 (`research/forecasts/FREEZE.md`, protocol commit cf489e4) stays frozen and unchanged.

**The check.** `fno.forecast.freeze_v2.require_version_frozen` runs before every live capture (`python -m fno forecast
capture`). It requires:
- this record and the protocol commit in the history of the running commit;
- the protocol text at that commit hashing to the value below;
- every file in the first table still having these bytes.

**What it covers.** The table covers the v2 code itself, not only the protocol text: the live pack, the history and
its gates, the closes source, the v2 schema, the capture, the freeze check, the command line, and the v1 forecast code
they use. It also covers the golden tool and every input and output file of the two v2 golden cases.

**What happens on a change.** Any change to these files stops the live capture with exit 1 and a #fno-desk alert; it
then needs a new version. `tests/forecast/test_freeze_v2.py` checks the real repository and plants an edit.

## Frozen files (checked byte for byte)

| File | SHA-256 |
|---|---|
| `research/forecasts/PROTOCOL_v2.md` | `5417b9557f348b765aa7f3662b915a55b5a134cdff7e8b89bd4d9834c403ff4e` |
| `fno/forecast/__init__.py` | `a0cda94272be5f444276f76e8a8e439c233b911ce286d62e8e421a167dc3122f` |
| `fno/forecast/backfill.py` | `e3feb76289c5798e0c35365c90e731325f2915ea94be9fe9e3c41d78bc9cf730` |
| `fno/forecast/baseline_wiring.py` | `0df32dbcf879de72d04454a771ffe16c5f35994d61981cfc0479fc1523a21258` |
| `fno/forecast/baselines.py` | `3cd873396e64e5324486b2b8153c2481710f0d92af945b4026d549591439e44c` |
| `fno/forecast/book1_method.py` | `ddfb6e62d1317b5ac0289270c53a2f033ac6053ea8af8d5cd9f8af23dae4b8e0` |
| `fno/forecast/capture.py` | `5c618d17215b43ecd913d1a2c6aa4f88c6b0f68ccef8787eed04df1b27de8272` |
| `fno/forecast/cli.py` | `71009865dd19b61a4fa733c17e19c57b8ac6c93ce1bc59f02c2b35e15f9b13fd` |
| `fno/forecast/closes_source.py` | `1d97d6e0ac3c7aa12260ffe393837338da7a5176c9b9fd10c4416928f243971e` |
| `fno/forecast/comparisons.py` | `bacf46dd4fe5063b32159e3ac87c01863e393fbe441e0dcdb416f63280d2412b` |
| `fno/forecast/freeze.py` | `bbe321c82ea3f0275af70dd869dcca3938ef55c031df742d2b0fb96e6f9c4b89` |
| `fno/forecast/freeze_v2.py` | `ab342b389048b28d4cc8164c09049599a6f5fbc8da89741bb37ebf77629c84a2` |
| `fno/forecast/golden.py` | `cdb4b34a7889bb7817357002d1e2d115ed17713b76e0ae4569b4fc9cb0f6a7e8` |
| `fno/forecast/history.py` | `cf779f0cb7d6e43daed4a47424f0e72dd4b47bda5690a68d63488b75657c3e75` |
| `fno/forecast/iv30.py` | `911d623d4790ac19fdfd86e5ab8a4c1590821034bf78366d857661fa45c0f466` |
| `fno/forecast/live_history.py` | `acedaa97381b288161a081851904ee11ea6a7e22d8bdb209689ddf0da27ec41a` |
| `fno/forecast/live_pack.py` | `279eb12b15a798e0eefcabb3bfacfc28371be6852e74166beeea8c38fcef706c` |
| `fno/forecast/models.py` | `54c846b67c1322b06aff18ae71a66aec4d9c7e7e70de2038ccf06921abf95ad9` |
| `fno/forecast/record_files.py` | `49a8fbb75485dcd45923549da8dccc950af931ba33dd64239cab8c6f3992c160` |
| `fno/forecast/schema.py` | `c465583109a1865ac2b629acfa6f332bb3fef3cb62fdb0f34b7efe57a680e60a` |
| `fno/forecast/schema_v2.py` | `75da00476ef6f25d5da73d8fda66980f21391a902475e24bd52fdab7d1e10e62` |
| `fno/forecast/targets.py` | `5d1c7b639d40e3ba781c6844d52367e4329d3a38cf853e3eeeabd03ee610f616` |
| `fno/forecast/wiring.py` | `e63c5fc439f8b262558a8d620b394159c9b34920aa34399b4b0e436ad3658916` |
| `tools/forecast_live_golden.py` | `8f3d6067c37b64658fbacf69d7a349e4b964a85dbe82e4627e99ec70c4fada8f` |
| `research/forecasts/v2/golden/case_a/forecasts.csv` | `fdd53f23f64e77215287f485b06e70c0b49aa01c98c12a18da4ddb99666e8f76` |
| `research/forecasts/v2/golden/case_a/pack.json` | `a7c1a25106ab30aaded014e3171e09ccbd33e7bd3391479b1a8a2ccb70df7a68` |
| `research/forecasts/v2/golden/case_a/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013.canonical` | `f763c65ee06bbabeaf0c9f38c9ee1f38075b5e46fc61f76a0eb7137a50904e13` |
| `research/forecasts/v2/golden/case_a/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013_145600.csv` | `25a5f9ea9dfb80706b019e61cadb926e62731f185cbfc64f816c6f09bd24e6ff` |
| `research/forecasts/v2/golden/case_a/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013_145600.meta.json` | `b6bb667cf82f787f7b057d510a6c24d4e46bfe19a87d3d21368c63a37e0a4fa3` |
| `research/forecasts/v2/golden/case_b/forecasts.csv` | `8232410bcc79a5052e19b82ee5ccc4f3e2ec781122a0ebe617def961e7d906ae` |
| `research/forecasts/v2/golden/case_b/pack.json` | `e3ddc0f7c35a242f75cc96ec86273608e3c55ae0a94a37f731f11e3390c1f524` |
| `research/forecasts/v2/golden/case_b/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013.canonical` | `f763c65ee06bbabeaf0c9f38c9ee1f38075b5e46fc61f76a0eb7137a50904e13` |
| `research/forecasts/v2/golden/case_b/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013_145600.csv` | `a4ada9568e760ab6ea3047a0de98d0f81a84f675ce154129cd604f0aa87ffe36` |
| `research/forecasts/v2/golden/case_b/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013_145600.meta.json` | `9c9e8e3c2f66a0a9c0b91c7de5c154b412889a7bd85e994e07a85d60c71b2b17` |

## Recorded, not byte-checked (behaviour locked by the golden cases)

The daily job recomputes both v2 golden cases (`python tools/forecast_live_golden.py`) before it captures, so a
behaviour change in any of these files fails the run before a forecast is made.

| File | SHA-256 at the protocol commit | Why not checked |
|---|---|---|
| `fno/research_engine/live_features.py` | `249826bfda9971fce35b9d3ba28f708eb11cd0dde70d7fe53e805c998f61f10d` | B7's live ATM rule (`atm_implied_vol_points`); behaviour locked by the v2 golden cases |
| `fno/research_data/quote_snapshots.py` | `a1b9fb7773099760901a055a673589551bb454e1eff4cb7b21729ef0da763949` | B7's `CutoffSnapshot` and `LiveQuote`; behaviour locked by the v2 golden cases |
| `fno/research_engine/implied_vol.py` | `a752d5acaa41649ef6e02dde0e2dec22349fa1d44ee24fee09a7f144eeef60f0` | B1's Black-76; behaviour locked by the v1 and v2 golden values |
| `fno/research_engine/volatility_features.py` | `22f371f681e09b83338f625d5532ba5c3b73f6d62c7b9175346738e21ccfb23b` | B1's ATM IV and realised volatility; locked by the v1 and v2 golden values |
| `fno/research_engine/close_series.py` | `4b3a06c66037e696f83ce37f5db5d4040f50fa12d9af73fd50cec9fc1479356e` | B1's realised volatility; locked by the v1 and v2 golden values |
| `fno/research_data/panel_reader.py` | `6860c74633fd8533d245d59a6754c98be76740b59e3f99965ec59433d86ef317` | the panel and closes reader (past IV30, closes after the panel, story O6); locked by the golden cases |
| `fno/quotes/recorder.py` | `0775c4ccd99b47b935902422fa970894e6672673d1ab854644cf25d1facc5adb` | A4's snapshot layout (`request_sent_at`, `response_received_at`; levels read before the first quote request) |
| `fno/quotes/market_levels.py` | `4db33740a033983f27ecdf3df5ade7acbfdc3e522136554678a37d417850d56c` | A4's India VIX with NSE's timestamp and the NIFTY futures in the meta |
| `research/data/nifty-panel/warmup_closes.csv` | `46da687d9138492e68123f2f6a3e4f6f8adc4f7c199acfbc675ef36baecdf6a4` | official closes; story O6 appends a row each trading evening, never rewriting one |
| `research/data/nifty-panel/manifest.json` | `89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636` | the panel grows with new days (A3); a revision of past days is an A11 revision |
| `research/data/calendar/nse_sessions.csv` | `e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d` | rows are added each year (A7); its SHA-256 is in every live pack |
| `config.yaml` | `450da78bf748e83ca316ebe50ea739f5af6487fc1ee2b6fade281e864e201a1d` | `risk_free_rate` 0.065 is read from here |

## Research ledger

Trials 37-41 (`forecasts-v2`, one per question) were registered in the protocol commit, before any live forecast. This
commit sets their `protocol_commit`.

## Access attestation

No live forecast exists. The v2 golden cases use synthetic 13 Oct 2026 quotes. Rule of the orchestrator's holdout:
no 2019-2023 rows of `golden_iv30_rv20.csv` or the G2 back-fill were opened, printed or analysed for this version.
